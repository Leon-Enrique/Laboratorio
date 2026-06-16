from datetime import date, timedelta
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.inventario import Reactivo, Lote, MovimientoStock


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
        if lote.estado in ("VENCIDO", "BLOQUEADO"):
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

    if lote.cantidad_disponible <= 0:
        raise HTTPException(status_code=400, detail="El lote no tiene stock para dar de baja")

    cantidad = lote.cantidad_disponible
    stock_antes = reactivo.stock_actual
    lote_stock_antes = lote.cantidad_disponible
    lote.cantidad_disponible = 0
    lote.estado = "BLOQUEADO" if lote.estado != "VENCIDO" else "VENCIDO"

    reactivo.stock_actual = max(0, stock_antes - cantidad)
    actualizar_lote_display(db, reactivo)

    movimiento = MovimientoStock(
        reactivo_id=reactivo.id,
        lote_id=lote.id,
        usuario_id=usuario_id,
        cantidad=-cantidad,
        tipo="BAJA_VENCIDO",
        descripcion=motivo or f"Baja de lote {lote.codigo_lote} por vencimiento o bloqueo",
        stock_antes=stock_antes,
        stock_despues=reactivo.stock_actual,
        stock_lote_antes=lote_stock_antes,
        stock_lote_despues=0,
    )
    db.add(movimiento)
    db.commit()
    db.refresh(lote)
    return lote


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
