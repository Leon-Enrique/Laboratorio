import uuid
import re
from datetime import datetime, timezone, date
from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, Header
from fastapi.responses import FileResponse, Response
from jose import jwt, JWTError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.db.session import get_db
from app.models.orden import Orden, Resultado
from app.models.usuario import Paciente
from app.models.examen import Examen, FormulaConsumo
from app.services import inventario_service as inv
from app.services import pdf_service, qr_service, rate_limit_service as rate_limit
from app.schemas.orden import (
    OrdenResponse,
    OrdenCreate,
    ResultadoCreate,
    OrdenPagoUpdate,
    OrdenMetaUpdate,
    ConsultaPacienteRequest,
    CodigoVerificacionResponse,
)
from app.api.v1.endpoints.auth import RoleChecker, get_current_user, oauth2_scheme
from app.models.usuario import Usuario

router = APIRouter()


def _orden_query(db: Session):
    return db.query(Orden).options(
        joinedload(Orden.paciente),
        joinedload(Orden.bioquimico),
        joinedload(Orden.resultados).joinedload(Resultado.examen).joinedload(Examen.parametros),
    )


def _informe_pdf_url(codigo_orden: str) -> str:
    return f"{settings.API_PUBLIC_URL}{settings.API_V1_STR}/ordenes/informe/{codigo_orden}/pdf"


def _staff_desde_token(authorization: Optional[str], db: Session) -> Optional[Usuario]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario and usuario.rol in ("admin", "bioquimico") and usuario.activo:
            return usuario
    except JWTError:
        return None
    return None


def _tiene_valores(valor_resultado) -> bool:
    if not valor_resultado:
        return False
    return any(v is not None and str(v).strip() for v in valor_resultado.values())


def _actualizar_estado_workflow(db: Session, orden: Orden) -> None:
    if orden.estado == "COMPLETADO":
        return
    resultados = db.query(Resultado).filter(Resultado.orden_id == orden.id).all()
    if any(_tiene_valores(r.valor_resultado) for r in resultados):
        orden.estado = "PROCESANDO"
    else:
        orden.estado = "PENDIENTE"


def _validar_fecha_nacimiento(fecha: date) -> None:
    hoy = date.today()
    if fecha.year < 1900 or fecha > hoy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fecha de nacimiento inválida. Use una fecha real (1900 – hoy).",
        )


def _validar_datos_factura(requiere: bool, nit: Optional[str], razon_social: Optional[str]) -> None:
    if not requiere:
        return
    nit_limpio = (nit or "").strip()
    if not nit_limpio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ingrese el NIT para emitir factura.",
        )
    digitos = re.sub(r"\D", "", nit_limpio)
    if len(digitos) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NIT inválido. Debe tener al menos 5 dígitos.",
        )
    if not (razon_social or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ingrese la razón social o nombre para factura.",
        )


# 1. Crear Orden (solo admin/bioquímico)
# Si el paciente no existe (por DNI), lo crea automáticamente
@router.post("/", response_model=OrdenResponse)
def crear_orden(
    orden_in: OrdenCreate, 
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    _validar_fecha_nacimiento(orden_in.fecha_nacimiento_paciente)
    requiere_factura = bool(orden_in.requiere_factura)
    _validar_datos_factura(requiere_factura, orden_in.nit_factura, orden_in.razon_social_factura)
    # Buscar paciente
    paciente = db.query(Paciente).filter(Paciente.dni == orden_in.paciente_dni).first()
    if not paciente:
        paciente = Paciente(
            dni=orden_in.paciente_dni,
            nombre=orden_in.nombre_paciente,
            apellido=orden_in.apellido_paciente,
            fecha_nacimiento=orden_in.fecha_nacimiento_paciente,
            genero=orden_in.genero_paciente,
            telefono=orden_in.telefono_paciente,
            direccion=orden_in.direccion_paciente,
            nit=orden_in.nit_factura.strip() if requiere_factura and orden_in.nit_factura else None,
            razon_social=orden_in.razon_social_factura.strip() if requiere_factura and orden_in.razon_social_factura else None,
        )
        db.add(paciente)
        db.commit()
        db.refresh(paciente)
    elif requiere_factura:
        if orden_in.nit_factura:
            paciente.nit = orden_in.nit_factura.strip()
        if orden_in.razon_social_factura:
            paciente.razon_social = orden_in.razon_social_factura.strip()
        db.add(paciente)
        db.commit()

    # Validar que los exámenes solicitados existan
    examenes = db.query(Examen).filter(Examen.id.in_(orden_in.examenes_ids)).all()
    if len(examenes) != len(orden_in.examenes_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más exámenes solicitados no existen en el catálogo"
        )

    # Generar código único legible para consulta de resultados
    codigo_unico = f"ORD-{uuid.uuid4().hex[:6].upper()}"

    prioridad = orden_in.prioridad if orden_in.prioridad in ("NORMAL", "URGENTE") else "NORMAL"
    nueva_orden = Orden(
        paciente_id=paciente.id,
        codigo_orden=codigo_unico,
        estado="PENDIENTE",
        estado_pago=orden_in.estado_pago if orden_in.estado_pago in ("PENDIENTE", "PAGADO") else "PENDIENTE",
        metodo_pago=orden_in.metodo_pago if orden_in.estado_pago == "PAGADO" else None,
        fecha_pago=datetime.now(timezone.utc) if orden_in.estado_pago == "PAGADO" else None,
        medico_solicitante=orden_in.medico_solicitante,
        prioridad=prioridad,
        notas=orden_in.notas,
        requiere_factura=requiere_factura,
        nit_factura=orden_in.nit_factura.strip() if requiere_factura and orden_in.nit_factura else None,
        razon_social_factura=orden_in.razon_social_factura.strip() if requiere_factura and orden_in.razon_social_factura else None,
    )
    db.add(nueva_orden)
    db.commit()
    db.refresh(nueva_orden)

    # Inicializar las estructuras de resultados vacías para cada examen asignado
    for examen in examenes:
        resultado = Resultado(
            orden_id=nueva_orden.id,
            examen_id=examen.id,
            valor_resultado=None
        )
        db.add(resultado)
        
    db.commit()
    return _orden_query(db).filter(Orden.id == nueva_orden.id).first()


# 2. Listar todas las órdenes (solo admin/bioquímico)
@router.get("/", response_model=List[OrdenResponse])
def listar_ordenes(
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    return _orden_query(db).order_by(Orden.fecha_creacion.desc()).all()


# 3a. Buscar Pacientes por DNI o Nombre parcial (solo admin/bioquímico)
@router.get("/pacientes/buscar")
def buscar_pacientes(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    if not q or len(q) < 2:
        return []
    term = f"%{q}%"
    pacientes = db.query(Paciente).filter(
        Paciente.dni.ilike(term) |
        Paciente.nombre.ilike(term) |
        Paciente.apellido.ilike(term)
    ).limit(10).all()
    return [
        {"dni": p.dni, "nombre": p.nombre, "apellido": p.apellido}
        for p in pacientes
    ]


# 3b. Obtener Historial de Paciente por DNI (solo admin/bioquímico)
@router.get("/pacientes/{dni}/historial", response_model=List[OrdenResponse])
def obtener_historial_paciente(
    dni: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    paciente = db.query(Paciente).filter(Paciente.dni == dni).first()
    if not paciente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado"
        )
    return _orden_query(db).filter(Orden.paciente_id == paciente.id).order_by(Orden.fecha_creacion.desc()).all()


# 4a. Verificar que un código de orden existe (sin datos sensibles)
@router.get("/consulta/verificar/{codigo_orden}", response_model=CodigoVerificacionResponse)
def verificar_codigo_orden(
    codigo_orden: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.registrar_intento(client_ip):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espere unos minutos e intente de nuevo.")

    codigo = codigo_orden.strip().upper()
    existe = db.query(Orden.id).filter(Orden.codigo_orden == codigo).first() is not None
    return CodigoVerificacionResponse(
        existe=existe,
        codigo_orden=codigo,
        mensaje="Código válido. Ingrese su CI y fecha de nacimiento para ver los resultados."
        if existe
        else "No se encontró una orden con ese código.",
    )


# 4b. Consulta pública verificada (CI + fecha de nacimiento)
@router.post("/consulta", response_model=OrdenResponse)
def consultar_resultado_paciente(
    body: ConsultaPacienteRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit.registrar_intento(client_ip):
        raise HTTPException(status_code=429, detail="Demasiados intentos. Espere unos minutos e intente de nuevo.")

    codigo = body.codigo_orden.strip().upper()
    orden = _orden_query(db).filter(Orden.codigo_orden == codigo).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Código de orden no encontrado o incorrecto")

    paciente = orden.paciente
    if paciente.dni.strip().upper() != body.dni.strip().upper():
        raise HTTPException(status_code=401, detail="La identificación no coincide con la orden registrada")
    if paciente.fecha_nacimiento != body.fecha_nacimiento:
        raise HTTPException(status_code=401, detail="La fecha de nacimiento no coincide con nuestros registros")

    _validar_fecha_nacimiento(body.fecha_nacimiento)

    pdf_url = _informe_pdf_url(codigo)
    for res in orden.resultados:
        if orden.estado == "COMPLETADO":
            res.pdf_url = pdf_url

    return orden


# 4c. Endpoint legacy deshabilitado
@router.get("/consulta/{codigo_orden}")
def consulta_legacy(codigo_orden: str) -> Any:
    raise HTTPException(
        status_code=410,
        detail="Por seguridad, use POST /ordenes/consulta con código, CI y fecha de nacimiento.",
    )


# 5. Guardar Valores de Resultado Temporales (Borrador - Solo Bioquímico/Admin)
@router.post("/{orden_id}/valores", response_model=OrdenResponse)
def guardar_valores_borrador(
    orden_id: int,
    resultados_in: List[ResultadoCreate],
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    if orden.estado == "COMPLETADO":
        raise HTTPException(status_code=400, detail="Esta orden ya ha sido completada y firmada")

    for res_in in resultados_in:
        db_res = db.query(Resultado).filter(
            Resultado.orden_id == orden_id, 
            Resultado.examen_id == res_in.examen_id
        ).first()
        
        if db_res:
            db_res.valor_resultado = res_in.valor_resultado
            db.add(db_res)

    _actualizar_estado_workflow(db, orden)
    db.add(orden)
    db.commit()
    return _orden_query(db).filter(Orden.id == orden_id).first()


# 6. Aprobar, Firmar Electrónicamente y Emitir Reporte Oficial (Solo Bioquímico Regente o Admin)
# ¡Activa el descuento automático de inventario MRP y genera URL de descarga PDF!
@router.post("/{orden_id}/aprobar", response_model=OrdenResponse)
def aprobar_y_emitir_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    orden = _orden_query(db).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
        
    if orden.estado == "COMPLETADO":
        raise HTTPException(status_code=400, detail="Esta orden ya se encuentra aprobada y completada")

    # Permitir firmar aunque falten valores parciales (borrador o incompleto)
    for res in orden.resultados:
        if res.valor_resultado is None:
            res.valor_resultado = {}
            db.add(res)

    # -- LOGICA MRP: Descontar reactivos por FEFO (lote más próximo a vencer primero) --
    try:
        for examen_resultado in orden.resultados:
            examen_id = examen_resultado.examen_id
            formulas = db.query(FormulaConsumo).filter(FormulaConsumo.examen_id == examen_id).all()

            for f in formulas:
                inv.consumir_por_fefo(
                    db=db,
                    reactivo_id=f.reactivo_id,
                    cantidad=f.cantidad_consumo,
                    tipo="CONSUMO_AUTO",
                    usuario_id=current_user.id,
                    orden_id=orden.id,
                    descripcion=f"Consumo automático por Aprobación de Orden {orden.codigo_orden}",
                )
    except HTTPException as e:
        db.rollback()
        raise e

    orden.estado = "COMPLETADO"
    orden.bioquimico_id = current_user.id
    orden.fecha_completado = datetime.now(timezone.utc)

    pdf_service.generar_informe_orden(orden, current_user.nombre)
    pdf_url = _informe_pdf_url(orden.codigo_orden)
    for res in orden.resultados:
        res.pdf_url = pdf_url
        db.add(res)

    db.add(orden)
    db.commit()
    return _orden_query(db).filter(Orden.id == orden_id).first()


@router.post("/{orden_id}/reabrir-resultados", response_model=OrdenResponse)
def reabrir_resultados_orden(
    orden_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    """Anula la firma para permitir corregir resultados y volver a emitir el informe."""
    orden = _orden_query(db).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden.estado not in ("COMPLETADO", "PROCESANDO"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden reiniciar órdenes con borrador o ya firmadas",
        )

    orden.fecha_completado = None
    orden.estado = "PENDIENTE"
    for res in orden.resultados:
        res.pdf_url = None
        res.valor_resultado = {}
        db.add(res)

    db.add(orden)
    db.commit()
    return _orden_query(db).filter(Orden.id == orden_id).first()


@router.patch("/{orden_id}/pago", response_model=OrdenResponse)
def actualizar_estado_pago(
    orden_id: int,
    pago_in: OrdenPagoUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if pago_in.estado_pago not in ("PENDIENTE", "PAGADO"):
        raise HTTPException(status_code=400, detail="estado_pago debe ser PENDIENTE o PAGADO")

    orden.estado_pago = pago_in.estado_pago
    if pago_in.estado_pago == "PAGADO":
        orden.metodo_pago = pago_in.metodo_pago or orden.metodo_pago or "EFECTIVO"
        orden.fecha_pago = datetime.now(timezone.utc)
    else:
        orden.metodo_pago = None
        orden.fecha_pago = None

    db.add(orden)
    db.commit()
    return _orden_query(db).filter(Orden.id == orden_id).first()


@router.patch("/{orden_id}/meta", response_model=OrdenResponse)
def actualizar_meta_orden(
    orden_id: int,
    meta_in: OrdenMetaUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if meta_in.prioridad is not None:
        if meta_in.prioridad not in ("NORMAL", "URGENTE"):
            raise HTTPException(status_code=400, detail="prioridad debe ser NORMAL o URGENTE")
        orden.prioridad = meta_in.prioridad
    if meta_in.medico_solicitante is not None:
        orden.medico_solicitante = meta_in.medico_solicitante or None
    if meta_in.notas is not None:
        orden.notas = meta_in.notas or None

    db.add(orden)
    db.commit()
    return _orden_query(db).filter(Orden.id == orden_id).first()


@router.get("/informe/{codigo_orden}/pdf")
def descargar_informe_pdf(
    codigo_orden: str,
    dni: Optional[str] = Query(None),
    fecha_nacimiento: Optional[date] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> FileResponse:
    codigo = codigo_orden.strip().upper()
    orden = _orden_query(db).filter(Orden.codigo_orden == codigo).first()
    if not orden or orden.estado != "COMPLETADO":
        raise HTTPException(status_code=404, detail="Informe no disponible")

    staff = _staff_desde_token(authorization, db)
    if not staff:
        if not dni or not fecha_nacimiento:
            raise HTTPException(
                status_code=401,
                detail="Debe verificar su identidad (CI y fecha de nacimiento) para descargar el informe",
            )
        p = orden.paciente
        if p.dni.strip().upper() != dni.strip().upper() or p.fecha_nacimiento != fecha_nacimiento:
            raise HTTPException(status_code=401, detail="Datos de verificación incorrectos")

    firmante = orden.bioquimico.nombre if orden.bioquimico else "Bioquímico Regente"
    pdf_service.generar_informe_orden(orden, firmante)

    return FileResponse(
        pdf_service.ruta_informe(codigo),
        media_type="application/pdf",
        filename=f"informe_{codigo}.pdf",
    )


@router.get("/qr/{codigo_orden}")
def qr_codigo_orden(codigo_orden: str) -> Response:
    codigo = codigo_orden.strip().upper()
    url = f"{settings.FRONTEND_URL}/resultados?codigo={codigo}"
    png = qr_service.generar_qr_png(url)
    return Response(content=png, media_type="image/png")
