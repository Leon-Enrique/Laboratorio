from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date, datetime


class ProveedorBase(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None


class ProveedorResponse(ProveedorBase):
    id: int

    class Config:
        from_attributes = True


class ReactivoBase(BaseModel):
    nombre: str
    stock_actual: float = 0.0
    stock_minimo: float = 10.0
    stock_de_seguridad: float = 0.0
    tiempo_entrega_proveedor_dias: int = 7
    unidad_medida: str
    lote: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: Optional[int] = None


class ReactivoCreate(ReactivoBase):
    pass


class ReactivoMrpUpdate(BaseModel):
    stock_de_seguridad: Optional[float] = None
    tiempo_entrega_proveedor_dias: Optional[int] = None
    stock_minimo: Optional[float] = None
    proveedor_id: Optional[int] = None


class LoteBase(BaseModel):
    codigo_lote: str
    cantidad_disponible: float = Field(gt=0)
    fecha_vencimiento: date
    proveedor_id: Optional[int] = None


class LoteCreate(LoteBase):
    reactivo_id: int
    descripcion: Optional[str] = None


class LoteResponse(LoteBase):
    id: int
    reactivo_id: int
    fecha_ingreso: date
    estado: str
    dias_para_vencer: Optional[int] = None

    class Config:
        from_attributes = True


class ReactivoResponse(ReactivoBase):
    id: int
    proveedor: Optional[ProveedorResponse] = None
    total_lotes: Optional[int] = None
    lotes_activos: Optional[int] = None

    class Config:
        from_attributes = True


class MovimientoStockBase(BaseModel):
    reactivo_id: int
    cantidad: float
    tipo: str
    descripcion: Optional[str] = None


class MovimientoStockCreate(MovimientoStockBase):
    codigo_lote: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    proveedor_id: Optional[int] = None


class MovimientoStockResponse(MovimientoStockBase):
    id: int
    fecha: datetime
    lote_id: Optional[int] = None
    orden_id: Optional[int] = None
    usuario_id: Optional[int] = None
    usuario_nombre: Optional[str] = None
    codigo_lote: Optional[str] = None
    reactivo_nombre: Optional[str] = None
    stock_antes: Optional[float] = None
    stock_despues: Optional[float] = None
    stock_lote_antes: Optional[float] = None
    stock_lote_despues: Optional[float] = None

    class Config:
        from_attributes = True


class BajaLoteRequest(BaseModel):
    motivo: Optional[str] = "Vencimiento"


class MermaInventarioResponse(BaseModel):
    id: int
    id_insumo: int
    insumo_nombre: Optional[str] = None
    lote_id: Optional[int] = None
    codigo_lote: Optional[str] = None
    cantidad_perdida: float
    fecha_baja: datetime
    motivo: str

    class Config:
        from_attributes = True


class SugerenciaCompraResponse(BaseModel):
    reactivo_id: int
    nombre: str
    unidad_medida: str
    stock_actual: float
    consumo_diario_promedio: float
    tiempo_entrega_proveedor_dias: int
    stock_de_seguridad: float = 0
    stock_minimo: Optional[float] = None
    punto_reorden: float
    cantidad_sugerida: float
    proveedor_id: Optional[int] = None
    proveedor_nombre: Optional[str] = None
    alertas: List[str] = []


class OrdenPedidoCreate(BaseModel):
    reactivo_id: int
    cantidad_pedida: float = Field(gt=0)
    proveedor_id: Optional[int] = None
    fecha_esperada: Optional[date] = None
    notas: Optional[str] = None


class OrdenPedidoUpdate(BaseModel):
    estado: Optional[str] = None
    cantidad_pedida: Optional[float] = None
    proveedor_id: Optional[int] = None
    fecha_esperada: Optional[date] = None
    notas: Optional[str] = None


class OrdenPedidoResponse(BaseModel):
    id: int
    reactivo_id: int
    reactivo_nombre: Optional[str] = None
    proveedor_id: Optional[int] = None
    proveedor_nombre: Optional[str] = None
    proveedor_telefono: Optional[str] = None
    cantidad_pedida: float
    estado: str
    fecha_creacion: datetime
    fecha_esperada: Optional[date] = None
    notas: Optional[str] = None

    class Config:
        from_attributes = True


class AuditoriaInventarioResponse(BaseModel):
    total_reactivos: int
    total_lotes: int
    lotes_vencidos_con_stock: int
    lotes_proximos_vencer: int
    reactivos_bajo_minimo: int
    movimientos_ultimos_30_dias: int
    ultimos_movimientos: List[MovimientoStockResponse]
