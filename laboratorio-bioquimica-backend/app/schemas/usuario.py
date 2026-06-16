from typing import Optional
from pydantic import BaseModel, EmailStr

class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    rol: str = "paciente"
    activo: Optional[bool] = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: str
    activo: bool

    class Config:
        from_attributes = True

# JWT Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: str

class TokenData(BaseModel):
    email: Optional[str] = None
    rol: Optional[str] = None
