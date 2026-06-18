export interface Proveedor {
  id: number;
  nombre: string;
}

export interface Reactivo {
  id: number;
  nombre: string;
  stock_actual: number;
  stock_minimo: number;
  unidad_medida: string;
  lote: string;
  fecha_vencimiento: string;
  total_lotes?: number;
  lotes_activos?: number;
}

export interface Lote {
  id: number;
  reactivo_id: number;
  codigo_lote: string;
  cantidad_disponible: number;
  fecha_vencimiento: string;
  fecha_ingreso: string;
  estado: string;
  dias_para_vencer?: number;
}

export interface MovimientoInventario {
  id: number;
  reactivo_id: number;
  reactivo_nombre?: string;
  lote_id?: number;
  codigo_lote?: string;
  cantidad: number;
  tipo: string;
  fecha: string;
  descripcion?: string;
  usuario_nombre?: string;
  stock_antes?: number;
  stock_despues?: number;
}

export interface AuditoriaInventario {
  total_reactivos: number;
  total_lotes: number;
  lotes_vencidos_con_stock: number;
  lotes_proximos_vencer: number;
  reactivos_bajo_minimo: number;
  movimientos_ultimos_30_dias: number;
  ultimos_movimientos: MovimientoInventario[];
}

export interface MesReporte {
  anio: number;
  mes: number;
  etiqueta: string;
  etiqueta_corta: string;
  ordenes_entradas: number;
  ordenes_completadas: number;
  ingresos_entradas: number;
  ingresos_completadas: number;
}

export interface DashboardReporte {
  moneda: string;
  resumen_hoy: {
    ordenes_entradas: number;
    ordenes_completadas: number;
    ingresos_entradas: number;
    ingresos_completadas: number;
  };
  resumen_mes_actual: {
    anio: number;
    mes: number;
    etiqueta: string;
    ordenes_entradas: number;
    ordenes_completadas: number;
    ingresos_entradas: number;
    ingresos_completadas: number;
    pendientes_del_mes: number;
    ticket_promedio: number;
    variacion_ordenes_pct?: number | null;
    variacion_ingresos_pct?: number | null;
  };
  pendientes_total: number;
  meses: MesReporte[];
  top_examenes_mes: { examen_id: number; nombre: string; cantidad: number; ingresos: number }[];
  mejor_mes?: { etiqueta: string; anio: number; mes: number; ordenes: number; ingresos: number };
  peor_mes?: { etiqueta: string; anio: number; mes: number; ordenes: number; ingresos: number };
}

export interface MovimientoDia {
  tipo: 'ENTRADA' | 'SALIDA';
  hora: string;
  hora_texto: string;
  orden_id: number;
  codigo_orden: string;
  paciente: string;
  monto: number;
  estado_orden: string;
  estado_pago: string;
  metodo_pago?: string | null;
  examenes: string[];
}

export interface ReporteDiario {
  moneda: string;
  resumen: {
    fecha: string;
    etiqueta_fecha: string;
    entradas: number;
    salidas: number;
    ingresos_entradas: number;
    ingresos_salidas: number;
    cobrado_dia: number;
    pendiente_dia: number;
  };
  movimientos: MovimientoDia[];
}

export interface ParametroExamen {
  id?: number;
  nombre: string;
  tipo?: string;
  grupo?: string | null;
  seccion?: string | null;
  llave?: string | null;
  valor_defecto?: string | null;
  unidad?: string | null;
  decimales?: number;
  metodo_prueba?: string | null;
  valor_referencia?: string | null;
  valor_min?: number | null;
  valor_max?: number | null;
  orden?: number;
}

export interface Examen {
  id: number;
  nombre: string;
  descripcion: string;
  preparacion: string;
  precio_bob: number;
  tiempo_entrega_horas: number;
  visible: boolean;
  destacado?: boolean;
  tipo?: string;
  grupo?: string | null;
  grupo_impresion?: string | null;
  derivacion?: string | null;
  material_muestra?: string | null;
  estado?: string;
  codigo_abrev?: string | null;
  precio_derivacion?: number;
  etiqueta?: string | null;
  formulas?: { id?: number; reactivo_id: number; cantidad_consumo: number; reactivo_nombre?: string }[];
  parametros?: ParametroExamen[];
}

export interface Orden {
  id: number;
  codigo_orden: string;
  fecha_creacion: string;
  estado: string;
  estado_pago?: string;
  metodo_pago?: string | null;
  fecha_pago?: string | null;
  medico_solicitante?: string | null;
  prioridad?: string;
  notas?: string | null;
  requiere_factura?: boolean;
  nit_factura?: string | null;
  razon_social_factura?: string | null;
  precio_total: number;
  paciente: {
    dni: string;
    nombre: string;
    apellido: string;
    telefono?: string | null;
    direccion?: string | null;
    nit?: string | null;
    razon_social?: string | null;
    fecha_nacimiento?: string;
    genero?: string;
  };
  resultados: {
    id: number;
    examen_id: number;
    valor_resultado?: Record<string, string> | null;
    examen?: { id: number; nombre: string; parametros?: ParametroExamen[] };
    examen_nombre?: string;
  }[];
}

export type PanelTabId = 'ordenes' | 'inventario' | 'reportes' | 'historial' | 'config-catalogo' | 'config-analisis';

export type PanelNavId =
  | 'ordenes-lista'
  | 'ordenes-nueva'
  | 'ordenes-cobros'
  | 'inventario'
  | 'reportes-stats'
  | 'reportes-paciente'
  | 'config-catalogo'
  | 'config-catalogo-nuevo';
