import os
from types import SimpleNamespace

import pytest

from app.core.production_checks import assert_strong_initial_password, is_weak_password, validate_production_settings


def test_is_weak_password():
    assert is_weak_password("admin123") is True
    assert is_weak_password("short") is True
    assert is_weak_password("MiClaveSegura2026!") is False


def test_assert_strong_initial_password():
    with pytest.raises(RuntimeError):
        assert_strong_initial_password("admin123")


def test_production_rejects_insecure_config(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:4200")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "admin123")

    settings = SimpleNamespace(
        is_production=True,
        SECRET_KEY="SUPER_SECRET_KEY_BIOQUIMICA_2026",
        DATABASE_URL="sqlite:///./test.db",
        CORS_ORIGINS=["http://localhost:4200"],
        FRONTEND_URL="http://localhost:4200",
        API_PUBLIC_URL="http://localhost:8000",
        PUBLIC_SITE_URL="",
        AUTO_MIGRATE=True,
    )
    with pytest.raises(RuntimeError, match="Configuración de producción inválida"):
        validate_production_settings(settings)


def test_production_accepts_secure_config(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://genotipia-lab.com")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "ClaveSeguraLaboratorio2026")

    settings = SimpleNamespace(
        is_production=True,
        SECRET_KEY="x" * 48,
        DATABASE_URL="postgresql://user:pass@localhost:5432/laboratorio_db",
        CORS_ORIGINS=["https://genotipia-lab.com"],
        FRONTEND_URL="https://genotipia-lab.com",
        API_PUBLIC_URL="https://api.genotipia-lab.com",
        PUBLIC_SITE_URL="https://genotipia-lab.com",
        AUTO_MIGRATE=False,
    )
    validate_production_settings(settings)
