import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Laboratorio de Bioquímica API"
    API_V1_STR: str = "/api/v1"
    
    # Base de Datos
    # Por defecto usamos SQLite para desarrollo rápido y local
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./laboratorio.db")
    
    # Seguridad JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_BIOQUIMICA_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 días

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:4200")
    API_PUBLIC_URL: str = os.getenv("API_PUBLIC_URL", "http://localhost:8000")

settings = Settings()
