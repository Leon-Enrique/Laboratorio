from datetime import date
import os

from sqlalchemy.orm import Session
from app.db.session import engine, Base
from app.db.migrate_lims import migrate_lims_inventory
from app.core.config import settings
from app.core.production_checks import assert_strong_initial_password
from app.models.usuario import Usuario, Paciente
from app.models.examen import Examen, FormulaConsumo
from app.models.parametro_examen import ParametroExamen
from app.models.inventario import Proveedor, Reactivo, MovimientoStock, Lote
from app.services import inventario_service as inv
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _password_admin_inicial() -> str:
    if settings.is_production:
        pwd = os.getenv("ADMIN_INITIAL_PASSWORD", "").strip()
        if not pwd:
            raise RuntimeError(
                "En producción defina ADMIN_INITIAL_PASSWORD en .env antes de run_init_db.py"
            )
        assert_strong_initial_password(pwd, label="ADMIN_INITIAL_PASSWORD")
        return pwd
    return os.getenv("ADMIN_INITIAL_PASSWORD", "admin123").strip() or "admin123"


def _seed_usuarios(db: Session) -> None:
    """Usuarios iniciales. En producción: solo admin con contraseña fuerte; demo opcional."""
    seed_demo = _env_bool("SEED_DEMO_USERS", default=not settings.is_production)

    admin = db.query(Usuario).filter(Usuario.email == "admin@laboratorio.com").first()
    if not admin:
        admin_pwd = _password_admin_inicial()
        admin = Usuario(
            email="admin@laboratorio.com",
            password_hash=get_password_hash(admin_pwd),
            nombre="Administrador General",
            rol="admin",
            activo=True,
        )
        db.add(admin)

    if not seed_demo:
        db.commit()
        return

    bioq = db.query(Usuario).filter(Usuario.email == "bioquimico@laboratorio.com").first()
    if not bioq:
        bio_pwd = os.getenv("BIOQUIMICO_INITIAL_PASSWORD", "bio123").strip() or "bio123"
        if settings.is_production:
            assert_strong_initial_password(bio_pwd, label="BIOQUIMICO_INITIAL_PASSWORD")
        bioq = Usuario(
            email="bioquimico@laboratorio.com",
            password_hash=get_password_hash(bio_pwd),
            nombre="Dr. Carlos Mendoza (Bioquímico)",
            rol="bioquimico",
            activo=True,
        )
        db.add(bioq)

    pac_user = db.query(Usuario).filter(Usuario.email == "juan.perez@email.com").first()
    if not pac_user:
        pac_user = Usuario(
            email="juan.perez@email.com",
            password_hash=get_password_hash("juan123"),
            nombre="Juan Pérez",
            rol="paciente",
            activo=True,
        )
        db.add(pac_user)
        db.commit()
        db.refresh(pac_user)

        paciente = Paciente(
            usuario_id=pac_user.id,
            dni="12345678-9",
            nombre="Juan",
            apellido="Pérez",
            fecha_nacimiento=date(1990, 5, 15),
            genero="M",
            telefono="+59170000000",
            direccion="Av. Siempre Viva 742",
        )
        db.add(paciente)

    db.commit()


def init_db(db: Session):
    # Crear tablas y migrar esquema LIMS (multi-lote)
    migrate_lims_inventory()

    # 1. Crear Proveedores
    prov_abrott = db.query(Proveedor).filter(Proveedor.nombre == "Abbott Diagnostics").first()
    if not prov_abrott:
        prov_abrott = Proveedor(
            nombre="Abbott Diagnostics",
            telefono="+1-800-222-688",
            email="support@abbott.com",
            direccion="Chicago, IL"
        )
        db.add(prov_abrott)
        db.commit()
        db.refresh(prov_abrott)

    prov_roche = db.query(Proveedor).filter(Proveedor.nombre == "Roche Diagnostics").first()
    if not prov_roche:
        prov_roche = Proveedor(
            nombre="Roche Diagnostics",
            telefono="+1-800-444-999",
            email="ventas@roche.com",
            direccion="Basilea, Suiza"
        )
        db.add(prov_roche)
        db.commit()
        db.refresh(prov_roche)

    # 2. Usuarios iniciales (admin obligatorio en prod con ADMIN_INITIAL_PASSWORD)
    _seed_usuarios(db)

    # 3. Crear Reactivos (Insumos) en Inventario
    reactivos_data = [
        {"nombre": "Tubo de extracción de sangre (Tapa Roja)", "stock_actual": 150.0, "stock_minimo": 50.0, "unidad_medida": "unidades", "lote": "L-TR990", "fecha_vencimiento": date(2027, 12, 31), "prov": prov_abrott},
        {"nombre": "Aguja estéril 21G", "stock_actual": 200.0, "stock_minimo": 60.0, "unidad_medida": "unidades", "lote": "L-AG112", "fecha_vencimiento": date(2028, 6, 30), "prov": prov_abrott},
        {"nombre": "Reactivo de Glucosa Oxidasa", "stock_actual": 500.0, "stock_minimo": 100.0, "unidad_medida": "ml", "lote": "R-GLU25", "fecha_vencimiento": date(2026, 12, 1), "prov": prov_roche},
        {"nombre": "Reactivo de Colesterol (Enzimático)", "stock_actual": 300.0, "stock_minimo": 80.0, "unidad_medida": "ml", "lote": "R-COL77", "fecha_vencimiento": date(2026, 10, 15), "prov": prov_roche},
        {"nombre": "Solución de Lavado / Buffer", "stock_actual": 1000.0, "stock_minimo": 200.0, "unidad_medida": "ml", "lote": "B-BUF44", "fecha_vencimiento": date(2027, 1, 1), "prov": prov_roche}
    ]

    reactivos_map = {}
    for r_item in reactivos_data:
        r = db.query(Reactivo).filter(Reactivo.nombre == r_item["nombre"]).first()
        if not r:
            r = Reactivo(
                nombre=r_item["nombre"],
                stock_actual=0,
                stock_minimo=r_item["stock_minimo"],
                unidad_medida=r_item["unidad_medida"],
                proveedor_id=r_item["prov"].id if r_item["prov"] else None
            )
            db.add(r)
            db.commit()
            db.refresh(r)

            if r_item["stock_actual"] > 0 and r_item["lote"] and r_item["fecha_vencimiento"]:
                inv.registrar_entrada_lote(
                    db=db,
                    reactivo_id=r.id,
                    codigo_lote=r_item["lote"],
                    cantidad=r_item["stock_actual"],
                    fecha_vencimiento=r_item["fecha_vencimiento"],
                    proveedor_id=r_item["prov"].id if r_item["prov"] else None,
                    descripcion="Carga inicial del inventario",
                )
                db.refresh(r)
        reactivos_map[r.nombre] = r

    # 4. Crear Exámenes del Catálogo
    examenes_data = [
        {"nombre": "Glucosa en Ayunas", "descripcion": "Mide el nivel de glucosa (azúcar) en sangre tras 8 horas de ayuno. Util para diagnosticar diabetes.", "preparacion": "Ayuno estricto de 8 a 12 horas.", "precio_bob": 80.0, "tiempo_entrega_horas": 12},
        {"nombre": "Perfil Lipídico Completo", "descripcion": "Mide colesterol total, triglicéridos, HDL y LDL en sangre para evaluar riesgo cardiovascular.", "preparacion": "Ayuno de 9 a 12 horas antes de la toma de muestra. No ingerir alcohol el día anterior.", "precio_bob": 220.0, "tiempo_entrega_horas": 24}
    ]

    for e_item in examenes_data:
        e = db.query(Examen).filter(Examen.nombre == e_item["nombre"]).first()
        if not e:
            e = Examen(
                nombre=e_item["nombre"],
                descripcion=e_item["descripcion"],
                preparacion=e_item["preparacion"],
                precio_bob=e_item["precio_bob"],
                tiempo_entrega_horas=e_item["tiempo_entrega_horas"]
            )
            db.add(e)
            db.commit()
            db.refresh(e)

            # 5. Crear Fórmulas de Consumo (BOM) para cada examen
            if e.nombre == "Glucosa en Ayunas":
                # Consume: 1 Tubo, 1 Aguja, 5ml Reactivo Glucosa, 10ml Solución Lavado
                formulas = [
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Tubo de extracción de sangre (Tapa Roja)"].id, cantidad_consumo=1.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Aguja estéril 21G"].id, cantidad_consumo=1.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Reactivo de Glucosa Oxidasa"].id, cantidad_consumo=5.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Solución de Lavado / Buffer"].id, cantidad_consumo=10.0)
                ]
                db.add_all(formulas)
            elif e.nombre == "Perfil Lipídico Completo":
                # Consume: 1 Tubo, 1 Aguja, 10ml Reactivo Colesterol, 15ml Solución Lavado
                formulas = [
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Tubo de extracción de sangre (Tapa Roja)"].id, cantidad_consumo=1.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Aguja estéril 21G"].id, cantidad_consumo=1.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Reactivo de Colesterol (Enzimático)"].id, cantidad_consumo=10.0),
                    FormulaConsumo(examen_id=e.id, reactivo_id=reactivos_map["Solución de Lavado / Buffer"].id, cantidad_consumo=15.0)
                ]
                db.add_all(formulas)
            db.commit()

    # 6. Parámetros analíticos del catálogo (rangos de referencia)
    parametros_seed = {
        "Glucosa en Ayunas": [
            {"nombre": "Glucosa", "unidad": "mg/dL", "valor_min": 70.0, "valor_max": 100.0, "orden": 0},
        ],
        "Perfil Lipídico Completo": [
            {"nombre": "Colesterol Total", "unidad": "mg/dL", "valor_min": 0.0, "valor_max": 200.0, "orden": 0},
            {"nombre": "Triglicéridos", "unidad": "mg/dL", "valor_min": 0.0, "valor_max": 150.0, "orden": 1},
            {"nombre": "HDL", "unidad": "mg/dL", "valor_min": 40.0, "valor_max": 60.0, "orden": 2},
            {"nombre": "LDL", "unidad": "mg/dL", "valor_min": 0.0, "valor_max": 100.0, "orden": 3},
        ],
    }
    for nombre_examen, params in parametros_seed.items():
        examen = db.query(Examen).filter(Examen.nombre == nombre_examen).first()
        if not examen:
            continue
        tiene = db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen.id).count()
        if tiene == 0:
            for p in params:
                db.add(ParametroExamen(examen_id=examen.id, **p))
            db.commit()

    # 7. Parámetros por defecto para exámenes sin catálogo analítico
    _backfill_parametros_faltantes(db)

    # 8. Catálogo ampliado de exámenes comunes (idempotente)
    from app.db.seed_catalogo import seed_examenes_comunes
    seed_examenes_comunes(db)

    print("Database seeding completed successfully!")


def _backfill_parametros_faltantes(db: Session) -> None:
    """Agrega un parámetro genérico a exámenes que aún no tienen ninguno."""
    defaults_por_nombre = {
        "vih": {"nombre": "Resultado VIH", "unidad": None, "valor_min": None, "valor_max": None},
        "embarazo": {"nombre": "Resultado", "unidad": None, "valor_min": None, "valor_max": None},
    }
    for examen in db.query(Examen).all():
        tiene = db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen.id).count()
        if tiene > 0:
            continue
        nombre_lower = examen.nombre.lower()
        cfg = None
        if "vih" in nombre_lower:
            cfg = defaults_por_nombre["vih"]
        elif "embarazo" in nombre_lower:
            cfg = defaults_por_nombre["embarazo"]
        else:
            cfg = {"nombre": "Resultado", "unidad": None, "valor_min": None, "valor_max": None}
        db.add(ParametroExamen(examen_id=examen.id, orden=0, **cfg))
    db.commit()
