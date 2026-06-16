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
