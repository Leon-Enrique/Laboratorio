from typing import Optional, List
from pydantic import BaseModel

from app.schemas.parametro_examen import ParametroExamenCreate, ParametroExamenResponse

class FormulaConsumoBase(BaseModel):
    reactivo_id: int
    cantidad_consumo: float

class FormulaConsumoCreate(FormulaConsumoBase):
    examen_id: int

class FormulaConsumoResponse(FormulaConsumoBase):
    id: int
    reactivo_nombre: Optional[str] = None

    class Config:
        from_attributes = True

class ExamenBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    preparacion: Optional[str] = None
    precio_usd: float
    tiempo_entrega_horas: int = 24
    visible: Optional[bool] = True

class ExamenCreate(ExamenBase):
    formulas: Optional[List[FormulaConsumoBase]] = []
    parametros: Optional[List[ParametroExamenCreate]] = []


class ExamenResponse(ExamenBase):
    id: int
    formulas: List[FormulaConsumoResponse] = []
    parametros: List[ParametroExamenResponse] = []

    class Config:
        from_attributes = True
