from typing import List, Optional

from pydantic import BaseModel, Field


class BusquedaCatalogoEvent(BaseModel):
    termino: str = Field(..., min_length=2, max_length=120)
    examen_ids: List[int] = Field(..., min_length=1, max_length=25)


class ClicCatalogoEvent(BaseModel):
    examen_id: int


class MasBuscadoResponse(BaseModel):
    examen_id: int
    nombre: str
    grupo: Optional[str] = None
    contador_busquedas: int
    contador_clics: int
    puntuacion: int
    ya_destacado: bool
    visible: bool
