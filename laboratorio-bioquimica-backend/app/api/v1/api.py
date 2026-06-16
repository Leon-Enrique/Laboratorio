from fastapi import APIRouter
from app.api.v1.endpoints import auth, examenes, inventario, ordenes, reportes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(examenes.router, prefix="/examenes", tags=["Exámenes"])
api_router.include_router(inventario.router, prefix="/inventario", tags=["Inventario MRP"])
api_router.include_router(ordenes.router, prefix="/ordenes", tags=["Órdenes"])
api_router.include_router(reportes.router, prefix="/reportes", tags=["Reportes"])
