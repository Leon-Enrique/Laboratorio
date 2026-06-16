from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel


class ResumenPeriodo(BaseModel):
    ordenes_entradas: int = 0
    ordenes_completadas: int = 0
    ingresos_entradas: float = 0.0
    ingresos_completadas: float = 0.0


class ResumenMesActual(ResumenPeriodo):
    anio: int
    mes: int
    etiqueta: str
    pendientes_del_mes: int = 0
    ticket_promedio: float = 0.0
    variacion_ordenes_pct: Optional[float] = None
    variacion_ingresos_pct: Optional[float] = None


class MesReporte(ResumenPeriodo):
    anio: int
    mes: int
    etiqueta: str
    etiqueta_corta: str


class TopExamenMes(BaseModel):
    examen_id: int
    nombre: str
    cantidad: int
    ingresos: float


class MesDestacado(BaseModel):
    etiqueta: str
    anio: int
    mes: int
    ordenes: int
    ingresos: float


class DashboardReporte(BaseModel):
    moneda: str = "USD"
    resumen_hoy: ResumenPeriodo
    resumen_mes_actual: ResumenMesActual
    pendientes_total: int
    meses: List[MesReporte]
    top_examenes_mes: List[TopExamenMes]
    mejor_mes: Optional[MesDestacado] = None
    peor_mes: Optional[MesDestacado] = None


class MovimientoDia(BaseModel):
    tipo: str  # ENTRADA | SALIDA
    hora: datetime
    hora_texto: str
    orden_id: int
    codigo_orden: str
    paciente: str
    monto: float
    estado_orden: str
    estado_pago: str
    metodo_pago: Optional[str] = None
    examenes: List[str] = []


class ResumenDia(BaseModel):
    fecha: date
    etiqueta_fecha: str
    entradas: int = 0
    salidas: int = 0
    ingresos_entradas: float = 0.0
    ingresos_salidas: float = 0.0
    cobrado_dia: float = 0.0
    pendiente_dia: float = 0.0


class ReporteDiario(BaseModel):
    moneda: str = "USD"
    resumen: ResumenDia
    movimientos: List[MovimientoDia]
