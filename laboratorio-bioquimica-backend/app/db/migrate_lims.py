"""Migraciones legacy (columnas) y backfills de datos LIMS."""
from datetime import date

from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.session import engine, SessionLocal, Base
from app.models.inventario import Reactivo, Lote, MermaInventario, OrdenPedido  # noqa: F401
from app.models.orden import Orden
from app.models.parametro_examen import ParametroExamen  # noqa: F401 — metadata


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


def _rename_column_if_exists(conn, inspector, table: str, old: str, new: str) -> None:
    if not _table_exists(inspector, table):
        return
    cols = {c["name"] for c in inspector.get_columns(table)}
    if old in cols and new not in cols:
        conn.execute(text(f"ALTER TABLE {table} RENAME COLUMN {old} TO {new}"))


def apply_legacy_schema_patches() -> None:
    """Parches idempotentes para BDs creadas antes de Alembic."""
    import app.models  # noqa: F401 — registrar todos los modelos en metadata

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
            _add_column_if_missing(conn, inspector, "ordenes", "requiere_factura", "requiere_factura BOOLEAN DEFAULT false")
            _add_column_if_missing(conn, inspector, "ordenes", "nit_factura", "nit_factura VARCHAR")
            _add_column_if_missing(conn, inspector, "ordenes", "razon_social_factura", "razon_social_factura VARCHAR")
            _add_column_if_missing(conn, inspector, "ordenes", "numero_comprobante", "numero_comprobante INTEGER")
            _add_column_if_missing(conn, inspector, "ordenes", "recepcionista_id", "recepcionista_id INTEGER")

        if _table_exists(inspector, "examenes"):
            _rename_column_if_exists(conn, inspector, "examenes", "precio_usd", "precio_bob")
            _add_column_if_missing(conn, inspector, "examenes", "destacado", "destacado BOOLEAN DEFAULT false")
            _add_column_if_missing(conn, inspector, "examenes", "tipo", "tipo VARCHAR DEFAULT 'Laboratorio'")
            _add_column_if_missing(conn, inspector, "examenes", "grupo", "grupo VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "grupo_impresion", "grupo_impresion VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "derivacion", "derivacion VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "material_muestra", "material_muestra VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "estado", "estado VARCHAR DEFAULT 'Activo'")
            _add_column_if_missing(conn, inspector, "examenes", "codigo_abrev", "codigo_abrev VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "precio_derivacion", "precio_derivacion FLOAT DEFAULT 0")
            _add_column_if_missing(conn, inspector, "examenes", "etiqueta", "etiqueta VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "titulo_destacado", "titulo_destacado VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "subtitulo_destacado", "subtitulo_destacado VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "descripcion_destacado", "descripcion_destacado VARCHAR")
            _add_column_if_missing(conn, inspector, "examenes", "orden_destacado", "orden_destacado INTEGER")

        if _table_exists(inspector, "parametros_examen"):
            _add_column_if_missing(conn, inspector, "parametros_examen", "tipo", "tipo VARCHAR DEFAULT 'Numero'")
            _add_column_if_missing(conn, inspector, "parametros_examen", "grupo", "grupo VARCHAR")
            _add_column_if_missing(conn, inspector, "parametros_examen", "seccion", "seccion VARCHAR")
            _add_column_if_missing(conn, inspector, "parametros_examen", "llave", "llave VARCHAR")
            _add_column_if_missing(conn, inspector, "parametros_examen", "valor_defecto", "valor_defecto VARCHAR")
            _add_column_if_missing(conn, inspector, "parametros_examen", "decimales", "decimales INTEGER DEFAULT 2")
            _add_column_if_missing(conn, inspector, "parametros_examen", "metodo_prueba", "metodo_prueba TEXT")
            _add_column_if_missing(conn, inspector, "parametros_examen", "valor_referencia", "valor_referencia TEXT")

        if _table_exists(inspector, "reactivos"):
            _add_column_if_missing(conn, inspector, "reactivos", "stock_de_seguridad", "stock_de_seguridad FLOAT DEFAULT 0")
            _add_column_if_missing(conn, inspector, "reactivos", "tiempo_entrega_proveedor_dias", "tiempo_entrega_proveedor_dias INTEGER DEFAULT 7")

        if _table_exists(inspector, "pacientes"):
            _add_column_if_missing(conn, inspector, "pacientes", "nit", "nit VARCHAR")
            _add_column_if_missing(conn, inspector, "pacientes", "razon_social", "razon_social VARCHAR")


def run_data_backfills() -> None:
    db = SessionLocal()
    try:
        _migrar_reactivos_a_lotes(db)
        _backfill_fecha_completado(db)
        _backfill_numero_comprobante(db)
        _backfill_catalogo_examenes_comunes(db)
        _fix_fechas_nacimiento_invalidas(db)
    finally:
        db.close()


def migrate_lims_inventory() -> None:
    """Compatibilidad: parches legacy + backfills (sin Alembic)."""
    if settings.RUN_LEGACY_SCHEMA_PATCHES:
        apply_legacy_schema_patches()
    if settings.RUN_DATA_BACKFILL:
        run_data_backfills()


def _aplicar_parametros_catalogo(db) -> None:
    from app.db.seed_parametros import aplicar_parametros_catalogo

    n = aplicar_parametros_catalogo(db)
    if n:
        print(f"Parámetros de resultado: {n} exámenes actualizados con formulario específico.")


def _rellenar_resultados_demo(db) -> None:
    from app.db.seed_parametros import rellenar_resultados_demo

    n = rellenar_resultados_demo(db)
    if n:
        print(f"Resultados demo: {n} registros rellenados con valores de ejemplo.")


def _backfill_catalogo_examenes_comunes(db) -> None:
    from app.db.seed_catalogo import seed_examenes_comunes

    result = seed_examenes_comunes(db)
    if result["creados"] or result["destacados_actualizados"]:
        print(
            f"Catálogo: +{result['creados']} exámenes nuevos, "
            f"{result['destacados_actualizados']} marcados destacados "
            f"({result['total_visibles']} visibles en total)."
        )


def _fix_fechas_nacimiento_invalidas(db) -> None:
    from app.models.usuario import Paciente

    hoy = date.today()
    placeholder = date(1990, 1, 1)
    cambios = 0
    for p in db.query(Paciente).all():
        if p.fecha_nacimiento.year < 1900 or p.fecha_nacimiento > hoy:
            p.fecha_nacimiento = placeholder
            cambios += 1
    if cambios:
        db.commit()


def _backfill_parametros_examen(db) -> None:
    from app.models.examen import Examen
    from app.models.parametro_examen import ParametroExamen

    for examen in db.query(Examen).all():
        tiene = db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen.id).count()
        if tiene > 0:
            continue
        nombre_lower = examen.nombre.lower()
        if "vih" in nombre_lower:
            nombre = "Resultado VIH"
        elif "embarazo" in nombre_lower:
            nombre = "Resultado"
        else:
            nombre = "Resultado"
        db.add(ParametroExamen(examen_id=examen.id, nombre=nombre, orden=0))
    db.commit()


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


def _backfill_numero_comprobante(db) -> None:
    sin_numero = db.query(Orden).filter(Orden.numero_comprobante.is_(None)).order_by(Orden.id).all()
    if not sin_numero:
        return
    max_num = db.query(Orden.numero_comprobante).filter(Orden.numero_comprobante.isnot(None)).order_by(
        Orden.numero_comprobante.desc()
    ).first()
    siguiente = (max_num[0] if max_num and max_num[0] else 0) + 1
    for orden in sin_numero:
        orden.numero_comprobante = siguiente
        siguiente += 1
    db.commit()
