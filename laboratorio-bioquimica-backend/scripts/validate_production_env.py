#!/usr/bin/env python3
"""
Valida un archivo .env de producción sin arrancar uvicorn.
Uso (desde laboratorio-bioquimica-backend):
  python scripts/validate_production_env.py
  python scripts/validate_production_env.py .env
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import dotenv_values


def main() -> int:
    backend_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_root))

    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else backend_root / ".env"

    if not env_path.is_file():
        print(f"ERROR: no existe {env_path}", file=sys.stderr)
        return 1

    # Cargar .env ANTES de importar app (validate_production corre al importar config)
    import os

    for key, value in dotenv_values(env_path).items():
        if value is not None:
            os.environ[key] = value
    os.environ["APP_ENV"] = "production"

    try:
        import importlib

        import app.core.config as config_module

        importlib.reload(config_module)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"OK: configuración de producción válida ({env_path.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
