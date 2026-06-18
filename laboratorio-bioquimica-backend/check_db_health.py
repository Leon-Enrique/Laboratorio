"""Diagnóstico rápido de PostgreSQL: esquema + datos."""
from datetime import date

from sqlalchemy import inspect, text

from app.db.session import engine, SessionLocal
from app.db.migrations import run_startup_migrations
from app.models.orden import Orden, Resultado
from app.models.usuario import Usuario, Paciente
from app.models.examen import Examen
from app.models.parametro_examen import ParametroExamen
from app.models.inventario import Reactivo, Lote, Proveedor


def main() -> None:
    issues: list[str] = []
    warnings: list[str] = []

    print("=== 1. CONEXION ===")
    print("Motor:", engine.dialect.name)
    print("URL:", engine.url.render_as_string(hide_password=True))

    print("\n=== 2. MIGRACION ===")
    try:
        run_startup_migrations()
        print("run_startup_migrations (Alembic + backfills): OK")
        with engine.connect() as conn:
            try:
                rev = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
                if rev:
                    print(f"Alembic revision: {rev}")
            except Exception:
                print("Alembic: sin tabla alembic_version (ejecute alembic upgrade head)")
    except Exception as e:
        issues.append(f"Error en migracion: {e}")
        print("ERROR migracion:", e)

    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    expected = [
        "examenes", "formulas_consumo", "lotes", "movimientos_stock",
        "ordenes", "pacientes", "parametros_examen", "proveedores",
        "reactivos", "resultados", "usuarios",
    ]
    missing_tables = [t for t in expected if t not in tables]
    print("Tablas en BD:", len(tables))
    if missing_tables:
        issues.append(f"Faltan tablas: {missing_tables}")
    else:
        print("Todas las tablas esperadas: OK")

    orden_cols = {c["name"] for c in inspector.get_columns("ordenes")}
    expected_cols = {
        "fecha_completado", "estado_pago", "metodo_pago", "fecha_pago",
        "medico_solicitante", "prioridad", "notas",
    }
    missing_cols = expected_cols - orden_cols
    if missing_cols:
        issues.append(f"Faltan columnas en ordenes: {missing_cols}")
    else:
        print("Columnas LIMS en ordenes: OK")

    db = SessionLocal()

    print("\n=== 3. CONTEOS ===")
    counts = {
        "usuarios": db.query(Usuario).count(),
        "pacientes": db.query(Paciente).count(),
        "examenes": db.query(Examen).count(),
        "parametros_examen": db.query(ParametroExamen).count(),
        "ordenes": db.query(Orden).count(),
        "resultados": db.query(Resultado).count(),
        "reactivos": db.query(Reactivo).count(),
        "lotes": db.query(Lote).count(),
        "proveedores": db.query(Proveedor).count(),
    }
    for k, v in counts.items():
        print(f"  {k}: {v}")

    print("\n=== 4. USUARIOS CLAVE ===")
    for email in ["admin@laboratorio.com", "bioquimico@laboratorio.com"]:
        u = db.query(Usuario).filter(Usuario.email == email).first()
        if u:
            print(f"  OK {email} rol={u.rol} activo={u.activo}")
        else:
            issues.append(f"Falta usuario {email}")

    print("\n=== 5. EXAMENES Y PARAMETROS ===")
    for ex in db.query(Examen).all():
        n = db.query(ParametroExamen).filter(ParametroExamen.examen_id == ex.id).count()
        print(f"  {ex.nombre}: {n} parametros, precio={ex.precio_bob} BOB")
        if n == 0:
            warnings.append(f"Examen sin parametros: {ex.nombre}")

    print("\n=== 6. INTEGRIDAD ORDENES ===")
    ordenes = db.query(Orden).all()
    for o in ordenes:
        if len(o.resultados) == 0:
            issues.append(f"Orden {o.codigo_orden} sin resultados")
        if o.estado == "COMPLETADO" and not o.fecha_completado:
            warnings.append(f"Orden {o.codigo_orden} COMPLETADO sin fecha_completado")
        if o.estado_pago == "PAGADO" and not o.metodo_pago:
            warnings.append(f"Orden {o.codigo_orden} PAGADO sin metodo_pago")
        if o.prioridad and o.prioridad not in ("NORMAL", "URGENTE"):
            issues.append(f"Orden {o.codigo_orden} prioridad invalida: {o.prioridad}")
        elif not o.prioridad:
            warnings.append(f"Orden {o.codigo_orden} prioridad NULL")

    print(f"  Total ordenes: {len(ordenes)}")
    estados: dict[str, int] = {}
    for o in ordenes:
        estados[o.estado] = estados.get(o.estado, 0) + 1
    print("  Por estado:", estados)

    pagos: dict[str, int] = {}
    for o in ordenes:
        pagos[o.estado_pago or "PENDIENTE"] = pagos.get(o.estado_pago or "PENDIENTE", 0) + 1
    print("  Por pago:", pagos)

    print("\n=== 7. PACIENTES ===")
    hoy = date.today()
    for p in db.query(Paciente).all():
        if p.fecha_nacimiento.year > hoy.year or p.fecha_nacimiento.year < 1900:
            issues.append(f"Paciente {p.dni} fecha_nac invalida: {p.fecha_nacimiento}")
        elif p.fecha_nacimiento > hoy:
            issues.append(f"Paciente {p.dni} fecha_nac en futuro: {p.fecha_nacimiento}")
        else:
            print(f"  OK {p.nombre} {p.apellido} CI={p.dni} nac={p.fecha_nacimiento}")

    print("\n=== 8. INVENTARIO FEFO ===")
    for r in db.query(Reactivo).all():
        lotes = db.query(Lote).filter(Lote.reactivo_id == r.id).count()
        if r.stock_actual and r.stock_actual > 0 and lotes == 0:
            warnings.append(f"Reactivo '{r.nombre}' con stock pero sin lotes")

    print("\n=== 9. FK HUERFANAS ===")
    with engine.connect() as conn:
        orphan_res = conn.execute(text("""
            SELECT COUNT(*) FROM resultados r
            LEFT JOIN ordenes o ON r.orden_id = o.id
            WHERE o.id IS NULL
        """)).scalar()
        orphan_ord = conn.execute(text("""
            SELECT COUNT(*) FROM ordenes o
            LEFT JOIN pacientes p ON o.paciente_id = p.id
            WHERE p.id IS NULL
        """)).scalar()
    if orphan_res:
        issues.append(f"{orphan_res} resultados huerfanos")
    else:
        print("  Resultados huerfanos: 0 OK")
    if orphan_ord:
        issues.append(f"{orphan_ord} ordenes sin paciente")
    else:
        print("  Ordenes sin paciente: 0 OK")

    print("\n=== 10. ULTIMAS 5 ORDENES ===")
    for o in db.query(Orden).order_by(Orden.fecha_creacion.desc()).limit(5).all():
        pac = o.paciente
        nombre = f"{pac.nombre} {pac.apellido}" if pac else "?"
        print(
            f"  {o.codigo_orden} | {o.estado} | pago={o.estado_pago} | "
            f"prioridad={o.prioridad or 'NULL'} | {nombre} | res={len(o.resultados)}"
        )

    db.close()

    print("\n=== RESUMEN ===")
    if issues:
        print(f"ERRORES ({len(issues)}):")
        for i in issues:
            print("  -", i)
    else:
        print("Errores criticos: ninguno")

    if warnings:
        print(f"ADVERTENCIAS ({len(warnings)}):")
        for w in warnings:
            print("  -", w)
    else:
        print("Advertencias: ninguna")

    print("\nEstado general:", "BIEN" if not issues else "REVISAR ERRORES")


if __name__ == "__main__":
    main()
