from datetime import date, timedelta, datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.inventario import Reactivo, Lote, MovimientoStock, MermaInventario

MOTIVOS_BAJA_VALIDOS = {"Vencimiento", "Calibración", "Desecho manual"}
DIAS_CONSUMO_PROMEDIO = 30


def sincronizar_lotes_vencidos(db: Session) -> int:
    """Marca lotes ACTIVO con fecha vencida como VENCIDO."""
    hoy = date.today()
    lotes = (
        db.query(Lote)
        .filter(
            Lote.estado == "ACTIVO",
            Lote.fecha_vencimiento < hoy,
            Lote.cantidad_disponible > 0,
        )
        .all()
    )
    for lote in lotes:
        lote.estado = "VENCIDO"
    if lotes:
        db.commit()
    return len(lotes)


def actualizar_lote_display(db: Session, reactivo: Reactivo) -> None:
    """Sincroniza lote/fecha_vencimiento del reactivo con el lote FEFO en uso."""
    hoy = date.today()
    lote_activo = (
        db.query(Lote)
        .filter(
            Lote.reactivo_id == reactivo.id,
            Lote.estado == "ACTIVO",
            Lote.cantidad_disponible > 0,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento.asc(), Lote.fecha_ingreso.asc())
        .first()
    )
    if lote_activo:
        reactivo.lote = lote_activo.codigo_lote
        reactivo.fecha_vencimiento = lote_activo.fecha_vencimiento
        return

    lote_cualquiera = (
        db.query(Lote)
        .filter(Lote.reactivo_id == reactivo.id, Lote.cantidad_disponible > 0)
        .order_by(Lote.fecha_vencimiento.asc())
        .first()
    )
    if lote_cualquiera:
        reactivo.lote = lote_cualquiera.codigo_lote
        reactivo.fecha_vencimiento = lote_cualquiera.fecha_vencimiento
    else:
        reactivo.lote = None
        reactivo.fecha_vencimiento = None


def recalcular_stock_reactivo(db: Session, reactivo: Reactivo) -> float:
    total = (
        db.query(Lote)
        .filter(Lote.reactivo_id == reactivo.id, Lote.cantidad_disponible > 0)
        .with_entities(Lote.cantidad_disponible)
        .all()
    )
    stock = sum(row[0] for row in total) if total else 0.0
    reactivo.stock_actual = stock
    actualizar_lote_display(db, reactivo)
    return stock


def registrar_entrada_lote(
    db: Session,
    reactivo_id: int,
    codigo_lote: str,
    cantidad: float,
    fecha_vencimiento: date,
    usuario_id: Optional[int] = None,
    proveedor_id: Optional[int] = None,
    descripcion: Optional[str] = None,
) -> Lote:
    if cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")
    if fecha_vencimiento < date.today():
        raise HTTPException(status_code=400, detail="No se puede registrar un lote ya vencido")

    reactivo = db.query(Reactivo).filter(Reactivo.id == reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")

    codigo_lote = codigo_lote.strip()
    stock_antes = reactivo.stock_actual

    lote = (
        db.query(Lote)
        .filter(Lote.reactivo_id == reactivo_id, Lote.codigo_lote == codigo_lote)
        .first()
    )

    if lote:
        if lote.estado in ("VENCIDO", "BLOQUEADO", "Dado_de_Baja"):
            raise HTTPException(
                status_code=400,
                detail=f"El lote '{codigo_lote}' está {lote.estado.lower()}. Usa un código de lote nuevo.",
            )
        lote_stock_antes = lote.cantidad_disponible
        lote.cantidad_disponible += cantidad
        lote.fecha_vencimiento = fecha_vencimiento
        if lote.estado == "AGOTADO":
            lote.estado = "ACTIVO"
        lote_stock_despues = lote.cantidad_disponible
    else:
        lote = Lote(
            reactivo_id=reactivo_id,
            codigo_lote=codigo_lote,
            cantidad_disponible=cantidad,
            fecha_vencimiento=fecha_vencimiento,
            fecha_ingreso=date.today(),
            proveedor_id=proveedor_id,
            estado="ACTIVO",
        )
        db.add(lote)
        db.flush()
        lote_stock_antes = 0.0
        lote_stock_despues = cantidad

    reactivo.stock_actual = stock_antes + cantidad
    actualizar_lote_display(db, reactivo)

    movimiento = MovimientoStock(
        reactivo_id=reactivo_id,
        lote_id=lote.id,
        usuario_id=usuario_id,
        cantidad=cantidad,
        tipo="ENTRADA",
        descripcion=descripcion or f"Ingreso lote {codigo_lote}",
        stock_antes=stock_antes,
        stock_despues=reactivo.stock_actual,
        stock_lote_antes=lote_stock_antes,
        stock_lote_despues=lote_stock_despues,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(lote)
    return lote


def consumir_por_fefo(
    db: Session,
    reactivo_id: int,
    cantidad: float,
    tipo: str,
    usuario_id: Optional[int] = None,
    orden_id: Optional[int] = None,
    descripcion: Optional[str] = None,
) -> List[MovimientoStock]:
    if cantidad <= 0:
        return []

    sincronizar_lotes_vencidos(db)
    hoy = date.today()

    reactivo = db.query(Reactivo).filter(Reactivo.id == reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")

    lotes = (
        db.query(Lote)
        .filter(
            Lote.reactivo_id == reactivo_id,
            Lote.estado == "ACTIVO",
            Lote.cantidad_disponible > 0,
            Lote.fecha_vencimiento >= hoy,
        )
        .order_by(Lote.fecha_vencimiento.asc(), Lote.fecha_ingreso.asc())
        .all()
    )

    disponible = sum(l.cantidad_disponible for l in lotes)
    if disponible < cantidad:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Stock insuficiente o lotes vencidos para '{reactivo.nombre}'. "
                f"Disponible (no vencido): {disponible} {reactivo.unidad_medida}, "
                f"requerido: {cantidad} {reactivo.unidad_medida}"
            ),
        )

    pendiente = cantidad
    movimientos: List[MovimientoStock] = []
    stock_corriente = reactivo.stock_actual

    for lote in lotes:
        if pendiente <= 0:
            break
        tomar = min(lote.cantidad_disponible, pendiente)
        lote_stock_antes = lote.cantidad_disponible
        lote.cantidad_disponible -= tomar
        lote_stock_despues = lote.cantidad_disponible
        if lote.cantidad_disponible == 0:
            lote.estado = "AGOTADO"
        pendiente -= tomar

        movimiento = MovimientoStock(
            reactivo_id=reactivo_id,
            lote_id=lote.id,
            usuario_id=usuario_id,
            orden_id=orden_id,
            cantidad=-tomar,
            tipo=tipo,
            descripcion=descripcion,
            stock_antes=stock_corriente,
            stock_despues=stock_corriente - tomar,
            stock_lote_antes=lote_stock_antes,
            stock_lote_despues=lote_stock_despues,
        )
        stock_corriente -= tomar
        db.add(movimiento)
        movimientos.append(movimiento)

    reactivo.stock_actual -= cantidad
    actualizar_lote_display(db, reactivo)
    db.add(reactivo)
    return movimientos


def dar_baja_lote(
    db: Session,
    lote_id: int,
    usuario_id: Optional[int] = None,
    motivo: Optional[str] = None,
) -> Lote:
    lote = db.query(Lote).filter(Lote.id == lote_id).first()
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    reactivo = db.query(Reactivo).filter(Reactivo.id == lote.reactivo_id).first()
    if not reactivo:
        raise HTTPException(status_code=404, detail="Reactivo no encontrado")

    if lote.estado == "Dado_de_Baja":
        raise HTTPException(status_code=400, detail="El lote ya fue dado de baja")

    if lote.cantidad_disponible <= 0 and lote.estado in ("AGOTADO", "Dado_de_Baja"):
        raise HTTPException(status_code=400, detail="El lote no tiene stock para dar de baja")

    motivo_norm = (motivo or "Vencimiento").strip()
    if motivo_norm not in MOTIVOS_BAJA_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Motivo inválido. Use: {', '.join(sorted(MOTIVOS_BAJA_VALIDOS))}",
        )

    cantidad = lote.cantidad_disponible
    stock_antes = reactivo.stock_actual
    lote_stock_antes = lote.cantidad_disponible
    lote.cantidad_disponible = 0
    lote.estado = "Dado_de_Baja"

    if cantidad > 0:
        reactivo.stock_actual = max(0, stock_antes - cantidad)
    actualizar_lote_display(db, reactivo)

    if cantidad > 0:
        movimiento = MovimientoStock(
            reactivo_id=reactivo.id,
            lote_id=lote.id,
            usuario_id=usuario_id,
            cantidad=-cantidad,
            tipo="BAJA_VENCIDO",
            descripcion=f"Baja de lote {lote.codigo_lote} — {motivo_norm}",
            stock_antes=stock_antes,
            stock_despues=reactivo.stock_actual,
            stock_lote_antes=lote_stock_antes,
            stock_lote_despues=0,
        )
        db.add(movimiento)

    merma = MermaInventario(
        id_insumo=reactivo.id,
        lote_id=lote.id,
        cantidad_perdida=cantidad if cantidad > 0 else lote_stock_antes,
        motivo=motivo_norm,
        codigo_lote=lote.codigo_lote,
        usuario_id=usuario_id,
    )
    db.add(merma)
    db.commit()
    db.refresh(lote)
    return lote


def consumo_diario_promedio(db: Session, reactivo_id: int, dias: int = DIAS_CONSUMO_PROMEDIO) -> float:
    desde = datetime.now(timezone.utc) - timedelta(days=dias)
    total = (
        db.query(func.coalesce(func.sum(func.abs(MovimientoStock.cantidad)), 0.0))
        .filter(
            MovimientoStock.reactivo_id == reactivo_id,
            MovimientoStock.fecha >= desde,
            MovimientoStock.cantidad < 0,
            MovimientoStock.tipo.in_(("CONSUMO_AUTO", "AJUSTE", "BAJA_VENCIDO")),
        )
        .scalar()
    )
    return round(float(total or 0) / max(dias, 1), 4)


def calcular_punto_reorden(reactivo: Reactivo, consumo_diario: float) -> float:
    lead = reactivo.tiempo_entrega_proveedor_dias or 0
    seguridad = reactivo.stock_de_seguridad or 0
    return round((consumo_diario * lead) + seguridad, 4)


def obtener_sugerencias_compra(db: Session, reactivo_id: Optional[int] = None) -> list:
    sincronizar_lotes_vencidos(db)
    q = db.query(Reactivo)
    if reactivo_id:
        q = q.filter(Reactivo.id == reactivo_id)
    reactivos = q.all()
    sugerencias = []

    for r in reactivos:
        consumo = consumo_diario_promedio(db, r.id)
        punto = calcular_punto_reorden(r, consumo)
        bajo_reorden = r.stock_actual < punto
        bajo_minimo = r.stock_actual <= r.stock_minimo

        if not bajo_reorden and not bajo_minimo and not reactivo_id:
            continue

        cantidad_sugerida = max(punto - r.stock_actual, r.stock_minimo - r.stock_actual, 1)
        if reactivo_id and cantidad_sugerida <= 0:
            cantidad_sugerida = max(r.stock_minimo, 1)

        alertas = []
        if bajo_minimo:
            alertas.append("Bajo stock")
        if bajo_reorden:
            alertas.append("Bajo punto de reorden")

        proveedor_nombre = r.proveedor.nombre if r.proveedor else None
        sugerencias.append(
            {
                "reactivo_id": r.id,
                "nombre": r.nombre,
                "unidad_medida": r.unidad_medida,
                "stock_actual": r.stock_actual,
                "consumo_diario_promedio": consumo,
                "tiempo_entrega_proveedor_dias": r.tiempo_entrega_proveedor_dias or 7,
                "stock_de_seguridad": r.stock_de_seguridad or 0,
                "stock_minimo": r.stock_minimo,
                "punto_reorden": punto,
                "cantidad_sugerida": round(cantidad_sugerida, 2),
                "proveedor_id": r.proveedor_id,
                "proveedor_nombre": proveedor_nombre,
                "alertas": alertas,
            }
        )

    sugerencias.sort(key=lambda x: x["stock_actual"] / max(x["punto_reorden"], 0.01))
    return sugerencias


def listar_mermas(db: Session, limit: int = 200) -> List[MermaInventario]:
    from sqlalchemy.orm import joinedload
    return (
        db.query(MermaInventario)
        .options(joinedload(MermaInventario.reactivo))
        .order_by(MermaInventario.fecha_baja.desc())
        .limit(limit)
        .all()
    )


def obtener_alertas(db: Session) -> list:
    sincronizar_lotes_vencidos(db)
    hoy = date.today()
    limite = hoy + timedelta(days=90)
    alertas = []
    reactivos = db.query(Reactivo).all()

    for r in reactivos:
        motivos = []
        lotes = db.query(Lote).filter(Lote.reactivo_id == r.id, Lote.cantidad_disponible > 0).all()

        if r.stock_actual <= r.stock_minimo:
            motivos.append("Bajo stock")

        consumo = consumo_diario_promedio(db, r.id)
        punto = calcular_punto_reorden(r, consumo)
        if r.stock_actual < punto and "Bajo stock" not in motivos:
            motivos.append("Bajo punto de reorden")

        for lote in lotes:
            if lote.fecha_vencimiento < hoy:
                if "Lote Vencido" not in motivos:
                    motivos.append("Lote Vencido")
            elif lote.fecha_vencimiento <= limite:
                if "Próximo a vencer" not in motivos:
                    motivos.append("Próximo a vencer")

        if motivos:
            lote_critico = sorted(
                [l for l in lotes if l.cantidad_disponible > 0],
                key=lambda x: x.fecha_vencimiento,
            )
            ref = lote_critico[0] if lote_critico else None
            alertas.append(
                {
                    "id": r.id,
                    "nombre": r.nombre,
                    "stock_actual": r.stock_actual,
                    "stock_minimo": r.stock_minimo,
                    "unidad_medida": r.unidad_medida,
                    "lote": ref.codigo_lote if ref else r.lote,
                    "fecha_vencimiento": ref.fecha_vencimiento if ref else r.fecha_vencimiento,
                    "alertas": motivos,
                    "lotes_afectados": len([l for l in lotes if l.fecha_vencimiento <= limite]),
                }
            )

    return alertas
