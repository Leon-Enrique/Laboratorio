"""Ejecuta migraciones Alembic y backfills de datos."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.migrate_lims import apply_legacy_schema_patches, run_data_backfills


def _alembic_config() -> Config:
    ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def upgrade_database() -> None:
    command.upgrade(_alembic_config(), "head")


def run_startup_migrations() -> None:
    if settings.RUN_LEGACY_SCHEMA_PATCHES:
        apply_legacy_schema_patches()
    if settings.AUTO_MIGRATE:
        upgrade_database()
    if settings.RUN_DATA_BACKFILL:
        run_data_backfills()
