from typing import List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case
from app.db.session import get_db
from app.models.examen import Examen, FormulaConsumo
from app.models.orden import Resultado
from app.schemas.examen import ExamenResponse, ExamenCreate, DestacadoInicioUpdate
from app.schemas.catalogo_analytics import BusquedaCatalogoEvent, ClicCatalogoEvent, MasBuscadoResponse
from app.api.v1.endpoints.auth import RoleChecker
from app.services import parametros_service as param_svc
from app.services import catalogo_analytics_service as analytics_svc

router = APIRouter()
MAX_DESTACADOS_INICIO = 6

def _examenes_query(db: Session):
    return db.query(Examen).options(
        joinedload(Examen.formulas),
        joinedload(Examen.parametros),
    )

# Catálogo público: exámenes visibles (opcionalmente solo destacados para la landing)
@router.get("/", response_model=List[ExamenResponse])
def listar_examenes(
    destacados: bool = Query(False, description="Si es true, solo exámenes marcados como destacados en inicio"),
    db: Session = Depends(get_db),
) -> Any:
    q = _examenes_query(db).filter(Examen.visible == True)
    if destacados:
        q = q.filter(Examen.destacado == True)
        return q.order_by(
            case((Examen.orden_destacado.is_(None), 999), else_=Examen.orden_destacado),
            Examen.nombre,
        ).limit(MAX_DESTACADOS_INICIO).all()
    return q.order_by(Examen.nombre).all()

# Catálogo administrativo: muestra todos los exámenes, visibles o no (solo admin/bioquímico)
@router.get("/admin-lista", response_model=List[ExamenResponse])
def listar_examenes_admin(
    ligero: bool = Query(False, description="Sin fórmulas MRP — más rápido para cola de órdenes"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    if ligero:
        return (
            db.query(Examen)
            .options(joinedload(Examen.parametros))
            .order_by(Examen.id)
            .all()
        )
    return _examenes_query(db).order_by(Examen.id).all()

# Analytics del catálogo público (sin autenticación)
@router.post("/analytics/busqueda", status_code=status.HTTP_204_NO_CONTENT)
def registrar_busqueda_catalogo(
    body: BusquedaCatalogoEvent,
    db: Session = Depends(get_db),
) -> None:
    analytics_svc.registrar_busqueda_catalogo(db, body.termino.strip().lower(), body.examen_ids)


@router.post("/analytics/clic", status_code=status.HTTP_204_NO_CONTENT)
def registrar_clic_catalogo(
    body: ClicCatalogoEvent,
    db: Session = Depends(get_db),
) -> None:
    if not analytics_svc.registrar_clic_catalogo(db, body.examen_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Examen no encontrado")


@router.get("/analytics/mas-buscados", response_model=List[MasBuscadoResponse])
def listar_mas_buscados_catalogo(
    limite: int = Query(10, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"])),
) -> Any:
    return analytics_svc.listar_mas_buscados(db, limite=limite)

# Cambiar visibilidad del examen (solo admin)
@router.put("/{examen_id}/visibilidad", response_model=ExamenResponse)
def toggle_visibilidad_examen(
    examen_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    # Alternar visibilidad
    examen.visible = not examen.visible
    if not examen.visible:
        examen.destacado = False
        examen.titulo_destacado = None
        examen.subtitulo_destacado = None
        examen.descripcion_destacado = None
        examen.orden_destacado = None
    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()

# Marcar/desmarcar examen como destacado en la página de inicio (solo admin)
@router.put("/{examen_id}/destacado", response_model=ExamenResponse)
def toggle_destacado_examen(
    examen_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    examen.destacado = not examen.destacado
    if not examen.destacado:
        examen.titulo_destacado = None
        examen.subtitulo_destacado = None
        examen.descripcion_destacado = None
        examen.orden_destacado = None
    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()

# Configurar texto y orden de un destacado en inicio (solo admin)
@router.put("/{examen_id}/destacado-config", response_model=ExamenResponse)
def configurar_destacado_inicio(
    examen_id: int,
    body: DestacadoInicioUpdate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    if body.destacado and not examen.visible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La prueba debe estar visible en la web para destacarla"
        )
    if body.destacado and not examen.destacado:
        activos = db.query(Examen).filter(Examen.destacado == True, Examen.visible == True).count()
        if activos >= MAX_DESTACADOS_INICIO:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Máximo {MAX_DESTACADOS_INICIO} pruebas destacadas en el inicio"
            )
    if body.orden_destacado is not None and (body.orden_destacado < 1 or body.orden_destacado > MAX_DESTACADOS_INICIO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El orden debe estar entre 1 y {MAX_DESTACADOS_INICIO}"
        )

    examen.destacado = body.destacado
    if body.destacado:
        examen.titulo_destacado = (body.titulo_destacado or "").strip() or None
        examen.subtitulo_destacado = (body.subtitulo_destacado or "").strip() or None
        examen.descripcion_destacado = (body.descripcion_destacado or "").strip() or None
        examen.orden_destacado = body.orden_destacado
    else:
        examen.titulo_destacado = None
        examen.subtitulo_destacado = None
        examen.descripcion_destacado = None
        examen.orden_destacado = None

    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()

# Crear examen con su fórmula BOM (solo admin/bioquímico)
@router.post("/", response_model=ExamenResponse)
def crear_examen(
    examen_in: ExamenCreate, 
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin", "bioquimico"]))
) -> Any:
    db_examen = db.query(Examen).filter(Examen.nombre == examen_in.nombre).first()
    if db_examen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un examen con este nombre"
        )
    
    nuevo_examen = Examen(
        nombre=examen_in.nombre,
        descripcion=examen_in.descripcion,
        preparacion=examen_in.preparacion,
        precio_bob=examen_in.precio_bob,
        tiempo_entrega_horas=examen_in.tiempo_entrega_horas,
        visible=examen_in.visible if examen_in.visible is not None else True,
        destacado=examen_in.destacado if examen_in.destacado is not None else False,
        tipo=examen_in.tipo or "Laboratorio",
        grupo=examen_in.grupo,
        grupo_impresion=examen_in.grupo_impresion,
        derivacion=examen_in.derivacion,
        material_muestra=examen_in.material_muestra,
        estado=examen_in.estado or "Activo",
        codigo_abrev=examen_in.codigo_abrev,
        precio_derivacion=examen_in.precio_derivacion if examen_in.precio_derivacion is not None else 0,
        etiqueta=examen_in.etiqueta,
    )
    db.add(nuevo_examen)
    db.commit()
    db.refresh(nuevo_examen)

    # Insertar fórmula de consumo (BOM) asociada si fue provista
    if examen_in.formulas:
        for f_item in examen_in.formulas:
            formula = FormulaConsumo(
                examen_id=nuevo_examen.id,
                reactivo_id=f_item.reactivo_id,
                cantidad_consumo=f_item.cantidad_consumo
            )
            db.add(formula)
        db.commit()

    if examen_in.parametros:
        param_svc.guardar_parametros_examen(db, nuevo_examen.id, examen_in.parametros)
        db.commit()

    db.refresh(nuevo_examen)
    return _examenes_query(db).filter(Examen.id == nuevo_examen.id).first()

# Actualizar examen con su fórmula BOM (solo admin)
@router.put("/{examen_id}", response_model=ExamenResponse)
def actualizar_examen(
    examen_id: int,
    examen_in: ExamenCreate,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"]))
) -> Any:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado"
        )
    
    # Validar duplicados si cambia el nombre
    if examen_in.nombre != examen.nombre:
        db_examen = db.query(Examen).filter(Examen.nombre == examen_in.nombre).first()
        if db_examen:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro examen con este nombre"
            )
            
    # Actualizar campos
    examen.nombre = examen_in.nombre
    examen.descripcion = examen_in.descripcion
    examen.preparacion = examen_in.preparacion
    examen.precio_bob = examen_in.precio_bob
    examen.tiempo_entrega_horas = examen_in.tiempo_entrega_horas
    if examen_in.visible is not None:
        examen.visible = examen_in.visible
    if examen_in.destacado is not None:
        examen.destacado = examen_in.destacado
    examen.tipo = examen_in.tipo or "Laboratorio"
    examen.grupo = examen_in.grupo
    examen.grupo_impresion = examen_in.grupo_impresion
    examen.derivacion = examen_in.derivacion
    examen.material_muestra = examen_in.material_muestra
    examen.estado = examen_in.estado or "Activo"
    examen.codigo_abrev = examen_in.codigo_abrev
    examen.precio_derivacion = examen_in.precio_derivacion if examen_in.precio_derivacion is not None else 0
    examen.etiqueta = examen_in.etiqueta
        
    # Eliminar fórmulas viejas e insertar nuevas
    db.query(FormulaConsumo).filter(FormulaConsumo.examen_id == examen_id).delete()
    
    if examen_in.formulas:
        for f_item in examen_in.formulas:
            formula = FormulaConsumo(
                examen_id=examen_id,
                reactivo_id=f_item.reactivo_id,
                cantidad_consumo=f_item.cantidad_consumo
            )
            db.add(formula)

    param_svc.guardar_parametros_examen(db, examen_id, examen_in.parametros or [])
            
    db.add(examen)
    db.commit()
    return _examenes_query(db).filter(Examen.id == examen_id).first()


@router.delete("/{examen_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_examen(
    examen_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(RoleChecker(["admin"])),
) -> None:
    examen = db.query(Examen).filter(Examen.id == examen_id).first()
    if not examen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Examen no encontrado",
        )

    usos = db.query(Resultado).filter(Resultado.examen_id == examen_id).count()
    if usos > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No se puede eliminar: la prueba tiene {usos} resultado(s) en órdenes. "
                "Ocúltala del catálogo público en su lugar."
            ),
        )

    db.delete(examen)
    db.commit()
