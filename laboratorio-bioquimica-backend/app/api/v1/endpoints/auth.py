from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import Token, UsuarioResponse
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

router = APIRouter()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, rol: str, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "rol": rol}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    # Buscar por email
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email o contraseña incorrectos"
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        usuario.email, rol=usuario.rol, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "rol": usuario.rol,
        "nombre": usuario.nombre
    }

# Dependencias para proteger rutas
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise credentials_exception
    return usuario

def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if not current_user.activo:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Usuario = Depends(get_current_active_user)):
        if current_user.rol not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción"
            )
        return current_user
