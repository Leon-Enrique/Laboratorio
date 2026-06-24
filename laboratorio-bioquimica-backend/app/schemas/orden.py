from typing import Optional, List, Any
from pydantic import BaseModel
from datetime import date, datetime
from app.schemas.usuario import UsuarioResponse
from app.schemas.parametro_examen import ParametroExamenResponse


class ExamenEnResultado(BaseModel):
    id: int
    nombre: str
    parametros: List[ParametroExamenResponse] = []

    class Config:
        from_attributes = True

class PacienteBase(BaseModel):
    dni: str
    nombre: str
    apellido: str
    fecha_nacimiento: date
    genero: str
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    nit: Optional[str] = None
    razon_social: Optional[str] = None

class PacienteCreate(PacienteBase):
    usuario_id: Optional[int] = None

class PacienteResponse(PacienteBase):
    id: int

    class Config:
        from_attributes = True

class ResultadoBase(BaseModel):
    examen_id: int
    valor_resultado: Optional[Any] = None  # Puede ser un dict/JSON
    pdf_url: Optional[str] = None

class ResultadoCreate(ResultadoBase):
    pass

class ResultadoResponse(ResultadoBase):
    id: int
    fecha_registro: datetime
    examen: Optional[ExamenEnResultado] = None

    class Config:
        from_attributes = True


class ConsultaPacienteRequest(BaseModel):
    codigo_orden: str
    dni: str
    fecha_nacimiento: date


class CodigoVerificacionResponse(BaseModel):
    existe: bool
    codigo_orden: str
    mensaje: str

class OrdenBase(BaseModel):
    paciente_id: int
    estado: str = "PENDIENTE"
    bioquimico_id: Optional[int] = None

class OrdenCreate(BaseModel):
    paciente_dni: str
    nombre_paciente: str
    apellido_paciente: str
    fecha_nacimiento_paciente: date
    genero_paciente: str
    telefono_paciente: Optional[str] = None
    direccion_paciente: Optional[str] = None
    examenes_ids: List[int]
    estado_pago: Optional[str] = "PENDIENTE"
    metodo_pago: Optional[str] = None
    medico_solicitante: Optional[str] = None
    prioridad: Optional[str] = "NORMAL"
    notas: Optional[str] = None
    requiere_factura: Optional[bool] = False
    nit_factura: Optional[str] = None
    razon_social_factura: Optional[str] = None


class OrdenMetaUpdate(BaseModel):
    prioridad: Optional[str] = None
    medico_solicitante: Optional[str] = None
    notas: Optional[str] = None


class OrdenPagoUpdate(BaseModel):
    estado_pago: str  # PENDIENTE | PAGADO
    metodo_pago: Optional[str] = None


class ComprobanteResumen(BaseModel):
    id: int
    numero_comprobante: Optional[int] = None
    codigo_orden: str
    fecha_creacion: datetime
    fecha_pago: Optional[datetime] = None
    estado_pago: str
    metodo_pago: Optional[str] = None
    precio_total: float
    requiere_factura: bool = False
    nit_factura: Optional[str] = None
    razon_social_factura: Optional[str] = None
    paciente_nombre: str
    paciente_apellido: str
    paciente_dni: str
    recepcionista_nombre: Optional[str] = None


class OrdenResponse(BaseModel):
    id: int
    codigo_orden: str
    numero_comprobante: Optional[int] = None
    fecha_creacion: datetime
    estado: str
    estado_pago: str = "PENDIENTE"
    metodo_pago: Optional[str] = None
    fecha_pago: Optional[datetime] = None
    medico_solicitante: Optional[str] = None
    prioridad: str = "NORMAL"
    notas: Optional[str] = None
    requiere_factura: bool = False
    nit_factura: Optional[str] = None
    razon_social_factura: Optional[str] = None
    precio_total: float
    paciente: PacienteResponse
    bioquimico: Optional[UsuarioResponse] = None
    recepcionista: Optional[UsuarioResponse] = None
    resultados: List[ResultadoResponse] = []

    class Config:
        from_attributes = True
