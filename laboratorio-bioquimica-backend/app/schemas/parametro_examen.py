from typing import List, Optional
from pydantic import BaseModel


class ParametroExamenBase(BaseModel):
    nombre: str
    tipo: Optional[str] = "Numero"
    grupo: Optional[str] = None
    seccion: Optional[str] = None
    llave: Optional[str] = None
    valor_defecto: Optional[str] = None
    unidad: Optional[str] = None
    decimales: Optional[int] = 2
    metodo_prueba: Optional[str] = None
    valor_referencia: Optional[str] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    orden: int = 0


class ParametroExamenCreate(ParametroExamenBase):
    pass


class ParametroExamenResponse(ParametroExamenBase):
    id: int

    class Config:
        from_attributes = True
