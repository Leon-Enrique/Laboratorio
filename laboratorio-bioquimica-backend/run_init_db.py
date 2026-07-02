from app.db.session import SessionLocal
from app.db.init_db import init_db

def main():
    from app.core.config import settings

    if settings.is_production:
        print("Entorno: PRODUCCIÓN — se aplican reglas de seguridad estrictas.")
    print("Iniciando la base de datos y cargando datos semilla...")
    db = SessionLocal()
    try:
        init_db(db)
        print("¡Base de datos inicializada con éxito!")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
