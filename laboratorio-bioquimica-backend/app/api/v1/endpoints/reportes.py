from typing import Any
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import RoleChecker
from app.db.session import get_db
from app.schemas.reportes import DashboardReporte, ReporteDiario
from app.services import reportes_service as rep

router = APIRouter()

dependencias = [Depends(RoleChecker(["admin", "bioquimico"]))]


@router.get("/dashboard", response_model=DashboardReporte, dependencies=dependencias)
def dashboard_reportes(
    meses: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db),
) -> Any:
    return rep.generar_dashboard(db, meses_historial=meses)


@router.get("/dia", response_model=ReporteDiario, dependencies=dependencias)
def reporte_diario(
    fecha: date = Query(..., description="Fecha a consultar (YYYY-MM-DD)"),
    tipo: str = Query("todos", pattern="^(todos|entradas|salidas)$"),
    db: Session = Depends(get_db),
) -> Any:
    return rep.generar_reporte_dia(db, fecha=fecha, tipo=tipo)
