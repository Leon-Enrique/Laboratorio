"""Validaciones de seguridad obligatorias antes de publicar (APP_ENV=production)."""
from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings

WEAK_SECRET_KEYS = frozenset(
    {
        "SUPER_SECRET_KEY_BIOQUIMICA_2026",
        "cambia_esta_clave_por_una_segura_larga",
        "check_deploy_only",
        "CAMBIAR_POR_CLAVE_LARGA_Y_UNICA",
        "CAMBIAR_POR_CLAVE_LARGA",
    }
)

WEAK_PASSWORDS = frozenset(
    {
        "admin123",
        "bio123",
        "juan123",
        "password",
        "12345678",
        "admin",
    }
)

_LOCALHOST_RE = re.compile(r"localhost|127\.0\.0\.1", re.I)


def is_weak_password(password: str) -> bool:
    pwd = (password or "").strip()
    if len(pwd) < 12:
        return True
    if pwd.lower() in WEAK_PASSWORDS:
        return True
    return False


def assert_strong_initial_password(password: str, *, label: str = "Contraseña") -> None:
    if is_weak_password(password):
        raise RuntimeError(
            f"{label} demasiado débil para producción. Use al menos 12 caracteres "
            "y evite contraseñas de demo (admin123, etc.)."
        )


def _require_https_url(name: str, url: str, errors: list[str]) -> None:
    value = (url or "").strip()
    if not value.lower().startswith("https://"):
        errors.append(f"{name} debe usar HTTPS en producción (valor actual: {value!r}).")


def _reject_localhost(name: str, value: str, errors: list[str]) -> None:
    if _LOCALHOST_RE.search(value or ""):
        errors.append(f"{name} no puede apuntar a localhost en producción ({value!r}).")


def validate_production_settings(settings: Settings) -> None:
    """Falla al arrancar si la configuración no es apta para internet."""
    if not settings.is_production:
        return

    errors: list[str] = []

    key = (settings.SECRET_KEY or "").strip()
    if key in WEAK_SECRET_KEYS or len(key) < 32:
        errors.append(
            "SECRET_KEY insegura en producción. Genere una clave única de al menos 32 caracteres: "
            'python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )

    if settings.DATABASE_URL.startswith("sqlite"):
        errors.append(
            "SQLite no está soportado en producción. Use PostgreSQL en DATABASE_URL."
        )

    if not os.getenv("CORS_ORIGINS", "").strip():
        errors.append(
            "Defina CORS_ORIGINS con su dominio HTTPS (ej. https://genotipia-lab.com)."
        )
    else:
        for origin in settings.CORS_ORIGINS:
            if not origin.lower().startswith("https://"):
                errors.append(f"CORS_ORIGINS debe ser HTTPS en producción: {origin!r}")
            _reject_localhost("CORS_ORIGINS", origin, errors)

    _require_https_url("FRONTEND_URL", settings.FRONTEND_URL, errors)
    _require_https_url("API_PUBLIC_URL", settings.API_PUBLIC_URL, errors)
    if settings.PUBLIC_SITE_URL:
        _require_https_url("PUBLIC_SITE_URL", settings.PUBLIC_SITE_URL, errors)

    _reject_localhost("FRONTEND_URL", settings.FRONTEND_URL, errors)
    _reject_localhost("API_PUBLIC_URL", settings.API_PUBLIC_URL, errors)

    if settings.AUTO_MIGRATE:
        errors.append(
            "AUTO_MIGRATE=true en producción. Use false y ejecute alembic upgrade head en el deploy."
        )

    if not os.getenv("ADMIN_INITIAL_PASSWORD", "").strip():
        errors.append(
            "Defina ADMIN_INITIAL_PASSWORD (mín. 12 caracteres) para el usuario admin inicial."
        )
    else:
        try:
            assert_strong_initial_password(
                os.getenv("ADMIN_INITIAL_PASSWORD", ""),
                label="ADMIN_INITIAL_PASSWORD",
            )
        except RuntimeError as exc:
            errors.append(str(exc))

    if errors:
        joined = "\n  - ".join(errors)
        raise RuntimeError(f"Configuración de producción inválida:\n  - {joined}")
