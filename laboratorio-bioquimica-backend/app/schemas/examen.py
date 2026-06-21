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
    precio_bob: float
    tiempo_entrega_horas: int = 24
    visible: Optional[bool] = True
    destacado: Optional[bool] = False
    titulo_destacado: Optional[str] = None
    subtitulo_destacado: Optional[str] = None
    descripcion_destacado: Optional[str] = None
    orden_destacado: Optional[int] = None
    tipo: Optional[str] = "Laboratorio"
    grupo: Optional[str] = None
    grupo_impresion: Optional[str] = None
    derivacion: Optional[str] = None
    material_muestra: Optional[str] = None
    estado: Optional[str] = "Activo"
    codigo_abrev: Optional[str] = None
    precio_derivacion: Optional[float] = 0
    etiqueta: Optional[str] = None

class ExamenCreate(ExamenBase):
    formulas: Optional[List[FormulaConsumoBase]] = []
    parametros: Optional[List[ParametroExamenCreate]] = []


class ExamenResponse(ExamenBase):
    id: int
    formulas: List[FormulaConsumoResponse] = []
    parametros: List[ParametroExamenResponse] = []

    class Config:
        from_attributes = True


class DestacadoInicioUpdate(BaseModel):
    destacado: bool
    titulo_destacado: Optional[str] = None
    subtitulo_destacado: Optional[str] = None
    descripcion_destacado: Optional[str] = None
    orden_destacado: Optional[int] = None
