from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.migrations import run_startup_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_startup_migrations()
    yield


app = FastAPI(
    title="Genotipia API",
    description="API REST para la gestión de pacientes, órdenes de exámenes y control de inventario MRP",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Salud"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }


app.include_router(api_router, prefix=settings.API_V1_STR)
