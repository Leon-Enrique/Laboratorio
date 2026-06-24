import os
from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]


class Settings:
    PROJECT_NAME: str = "Laboratorio de Bioquímica API"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = os.getenv("APP_ENV", "development").lower()

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./laboratorio.db")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_BIOQUIMICA_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 8)))

    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:4200")
    API_PUBLIC_URL: str = os.getenv("API_PUBLIC_URL", "http://localhost:8000")
    # Sitio público para QR/enlaces en PDF (dominio real aunque el API corra en local)
    PUBLIC_SITE_URL: str = os.getenv("PUBLIC_SITE_URL", "").strip()
    # Demo/cloud: omitir descuento MRP al firmar si no hay inventario cargado
    SKIP_MRP_ON_APROBAR: bool = _env_bool("SKIP_MRP_ON_APROBAR", False)
    # Marca de agua en PDF (desactivar en cloud mejora velocidad)
    PDF_WATERMARK: bool = _env_bool("PDF_WATERMARK", True)

    CORS_ORIGINS: list[str] = _parse_cors_origins()

    # Alembic al arrancar (recomendado en dev; en prod usar CI/deploy + AUTO_MIGRATE=false)
    AUTO_MIGRATE: bool = _env_bool(
        "AUTO_MIGRATE",
        default=os.getenv("APP_ENV", "development").lower() != "production",
    )
    # Parches legacy de columnas (solo si la BD existía antes de Alembic)
    RUN_LEGACY_SCHEMA_PATCHES: bool = _env_bool("RUN_LEGACY_SCHEMA_PATCHES", True)
    # Backfills de datos (parámetros, lotes legacy, fechas)
    RUN_DATA_BACKFILL: bool = _env_bool("RUN_DATA_BACKFILL", True)

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def public_site_url(self) -> str:
        """URL del portal para QR y PDF. Nunca apunta a localhost si hay dominio configurado."""
        if self.PUBLIC_SITE_URL:
            return self.PUBLIC_SITE_URL.rstrip("/")
        frontend = self.FRONTEND_URL.rstrip("/")
        host = frontend.lower()
        if "localhost" in host or "127.0.0.1" in host:
            return "https://genotipia-lab.com"
        return frontend

    def validate_production(self) -> None:
        if not self.is_production:
            return
        if self.SECRET_KEY == "SUPER_SECRET_KEY_BIOQUIMICA_2026":
            raise RuntimeError(
                "SECRET_KEY insegura en producción. Defina SECRET_KEY en el entorno."
            )
        if self.DATABASE_URL.startswith("sqlite"):
            raise RuntimeError(
                "SQLite no está soportado en producción. Use PostgreSQL (DATABASE_URL)."
            )


settings = Settings()
settings.validate_production()
