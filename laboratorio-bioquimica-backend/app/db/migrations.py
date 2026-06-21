"""Ejecuta migraciones Alembic y backfills de datos."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.config import settings
from app.db.migrate_lims import apply_legacy_schema_patches, run_data_backfills
from app.db.session import engine


def _alembic_config() -> Config:
    ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def _alembic_initial_schema_applied() -> bool:
    """True si create_all ya creó índices de la revisión inicial (BD Neon vacía)."""
    inspector = inspect(engine)
    if "movimientos_stock" not in inspector.get_table_names():
        return False
    index_names = {idx["name"] for idx in inspector.get_indexes("movimientos_stock")}
    return "ix_movimientos_stock_lote_id" in index_names


def upgrade_database() -> None:
    cfg = _alembic_config()
    if _alembic_initial_schema_applied():
        command.stamp(cfg, "head")
        return
    command.upgrade(cfg, "head")


def run_startup_migrations() -> None:
    if settings.RUN_LEGACY_SCHEMA_PATCHES:
        apply_legacy_schema_patches()
    if settings.AUTO_MIGRATE:
        upgrade_database()
    if settings.RUN_DATA_BACKFILL:
        run_data_backfills()
