"""Migración ligera para SQLite: tablas/columnas LIMS sin Alembic."""
from datetime import date

from sqlalchemy import inspect, text

from app.db.session import engine, SessionLocal, Base
from app.models.inventario import Reactivo, Lote, MovimientoStock
from app.models.orden import Orden
from app.models.parametro_examen import ParametroExamen  # noqa: F401 — create_all


def _column_exists(inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _add_column_if_missing(conn, inspector, table: str, column: str, ddl: str) -> None:
    if _table_exists(inspector, table) and not _column_exists(inspector, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def _datetime_column_ddl(engine, column: str) -> str:
    dialect = engine.dialect.name
    if dialect == "postgresql":
        return f"{column} TIMESTAMP WITH TIME ZONE"
    return f"{column} DATETIME"


def migrate_lims_inventory() -> None:
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    fecha_ddl = _datetime_column_ddl(engine, "fecha_completado")
    fecha_pago_ddl = _datetime_column_ddl(engine, "fecha_pago")

    with engine.begin() as conn:
        if _table_exists(inspector, "movimientos_stock"):
            _add_column_if_missing(conn, inspector, "movimientos_stock", "lote_id", "lote_id INTEGER")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "usuario_id", "usuario_id INTEGER")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "orden_id", "orden_id INTEGER")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "stock_antes", "stock_antes FLOAT")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "stock_despues", "stock_despues FLOAT")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "stock_lote_antes", "stock_lote_antes FLOAT")
            _add_column_if_missing(conn, inspector, "movimientos_stock", "stock_lote_despues", "stock_lote_despues FLOAT")

        if _table_exists(inspector, "ordenes"):
            _add_column_if_missing(conn, inspector, "ordenes", "fecha_completado", fecha_ddl)
            _add_column_if_missing(conn, inspector, "ordenes", "estado_pago", "estado_pago VARCHAR DEFAULT 'PENDIENTE'")
            _add_column_if_missing(conn, inspector, "ordenes", "metodo_pago", "metodo_pago VARCHAR")
            _add_column_if_missing(conn, inspector, "ordenes", "fecha_pago", fecha_pago_ddl)
            _add_column_if_missing(conn, inspector, "ordenes", "medico_solicitante", "medico_solicitante VARCHAR")
            _add_column_if_missing(conn, inspector, "ordenes", "prioridad", "prioridad VARCHAR DEFAULT 'NORMAL'")
            _add_column_if_missing(conn, inspector, "ordenes", "notas", "notas VARCHAR")

    db = SessionLocal()
    try:
        _migrar_reactivos_a_lotes(db)
        _backfill_fecha_completado(db)
    finally:
        db.close()


def _migrar_reactivos_a_lotes(db) -> None:
    """Convierte reactivos mono-lote existentes en registros Lote."""
    reactivos = db.query(Reactivo).all()
    for r in reactivos:
        tiene_lotes = db.query(Lote).filter(Lote.reactivo_id == r.id).count() > 0
        if tiene_lotes:
            continue
        if r.stock_actual and r.stock_actual > 0:
            codigo = r.lote or f"LEGACY-{r.id}"
            venc = r.fecha_vencimiento or date.today().replace(year=date.today().year + 1)
            estado = "VENCIDO" if venc < date.today() else "ACTIVO"
            lote = Lote(
                reactivo_id=r.id,
                codigo_lote=codigo,
                cantidad_disponible=r.stock_actual,
                fecha_vencimiento=venc,
                fecha_ingreso=date.today(),
                proveedor_id=r.proveedor_id,
                estado=estado,
            )
            db.add(lote)
    db.commit()


def _backfill_fecha_completado(db) -> None:
    ordenes = db.query(Orden).filter(Orden.estado == "COMPLETADO", Orden.fecha_completado.is_(None)).all()
    for o in ordenes:
        o.fecha_completado = o.fecha_creacion
    if ordenes:
        db.commit()
