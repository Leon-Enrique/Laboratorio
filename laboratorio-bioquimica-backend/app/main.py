from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.db.migrate_lims import migrate_lims_inventory

app = FastAPI(
    title="Genotipia API",
    description="API REST para la gestión de pacientes, órdenes de exámenes y control de inventario MRP",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Salud"])
def health_check():
    return {
        "status": "healthy",
        "project": "Laboratorio Bioquímico API",
        "version": "1.0.0"
    }

# Rutas principales de la API v1
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    migrate_lims_inventory()

