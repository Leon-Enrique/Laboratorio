from typing import List, Any, Optional
from datetime import date, timedelta, datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.inventario import Reactivo, Proveedor, MovimientoStock, Lote, MermaInventario, OrdenPedido
from app.models.usuario import Usuario
from app.schemas.inventario import (
    ReactivoResponse,
    ReactivoCreate,
    ProveedorResponse,
    ProveedorCreate,
    ProveedorUpdate,
    MovimientoStockResponse,
    MovimientoStockCreate,
    LoteCreate,
    LoteResponse,
    BajaLoteRequest,
    AuditoriaInventarioResponse,
    MermaInventarioResponse,
    SugerenciaCompraResponse,
    OrdenPedidoCreate,
    OrdenPedidoUpdate,
    OrdenPedidoResponse,
    ReactivoMrpUpdate,
)
from app.api.v1.endpoints.auth import RoleChecker
from app.services import inventario_service as inv

router = APIRouter()

dependencias_seguridad = [Depends(RoleChecker(["admin", "bioquimico"]))]


def _enriquecer_lote(lote: Lote) -> dict:
    hoy = date.today()
    data = LoteResponse.model_validate(lote).model_dump()
    data["dias_para_vencer"] = (lote.fecha_vencimiento - hoy).days
    return data


def _enriquecer_movimiento(m: MovimientoStock) -> MovimientoStockResponse:
    return MovimientoStockResponse(
        id=m.id,
        reactivo_id=m.reactivo_id,
        cantidad=m.cantidad,
        tipo=m.tipo,
        descripcion=m.descripcion,
        fecha=m.fecha,
        lote_id=m.lote_id,
        orden_id=m.orden_id,
        usuario_id=m.usuario_id,
        usuario_nombre=m.usuario.nombre if m.usuario else None,
        codigo_lote=m.lote.codigo_lote if m.lote else None,
        reactivo_nombre=m.reactivo.nombre if m.reactivo else None,
        stock_antes=m.stock_antes,
        stock_despues=m.stock_despues,
        stock_lote_antes=m.stock_lote_antes,
        stock_lote_despues=m.stock_lote_despues,
    )


@router.get("/reactivos", response_model=List[ReactivoResponse], dependencies=dependencias_seguridad)
def listar_reactivos(db: Session = Depends(get_db)) -> Any:
    inv.sincronizar_lotes_vencidos(db)
    reactivos = (
        db.query(Reactivo)
        .options(joinedload(Reactivo.proveedor), selectinload(Reactivo.lotes))
        .all()
    )
    resultado = []
    for r in reactivos:
        lotes = r.lotes or []
        item = ReactivoResponse.model_validate(r)
        item.total_lotes = len(lotes)
        item.lotes_activos = len(
            [l for l in lotes if l.estado == "ACTIVO" and l.cantidad_disponible > 0]
        )
        resultado.append(item)
    return resultado


@router.post("/reactivos", response_model=ReactivoResponse)
def crear_reactivo(
    reactivo_in: ReactivoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin"])),
) -> Any:
    db_r = db.query(Reactivo).filter(Reactivo.nombre == reactivo_in.nombre).first()
    if db_r:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un reactivo con este nombre en el inventario",
        )

    nuevo_reactivo = Reactivo(
        nombre=reactivo_in.nombre,
        stock_actual=0,
        stock_minimo=reactivo_in.stock_minimo,
        stock_de_seguridad=reactivo_in.stock_de_seguridad,
        tiempo_entrega_proveedor_dias=reactivo_in.tiempo_entrega_proveedor_dias,
        unidad_medida=reactivo_in.unidad_medida,
        proveedor_id=reactivo_in.proveedor_id,
    )
    db.add(nuevo_reactivo)
    db.commit()
    db.refresh(nuevo_reactivo)

    if reactivo_in.stock_actual > 0 and reactivo_in.lote and reactivo_in.fecha_vencimiento:
        inv.registrar_entrada_lote(
            db=db,
            reactivo_id=nuevo_reactivo.id,
            codigo_lote=reactivo_in.lote,
            cantidad=reactivo_in.stock_actual,
            fecha_vencimiento=reactivo_in.fecha_vencimiento,
            usuario_id=current_user.id,
            proveedor_id=reactivo_in.proveedor_id,
            descripcion="Ingreso inicial al crear reactivo",
        )
        db.refresh(nuevo_reactivo)

    return nuevo_reactivo


@router.get("/reactivos/{reactivo_id}/lotes", dependencies=dependencias_seguridad)
def listar_lotes_reactivo(reactivo_id: int, db: Session = Depends(get_db)) -> Any:
    reactivo = db.query(Reactivo).filter(Reactivo.id == reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")
    inv.sincronizar_lotes_vencidos(db)
    lotes = (
        db.query(Lote)
        .filter(Lote.reactivo_id == reactivo_id)
        .order_by(Lote.fecha_vencimiento.asc())
        .all()
    )
    return [_enriquecer_lote(l) for l in lotes]


@router.post("/lotes", dependencies=dependencias_seguridad)
def registrar_lote(
    lote_in: LoteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    lote = inv.registrar_entrada_lote(
        db=db,
        reactivo_id=lote_in.reactivo_id,
        codigo_lote=lote_in.codigo_lote,
        cantidad=lote_in.cantidad_disponible,
        fecha_vencimiento=lote_in.fecha_vencimiento,
        usuario_id=current_user.id,
        proveedor_id=lote_in.proveedor_id,
        descripcion=lote_in.descripcion or f"Reabastecimiento lote {lote_in.codigo_lote}",
    )
    return _enriquecer_lote(lote)


@router.post("/lotes/{lote_id}/baja", dependencies=dependencias_seguridad)
def dar_baja_lote(
    lote_id: int,
    body: BajaLoteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    lote = inv.dar_baja_lote(db, lote_id, current_user.id, body.motivo)
    return _enriquecer_lote(lote)


@router.post("/lotes/sincronizar-vencidos", dependencies=dependencias_seguridad)
def sincronizar_vencidos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin"])),
) -> Any:
    count = inv.sincronizar_lotes_vencidos(db)
    return {"lotes_marcados_vencidos": count}


@router.get("/alertas", dependencies=dependencias_seguridad)
def obtener_alertas_inventario(db: Session = Depends(get_db)) -> Any:
    return inv.obtener_alertas(db)


@router.get("/movimientos", response_model=List[MovimientoStockResponse], dependencies=dependencias_seguridad)
def listar_movimientos(
    reactivo_id: Optional[int] = Query(None),
    lote_id: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
) -> Any:
    q = (
        db.query(MovimientoStock)
        .options(
            joinedload(MovimientoStock.lote),
            joinedload(MovimientoStock.reactivo),
            joinedload(MovimientoStock.usuario),
        )
        .order_by(MovimientoStock.fecha.desc())
    )
    if reactivo_id:
        q = q.filter(MovimientoStock.reactivo_id == reactivo_id)
    if lote_id:
        q = q.filter(MovimientoStock.lote_id == lote_id)
    if tipo:
        q = q.filter(MovimientoStock.tipo == tipo)
    movimientos = q.limit(limit).all()
    return [_enriquecer_movimiento(m) for m in movimientos]


@router.get("/auditoria", response_model=AuditoriaInventarioResponse, dependencies=dependencias_seguridad)
def reporte_auditoria(db: Session = Depends(get_db)) -> Any:
    inv.sincronizar_lotes_vencidos(db)
    hoy = date.today()
    limite = hoy + timedelta(days=90)
    hace_30 = datetime.combine(hoy - timedelta(days=30), datetime.min.time())

    total_reactivos = db.query(Reactivo).count()
    total_lotes = db.query(Lote).count()
    lotes_vencidos = (
        db.query(Lote)
        .filter(Lote.cantidad_disponible > 0, Lote.estado == "VENCIDO")
        .count()
    )
    lotes_proximos = (
        db.query(Lote)
        .filter(
            Lote.cantidad_disponible > 0,
            Lote.estado == "ACTIVO",
            Lote.fecha_vencimiento <= limite,
            Lote.fecha_vencimiento >= hoy,
        )
        .count()
    )
    reactivos_bajo = db.query(Reactivo).filter(Reactivo.stock_actual <= Reactivo.stock_minimo).count()
    mov_30 = db.query(MovimientoStock).filter(MovimientoStock.fecha >= hace_30).count()

    ultimos = (
        db.query(MovimientoStock)
        .options(
            joinedload(MovimientoStock.lote),
            joinedload(MovimientoStock.reactivo),
            joinedload(MovimientoStock.usuario),
        )
        .order_by(MovimientoStock.fecha.desc())
        .limit(20)
        .all()
    )

    return AuditoriaInventarioResponse(
        total_reactivos=total_reactivos,
        total_lotes=total_lotes,
        lotes_vencidos_con_stock=lotes_vencidos,
        lotes_proximos_vencer=lotes_proximos,
        reactivos_bajo_minimo=reactivos_bajo,
        movimientos_ultimos_30_dias=mov_30,
        ultimos_movimientos=[_enriquecer_movimiento(m) for m in ultimos],
    )


@router.post("/movimientos", response_model=MovimientoStockResponse, dependencies=dependencias_seguridad)
def registrar_movimiento(
    movimiento: MovimientoStockCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    if movimiento.tipo == "ENTRADA":
        if not movimiento.codigo_lote or not movimiento.fecha_vencimiento:
            raise HTTPException(
                status_code=400,
                detail="Las entradas requieren codigo_lote y fecha_vencimiento",
            )
        lote = inv.registrar_entrada_lote(
            db=db,
            reactivo_id=movimiento.reactivo_id,
            codigo_lote=movimiento.codigo_lote,
            cantidad=movimiento.cantidad,
            fecha_vencimiento=movimiento.fecha_vencimiento,
            usuario_id=current_user.id,
            proveedor_id=movimiento.proveedor_id,
            descripcion=movimiento.descripcion,
        )
        mov = (
            db.query(MovimientoStock)
            .options(joinedload(MovimientoStock.lote), joinedload(MovimientoStock.reactivo), joinedload(MovimientoStock.usuario))
            .filter(MovimientoStock.lote_id == lote.id)
            .order_by(MovimientoStock.id.desc())
            .first()
        )
        return _enriquecer_movimiento(mov)

    reactivo = db.query(Reactivo).filter(Reactivo.id == movimiento.reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")

    if movimiento.cantidad < 0:
        inv.consumir_por_fefo(
            db=db,
            reactivo_id=movimiento.reactivo_id,
            cantidad=abs(movimiento.cantidad),
            tipo=movimiento.tipo or "AJUSTE",
            usuario_id=current_user.id,
            descripcion=movimiento.descripcion,
        )
        db.flush()
        mov = (
            db.query(MovimientoStock)
            .options(joinedload(MovimientoStock.lote), joinedload(MovimientoStock.reactivo), joinedload(MovimientoStock.usuario))
            .filter(MovimientoStock.reactivo_id == movimiento.reactivo_id)
            .order_by(MovimientoStock.id.desc())
            .first()
        )
        db.commit()
        return _enriquecer_movimiento(mov)

    raise HTTPException(status_code=400, detail="Use tipo ENTRADA con lote o cantidad negativa para salidas")


def _orden_pedido_response(orden: OrdenPedido) -> OrdenPedidoResponse:
    return OrdenPedidoResponse(
        id=orden.id,
        reactivo_id=orden.reactivo_id,
        reactivo_nombre=orden.reactivo.nombre if orden.reactivo else None,
        proveedor_id=orden.proveedor_id,
        proveedor_nombre=orden.proveedor.nombre if orden.proveedor else None,
        proveedor_telefono=orden.proveedor.telefono if orden.proveedor else None,
        cantidad_pedida=orden.cantidad_pedida,
        estado=orden.estado,
        fecha_creacion=orden.fecha_creacion,
        fecha_esperada=orden.fecha_esperada,
        notas=orden.notas,
    )


@router.get("/proveedores", response_model=List[ProveedorResponse], dependencies=dependencias_seguridad)
def listar_proveedores(db: Session = Depends(get_db)) -> Any:
    return db.query(Proveedor).order_by(Proveedor.nombre).all()


@router.post("/proveedores", response_model=ProveedorResponse, dependencies=dependencias_seguridad)
def crear_proveedor(
    body: ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin"])),
) -> Any:
    existente = db.query(Proveedor).filter(Proveedor.nombre == body.nombre.strip()).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese nombre")
    proveedor = Proveedor(
        nombre=body.nombre.strip(),
        telefono=body.telefono,
        email=body.email,
        direccion=body.direccion,
    )
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.patch("/proveedores/{proveedor_id}", response_model=ProveedorResponse, dependencies=dependencias_seguridad)
def actualizar_proveedor(
    proveedor_id: int,
    body: ProveedorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin"])),
) -> Any:
    proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if body.nombre is not None:
        nombre = body.nombre.strip()
        if not nombre:
            raise HTTPException(status_code=400, detail="El nombre del proveedor no puede estar vacío")
        otro = db.query(Proveedor).filter(Proveedor.nombre == nombre, Proveedor.id != proveedor_id).first()
        if otro:
            raise HTTPException(status_code=400, detail="Ya existe otro proveedor con ese nombre")
        proveedor.nombre = nombre
    if body.telefono is not None:
        proveedor.telefono = body.telefono or None
    if body.email is not None:
        proveedor.email = body.email or None
    if body.direccion is not None:
        proveedor.direccion = body.direccion or None
    db.add(proveedor)
    db.commit()
    db.refresh(proveedor)
    return proveedor


@router.patch("/reactivos/{reactivo_id}", response_model=ReactivoResponse, dependencies=dependencias_seguridad)
def actualizar_reactivo_mrp(
    reactivo_id: int,
    body: ReactivoMrpUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin"])),
) -> Any:
    reactivo = db.query(Reactivo).filter(Reactivo.id == reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")
    if body.stock_de_seguridad is not None:
        reactivo.stock_de_seguridad = body.stock_de_seguridad
    if body.tiempo_entrega_proveedor_dias is not None:
        reactivo.tiempo_entrega_proveedor_dias = body.tiempo_entrega_proveedor_dias
    if body.stock_minimo is not None:
        reactivo.stock_minimo = body.stock_minimo
    if body.proveedor_id is not None:
        if body.proveedor_id == 0:
            reactivo.proveedor_id = None
        else:
            prov = db.query(Proveedor).filter(Proveedor.id == body.proveedor_id).first()
            if not prov:
                raise HTTPException(status_code=404, detail="Proveedor no encontrado")
            reactivo.proveedor_id = body.proveedor_id
    db.add(reactivo)
    db.commit()
    db.refresh(reactivo)
    return reactivo


@router.get("/mermas", response_model=List[MermaInventarioResponse], dependencies=dependencias_seguridad)
def listar_mermas(
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> Any:
    mermas = inv.listar_mermas(db, limit=limit)
    return [
        MermaInventarioResponse(
            id=m.id,
            id_insumo=m.id_insumo,
            insumo_nombre=m.reactivo.nombre if m.reactivo else None,
            lote_id=m.lote_id,
            codigo_lote=m.codigo_lote,
            cantidad_perdida=m.cantidad_perdida,
            fecha_baja=m.fecha_baja,
            motivo=m.motivo,
        )
        for m in mermas
    ]


@router.get("/sugerencias-compra", response_model=List[SugerenciaCompraResponse], dependencies=dependencias_seguridad)
def sugerencias_compra(
    reactivo_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> Any:
    return inv.obtener_sugerencias_compra(db, reactivo_id=reactivo_id)


@router.get("/ordenes-pedido", response_model=List[OrdenPedidoResponse], dependencies=dependencias_seguridad)
def listar_ordenes_pedido(db: Session = Depends(get_db)) -> Any:
    ordenes = (
        db.query(OrdenPedido)
        .options(joinedload(OrdenPedido.reactivo), joinedload(OrdenPedido.proveedor))
        .order_by(OrdenPedido.fecha_creacion.desc())
        .all()
    )
    return [_orden_pedido_response(o) for o in ordenes]


@router.post("/ordenes-pedido", response_model=OrdenPedidoResponse, dependencies=dependencias_seguridad)
def crear_orden_pedido(
    body: OrdenPedidoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    reactivo = db.query(Reactivo).filter(Reactivo.id == body.reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")
    orden = OrdenPedido(
        reactivo_id=body.reactivo_id,
        cantidad_pedida=body.cantidad_pedida,
        proveedor_id=body.proveedor_id or reactivo.proveedor_id,
        fecha_esperada=body.fecha_esperada,
        notas=body.notas,
        usuario_id=current_user.id,
        estado="BORRADOR",
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)
    orden = (
        db.query(OrdenPedido)
        .options(joinedload(OrdenPedido.reactivo), joinedload(OrdenPedido.proveedor))
        .filter(OrdenPedido.id == orden.id)
        .first()
    )
    return _orden_pedido_response(orden)


@router.patch("/ordenes-pedido/{orden_id}", response_model=OrdenPedidoResponse, dependencies=dependencias_seguridad)
def actualizar_orden_pedido(
    orden_id: int,
    body: OrdenPedidoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(RoleChecker(["admin", "bioquimico"])),
) -> Any:
    orden = db.query(OrdenPedido).filter(OrdenPedido.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden de pedido no encontrada")
    if body.estado is not None:
        if body.estado not in ("BORRADOR", "ENVIADA", "RECIBIDA", "CANCELADA"):
            raise HTTPException(status_code=400, detail="Estado de pedido inválido")
        orden.estado = body.estado
    if body.cantidad_pedida is not None:
        orden.cantidad_pedida = body.cantidad_pedida
    if body.proveedor_id is not None:
        orden.proveedor_id = body.proveedor_id
    if body.fecha_esperada is not None:
        orden.fecha_esperada = body.fecha_esperada
    if body.notas is not None:
        orden.notas = body.notas
    db.add(orden)
    db.commit()
    orden = (
        db.query(OrdenPedido)
        .options(joinedload(OrdenPedido.reactivo), joinedload(OrdenPedido.proveedor))
        .filter(OrdenPedido.id == orden.id)
        .first()
    )
    return _orden_pedido_response(orden)
