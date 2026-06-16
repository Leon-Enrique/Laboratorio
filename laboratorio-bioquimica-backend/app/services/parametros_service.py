"""Utilidades para parámetros de exámenes."""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.parametro_examen import ParametroExamen


def parametro_clave(nombre: str, unidad: Optional[str] = None) -> str:
    return f"{nombre} ({unidad})" if unidad else nombre


def guardar_parametros_examen(db: Session, examen_id: int, parametros_in) -> None:
    db.query(ParametroExamen).filter(ParametroExamen.examen_id == examen_id).delete()
    if not parametros_in:
        return
    for i, p in enumerate(parametros_in):
        db.add(
            ParametroExamen(
                examen_id=examen_id,
                nombre=p.nombre,
                unidad=p.unidad,
                valor_min=p.valor_min,
                valor_max=p.valor_max,
                orden=p.orden if p.orden else i,
            )
        )
