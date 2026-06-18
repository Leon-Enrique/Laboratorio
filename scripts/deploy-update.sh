#!/usr/bin/env bash
# Actualización en servidor Linux (VPS).
# Uso: ./scripts/deploy-update.sh
# Requisitos: git, python3, venv, node/npm, PostgreSQL, nginx (o similar)

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/laboratorio-bioquimica-backend"
FRONTEND="$ROOT/laboratorio-bioquimica-web"
WEB_ROOT="${WEB_ROOT:-/var/www/genotipia}"

echo "==> 1. Código actualizado desde Git"
cd "$ROOT"
git pull --ff-only

echo "==> 2. Backend: dependencias y migraciones"
cd "$BACKEND"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate
pip install -q -r requirements.txt
alembic upgrade head

echo "==> 3. Frontend: build producción"
cd "$FRONTEND"
npm ci
npm run build -- --configuration=production

echo "==> 4. Publicar sitio estático"
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete "$FRONTEND/dist/laboratorio-bioquimica-web/browser/" "$WEB_ROOT/"

echo "==> 5. Reiniciar API (systemd)"
if systemctl is-active --quiet genotipia-api 2>/dev/null; then
  sudo systemctl restart genotipia-api
  echo "Servicio genotipia-api reiniciado."
else
  echo "Aviso: servicio genotipia-api no encontrado. Inicie manualmente:"
  echo "  cd $BACKEND && source venv/bin/activate"
  echo "  uvicorn app.main:app --host 127.0.0.1 --port 8000"
fi

echo "==> Deploy completado."
