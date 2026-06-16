from typing import List, Optional
from pydantic import BaseModel


class ParametroExamenBase(BaseModel):
    nombre: str
    unidad: Optional[str] = None
    valor_min: Optional[float] = None
    valor_max: Optional[float] = None
    orden: int = 0


class ParametroExamenCreate(ParametroExamenBase):
    pass


class ParametroExamenResponse(ParametroExamenBase):
    id: int

    class Config:
        from_attributes = True
