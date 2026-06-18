# Laboratorio Bioquímica — Genotipia

Sistema LIMS para laboratorio clínico: recepción de órdenes, cola de trabajo, resultados, inventario FEFO, reportes y portal del paciente.

## Estructura

- `laboratorio-bioquimica-web` — Frontend Angular
- `laboratorio-bioquimica-backend` — API FastAPI + SQLAlchemy

## Backend

```powershell
cd laboratorio-bioquimica-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run_init_db.py
python -m uvicorn app.main:app --reload
```

API: http://localhost:8000/docs

## Frontend

```powershell
cd laboratorio-bioquimica-web
npm install
npm start
```

App: http://localhost:4200

## Credenciales demo

- Admin: `admin@laboratorio.com` / `admin123`

## Desarrollo vs publicar en internet

**Ahora:** sigue mejorando la página y el panel en local. No necesitas servidor ni dominio.

**Cuando quieras subir** (más adelante): todo está preparado en el repo. Lee **[DEPLOY.md](DEPLOY.md)** — guía paso a paso.

Verificación rápida en tu PC (sin subir nada):

```powershell
.\scripts\check-deploy-ready.ps1
```
