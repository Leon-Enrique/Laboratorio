import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';

interface Proveedor {
  id: number;
  nombre: string;
}

interface Reactivo {
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

interface Lote {
  id: number;
  reactivo_id: number;
  codigo_lote: string;
  cantidad_disponible: number;
  fecha_vencimiento: string;
  fecha_ingreso: string;
  estado: string;
  dias_para_vencer?: number;
}

interface MovimientoInventario {
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

interface AuditoriaInventario {
  total_reactivos: number;
  total_lotes: number;
  lotes_vencidos_con_stock: number;
  lotes_proximos_vencer: number;
  reactivos_bajo_minimo: number;
  movimientos_ultimos_30_dias: number;
  ultimos_movimientos: MovimientoInventario[];
}

interface MesReporte {
  anio: number;
  mes: number;
  etiqueta: string;
  etiqueta_corta: string;
  ordenes_entradas: number;
  ordenes_completadas: number;
  ingresos_entradas: number;
  ingresos_completadas: number;
}

interface DashboardReporte {
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

interface MovimientoDia {
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

interface ReporteDiario {
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

interface ParametroExamen {
  id?: number;
  nombre: string;
  unidad?: string | null;
  valor_min?: number | null;
  valor_max?: number | null;
  orden?: number;
}

interface Examen {
  id: number;
  nombre: string;
  descripcion: string;
  preparacion: string;
  precio_usd: number;
  tiempo_entrega_horas: number;
  visible: boolean;
  formulas?: any[];
  parametros?: ParametroExamen[];
}

interface Orden {
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
  precio_total: number;
  paciente: {
    dni: string;
    nombre: string;
    apellido: string;
    telefono?: string | null;
    direccion?: string | null;
    fecha_nacimiento?: string;
    genero?: string;
  };
  resultados: any[];
}

@Component({
  selector: 'app-panel-admin',
  standalone: true,
  imports: [CommonModule, FormsModule, BrandLogoComponent],
  templateUrl: './panel.html',
  styleUrl: './panel.scss'
})
export class PanelAdminComponent implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  private router = inject(Router);

  nombreUsuario = this.auth.currentUser;
  rolUsuario = this.auth.currentRole;
  tabActiva = signal<string>('ordenes'); // ordenes | inventario | reportes | historial | config-catalogo

  // Reportes / dashboard
  reportes = signal<DashboardReporte | null>(null);
  reportesCargando = signal(false);
  reportesError = signal<string | null>(null);

  fechaConsultaReporte = signal<string>(new Date().toISOString().slice(0, 10));
  filtroTipoDia = signal<'todos' | 'entradas' | 'salidas'>('todos');
  reporteDia = signal<ReporteDiario | null>(null);
  reporteDiaCargando = signal(false);
  reporteDiaError = signal<string | null>(null);

  maxOrdenesGrafico = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return Math.max(...meses.map(m => m.ordenes_entradas), 1);
  });

  maxIngresosGrafico = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return Math.max(...meses.map(m => m.ingresos_entradas), 1);
  });

  mesesTablaDesc = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return [...meses].reverse();
  });

  // Listas de datos
  ordenes = signal<Orden[]>([]);
  busquedaOrdenes = signal<string>('');
  filtroOrdenesTab = signal<'todas' | 'proceso' | 'firmadas' | 'cobro_pendiente'>('todas');
  filtroFechaOrdenes = signal<'todas' | 'hoy' | 'semana' | 'mes'>('todas');
  paginaOrdenes = signal<number>(1);
  ordenSortCampo = signal<string>('fecha');
  ordenSortAsc = signal<boolean>(false);
  readonly itemsPorPagina = 8;
  ordenDetalle = signal<Orden | null>(null);
  mostrarDetalleOrden = signal<boolean>(false);

  resumenOrdenes = computed(() => {
    const list = this.ordenes();
    return {
      total: list.length,
      proceso: list.filter(o => o.estado !== 'COMPLETADO').length,
      firmadas: list.filter(o => o.estado === 'COMPLETADO').length,
      cobroPendiente: list.filter(o => (o.estado_pago || 'PENDIENTE') !== 'PAGADO').length
    };
  });

  ordenesFiltradas = computed(() => {
    const q = this.busquedaOrdenes().toLowerCase().trim();
    const tab = this.filtroOrdenesTab();
    return this.ordenes().filter(ord => {
      if (!this.pasaFiltroFecha(ord)) return false;
      if (tab === 'proceso' && ord.estado === 'COMPLETADO') return false;
      if (tab === 'firmadas' && ord.estado !== 'COMPLETADO') return false;
      if (tab === 'cobro_pendiente' && ord.estado_pago === 'PAGADO') return false;
      if (!q) return true;
      const examenes = this.examenesOrdenLista(ord).join(' ').toLowerCase();
      const paciente = `${ord.paciente.nombre} ${ord.paciente.apellido} ${ord.paciente.dni}`.toLowerCase();
      const medico = (ord.medico_solicitante || '').toLowerCase();
      return ord.codigo_orden.toLowerCase().includes(q) || paciente.includes(q) || examenes.includes(q) || medico.includes(q);
    });
  });

  ordenesOrdenadas = computed(() => {
    const list = [...this.ordenesFiltradas()];
    const campo = this.ordenSortCampo();
    const asc = this.ordenSortAsc();
    list.sort((a, b) => {
      let cmp = 0;
      switch (campo) {
        case 'codigo':
          cmp = a.codigo_orden.localeCompare(b.codigo_orden);
          break;
        case 'paciente':
          cmp = this.nombrePacienteDisplay(a).localeCompare(this.nombrePacienteDisplay(b));
          break;
        case 'total':
          cmp = a.precio_total - b.precio_total;
          break;
        case 'estado':
          cmp = a.estado.localeCompare(b.estado);
          break;
        case 'fecha':
        default:
          cmp = new Date(a.fecha_creacion).getTime() - new Date(b.fecha_creacion).getTime();
          break;
      }
      if (cmp === 0 && (a.prioridad || 'NORMAL') === 'URGENTE' && (b.prioridad || 'NORMAL') !== 'URGENTE') return -1;
      if (cmp === 0 && (b.prioridad || 'NORMAL') === 'URGENTE' && (a.prioridad || 'NORMAL') !== 'URGENTE') return 1;
      return asc ? cmp : -cmp;
    });
    return list;
  });

  ordenesPaginadas = computed(() => {
    const list = this.ordenesOrdenadas();
    const start = (this.paginaOrdenes() - 1) * this.itemsPorPagina;
    return list.slice(start, start + this.itemsPorPagina);
  });

  totalPaginasOrdenes = computed(() =>
    Math.max(1, Math.ceil(this.ordenesOrdenadas().length / this.itemsPorPagina))
  );

  reactivos = signal<Reactivo[]>([]);
  alertasInventario = signal<any[]>([]);
  examenesCatalogo = signal<Examen[]>([]);
  proveedores = signal<Proveedor[]>([]);

  // Formulario Nueva Orden (Recepción Rápida)
  nuevoDni = signal<string>('');
  nuevoNombre = signal<string>('');
  nuevoApellido = signal<string>('');
  nuevaFechaNac = signal<string>('');
  nuevoGenero = signal<string>('M');
  nuevoTelefono = signal<string>('');
  nuevaDireccion = signal<string>('');
  nuevoMedicoSolicitante = signal<string>('');
  nuevaOrdenUrgente = signal<boolean>(false);
  examenesSeleccionados = signal<number[]>([]);
  precioTotalAcumulado = signal<number>(0);
  ordenCobradaEnRecepcion = signal<boolean>(false);
  metodoPagoRecepcion = signal<string>('EFECTIVO');
  metodoPagoRapido = signal<string>('EFECTIVO');
  busquedaExamen = signal<string>('');
  mostrarDropdownExamenes = signal<boolean>(false);

  // Exámenes filtrados para el buscador (que no han sido seleccionados aún)
  examenesFiltradosBusqueda = computed(() => {
    const query = this.busquedaExamen().toLowerCase().trim();
    const seleccionados = this.examenesSeleccionados();
    return this.examenesCatalogo().filter(ex => {
      const match = !query || ex.nombre.toLowerCase().includes(query) || (ex.descripcion && ex.descripcion.toLowerCase().includes(query));
      return match && !seleccionados.includes(ex.id);
    });
  });

  // Exámenes seleccionados en formato objeto para renderizar los chips
  examenesSeleccionadosObjetos = computed(() => {
    const seleccionados = this.examenesSeleccionados();
    return this.examenesCatalogo().filter(ex => seleccionados.includes(ex.id));
  });

  // Ticket de Caja y Código QR de Tubos
  mostrarTicketModal = signal<boolean>(false);
  ticketOrden = signal<Orden | null>(null);

  // Formulario Nuevo Reactivo (Inventario)
  mostrarNuevoReactivoModal = signal<boolean>(false);
  nuevoReactivoNombre = signal<string>('');
  nuevoReactivoMin = signal<number>(10);
  nuevoReactivoUnidad = signal<string>('unidades');
  nuevoReactivoStockInicial = signal<number>(0);
  nuevoReactivoLote = signal<string>('');
  nuevoReactivoVencimiento = signal<string>('');
  nuevoReactivoProveedorId = signal<number | null>(null);

  // Formulario Nuevo Examen (Catálogo)
  mostrarNuevoExamenModal = signal<boolean>(false);
  nuevoExamenNombre = signal<string>('');
  nuevoExamenDesc = signal<string>('');
  nuevoExamenPrep = signal<string>('');
  nuevoExamenPrecio = signal<number>(0);
  nuevoExamenEntrega = signal<number>(24);
  nuevoExamenVisible = signal<boolean>(true);
  
  // Fórmula dinámica para nuevo examen
  recetaInsumos = signal<{ reactivo_id: number; cantidad_consumo: number }[]>([]);

  // Formulario Edición Examen (Catálogo)
  examenEditando = signal<Examen | null>(null);
  editExamenNombre = signal<string>('');
  editExamenDesc = signal<string>('');
  editExamenPrep = signal<string>('');
  editExamenPrecio = signal<number>(0);
  editExamenEntrega = signal<number>(24);
  editExamenVisible = signal<boolean>(true);
  editRecetaInsumos = signal<{ reactivo_id: number; cantidad_consumo: number }[]>([]);

  // Formulario Carga Resultados (Bioquímico)
  ordenSeleccionadaResultados = signal<Orden | null>(null);
  valoresResultados = signal<{ [key: string]: string }>({});
  referenciasResultados = signal<Record<string, string>>({});

  // Formulario Entrada Inventario (Reabastecer)
  reactivoSeleccionadoReorden = signal<Reactivo | null>(null);
  cantidadIngreso = signal<number>(100);
  loteIngreso = signal<string>('');
  vencimientoIngreso = signal<string>('');

  // LIMS multi-lote
  reactivoExpandido = signal<number | null>(null);
  lotesPorReactivo = signal<Record<number, Lote[]>>({});
  lotesCargando = signal<number | null>(null);
  mostrarHistorialInventario = signal<boolean>(false);
  movimientosInventario = signal<MovimientoInventario[]>([]);
  filtroMovimientoReactivo = signal<number | null>(null);
  auditoriaInventario = signal<AuditoriaInventario | null>(null);
  mostrarAuditoriaInventario = signal<boolean>(false);

  // Historial Clínico de Pacientes
  busquedaDniHistorial = signal<string>('');
  historialOrdenes = signal<Orden[]>([]);
  pacienteHistorialCargado = signal<any | null>(null);
  historialError = signal<string | null>(null);
  historialCargando = signal<boolean>(false);

  // Autocomplete de pacientes para historial
  busquedaPacienteHistorial = signal<string>('');
  pacientesEncontrados = signal<{ dni: string; nombre: string; apellido: string }[]>([]);
  mostrarDropdownPacientes = signal<boolean>(false);
  busquedaPacienteDebounce: any = null;

  ngOnInit() {
    this.cargarDatosOrdenes();
    this.cargarDatosInventario();
    this.cargarExamenesCatalogo();
    this.cargarProveedores();
  }

  cambiarTab(tab: string) {
    this.tabActiva.set(tab);
    if (tab === 'ordenes') {
      this.cargarDatosOrdenes();
    } else if (tab === 'inventario') {
      this.cargarDatosInventario();
    } else if (tab === 'reportes') {
      this.cargarReportes();
    } else if (tab === 'config-catalogo') {
      this.cargarExamenesCatalogo();
    }
  }

  cargarDatosOrdenes() {
    this.api.get<Orden[]>('/ordenes/').subscribe(data => this.ordenes.set(data));
  }

  cargarReportes() {
    this.reportesCargando.set(true);
    this.reportesError.set(null);
    this.api.get<DashboardReporte>('/reportes/dashboard?meses=12').subscribe({
      next: (data) => {
        this.reportes.set(data);
        this.reportesCargando.set(false);
      },
      error: (err) => {
        this.reportesError.set('No se pudieron cargar los reportes. ' + (err.error?.detail || err.message));
        this.reportesCargando.set(false);
      }
    });
    this.cargarReporteDia();
  }

  cargarReporteDia() {
    this.reporteDiaCargando.set(true);
    this.reporteDiaError.set(null);
    const fecha = this.fechaConsultaReporte();
    const tipo = this.filtroTipoDia();
    this.api.get<ReporteDiario>(`/reportes/dia?fecha=${fecha}&tipo=${tipo}`).subscribe({
      next: (data) => {
        this.reporteDia.set(data);
        this.reporteDiaCargando.set(false);
      },
      error: (err) => {
        this.reporteDiaError.set('No se pudo cargar el detalle del día. ' + (err.error?.detail || err.message));
        this.reporteDiaCargando.set(false);
      }
    });
  }

  cambiarFiltroDia(tipo: 'todos' | 'entradas' | 'salidas') {
    this.filtroTipoDia.set(tipo);
    this.cargarReporteDia();
  }

  irADiaRelativo(offset: number) {
    const base = new Date(this.fechaConsultaReporte() + 'T12:00:00');
    base.setDate(base.getDate() + offset);
    this.fechaConsultaReporte.set(base.toISOString().slice(0, 10));
    this.cargarReporteDia();
  }

  irAHoyReporte() {
    this.fechaConsultaReporte.set(new Date().toISOString().slice(0, 10));
    this.cargarReporteDia();
  }

  alturaBarra(valor: number, maximo: number): number {
    if (!maximo || valor <= 0) return 4;
    return Math.max(8, Math.round((valor / maximo) * 100));
  }

  formatearVariacion(pct: number): string {
    const signo = pct > 0 ? '+' : '';
    return `${signo}${pct}%`;
  }

  cargarDatosInventario() {
    this.api.get<Reactivo[]>('/inventario/reactivos').subscribe(data => this.reactivos.set(data));
    this.api.get<any[]>('/inventario/alertas').subscribe(data => this.alertasInventario.set(data));
    if (this.mostrarAuditoriaInventario()) {
      this.cargarAuditoriaInventario();
    }
  }

  toggleExpandirReactivo(reactivo: Reactivo) {
    if (this.reactivoExpandido() === reactivo.id) {
      this.reactivoExpandido.set(null);
      return;
    }
    this.reactivoExpandido.set(reactivo.id);
    this.cargarLotesReactivo(reactivo.id);
  }

  cargarLotesReactivo(reactivoId: number) {
    this.lotesCargando.set(reactivoId);
    this.api.get<Lote[]>(`/inventario/reactivos/${reactivoId}/lotes`).subscribe({
      next: (lotes) => {
        this.lotesPorReactivo.set({ ...this.lotesPorReactivo(), [reactivoId]: lotes });
        this.lotesCargando.set(null);
      },
      error: () => this.lotesCargando.set(null)
    });
  }

  estadoLotePill(estado: string, dias?: number): string {
    if (estado === 'VENCIDO') return 'pill-danger';
    if (estado === 'BLOQUEADO' || estado === 'AGOTADO') return 'pill-warning';
    if (dias !== undefined && dias <= 90) return 'pill-warning';
    return 'pill-success';
  }

  etiquetaEstadoLote(lote: Lote): string {
    if (lote.estado === 'VENCIDO') return 'Vencido';
    if (lote.estado === 'BLOQUEADO') return 'Bloqueado';
    if (lote.estado === 'AGOTADO') return 'Agotado';
    if (lote.dias_para_vencer !== undefined && lote.dias_para_vencer <= 90) return 'Próximo a vencer';
    return 'Activo';
  }

  darBajaLote(lote: Lote, reactivoId: number) {
    const motivo = prompt(`Motivo de baja para lote ${lote.codigo_lote}:`, 'Retiro por vencimiento');
    if (motivo === null) return;
    this.api.post(`/inventario/lotes/${lote.id}/baja`, { motivo }).subscribe({
      next: () => {
        alert('Lote dado de baja correctamente.');
        this.cargarLotesReactivo(reactivoId);
        this.cargarDatosInventario();
      },
      error: (err) => alert('Error al dar de baja: ' + (err.error?.detail || err.message))
    });
  }

  abrirHistorialInventario(reactivoId?: number) {
    this.filtroMovimientoReactivo.set(reactivoId ?? null);
    this.mostrarHistorialInventario.set(true);
    this.cargarMovimientosInventario(reactivoId);
  }

  cargarMovimientosInventario(reactivoId?: number) {
    const params = reactivoId ? `?reactivo_id=${reactivoId}&limit=100` : '?limit=100';
    this.api.get<MovimientoInventario[]>(`/inventario/movimientos${params}`).subscribe({
      next: (data) => this.movimientosInventario.set(data)
    });
  }

  toggleAuditoriaInventario() {
    const visible = !this.mostrarAuditoriaInventario();
    this.mostrarAuditoriaInventario.set(visible);
    if (visible) {
      this.cargarAuditoriaInventario();
    }
  }

  cargarAuditoriaInventario() {
    this.api.get<AuditoriaInventario>('/inventario/auditoria').subscribe({
      next: (data) => this.auditoriaInventario.set(data)
    });
  }

  cargarExamenesCatalogo() {
    // Para administradores cargamos todos los exámenes, incluyendo los ocultos
    this.api.get<Examen[]>('/examenes/admin-lista').subscribe(data => this.examenesCatalogo.set(data));
  }

  cargarProveedores() {
    this.api.get<Proveedor[]>('/inventario/proveedores').subscribe(data => this.proveedores.set(data));
  }

  toggleExamenSeleccionado(id: number) {
    const seleccionados = [...this.examenesSeleccionados()];
    const index = seleccionados.indexOf(id);
    if (index > -1) {
      seleccionados.splice(index, 1);
    } else {
      seleccionados.push(id);
    }
    this.examenesSeleccionados.set(seleccionados);
    this.calcularPrecioTotalAcumulado();
  }

  seleccionarExamenAutocomplete(id: number) {
    const seleccionados = [...this.examenesSeleccionados()];
    if (!seleccionados.includes(id)) {
      seleccionados.push(id);
      this.examenesSeleccionados.set(seleccionados);
      this.calcularPrecioTotalAcumulado();
    }
    this.busquedaExamen.set('');
    this.mostrarDropdownExamenes.set(false);
  }

  deseleccionarExamenChip(id: number) {
    const seleccionados = this.examenesSeleccionados().filter(exId => exId !== id);
    this.examenesSeleccionados.set(seleccionados);
    this.calcularPrecioTotalAcumulado();
  }

  ocultarDropdownConRetraso() {
    setTimeout(() => {
      this.mostrarDropdownExamenes.set(false);
    }, 200);
  }

  calcularPrecioTotalAcumulado() {
    const seleccionados = this.examenesSeleccionados();
    let total = 0;
    seleccionados.forEach(id => {
      const examen = this.examenesCatalogo().find(ex => ex.id === id);
      if (examen) {
        total += examen.precio_usd;
      }
    });
    this.precioTotalAcumulado.set(total);
  }

  crearNuevaOrden() {
    if (this.examenesSeleccionados().length === 0 || !this.nuevoDni() || !this.nuevoNombre() || !this.nuevoApellido()) {
      alert('Por favor complete todos los datos requeridos y seleccione al menos un examen.');
      return;
    }

    const payload = {
      paciente_dni: this.nuevoDni(),
      nombre_paciente: this.nuevoNombre(),
      apellido_paciente: this.nuevoApellido(),
      fecha_nacimiento_paciente: this.nuevaFechaNac(),
      genero_paciente: this.nuevoGenero(),
      telefono_paciente: this.nuevoTelefono(),
      direccion_paciente: this.nuevaDireccion(),
      examenes_ids: this.examenesSeleccionados(),
      estado_pago: this.ordenCobradaEnRecepcion() ? 'PAGADO' : 'PENDIENTE',
      metodo_pago: this.ordenCobradaEnRecepcion() ? this.metodoPagoRecepcion() : null,
      medico_solicitante: this.nuevoMedicoSolicitante() || null,
      prioridad: this.nuevaOrdenUrgente() ? 'URGENTE' : 'NORMAL'
    };

    this.api.post<Orden>('/ordenes/', payload).subscribe({
      next: (data) => {
        // Enlazar nombres a los resultados del comprobante
        if (data.resultados) {
          data.resultados.forEach(res => {
            const ex = this.examenesCatalogo().find(e => e.id === res.examen_id);
            res.examen_nombre = ex ? ex.nombre : 'Examen Clínico';
          });
        }
        this.ticketOrden.set(data);
        this.mostrarTicketModal.set(true);
        this.limpiarFormularioOrden();
        this.cargarDatosOrdenes();
      },
      error: (err) => alert('Error al crear orden: ' + (err.error?.detail || err.message))
    });
  }

  limpiarFormularioOrden() {
    this.nuevoDni.set('');
    this.nuevoNombre.set('');
    this.nuevoApellido.set('');
    this.nuevaFechaNac.set('');
    this.nuevoGenero.set('M');
    this.nuevoTelefono.set('');
    this.nuevaDireccion.set('');
    this.nuevoMedicoSolicitante.set('');
    this.nuevaOrdenUrgente.set(false);
    this.examenesSeleccionados.set([]);
    this.precioTotalAcumulado.set(0);
    this.ordenCobradaEnRecepcion.set(false);
    this.metodoPagoRecepcion.set('EFECTIVO');
  }

  labelMetodoPago(metodo: string | null | undefined): string {
    const map: Record<string, string> = {
      EFECTIVO: 'Efectivo',
      TRANSFERENCIA: 'Transferencia',
      TARJETA: 'Tarjeta',
      QR: 'QR'
    };
    return metodo ? (map[metodo] || metodo) : '';
  }

  tituloPalabras(texto: string): string {
    if (!texto) return '';
    return texto.trim().split(/\s+/).map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join(' ');
  }

  nombrePacienteDisplay(ord: Orden): string {
    return `${this.tituloPalabras(ord.paciente.nombre)} ${this.tituloPalabras(ord.paciente.apellido)}`.trim();
  }

  examenesOrdenLista(ord: Orden): string[] {
    if (!ord.resultados?.length) return [];
    return ord.resultados.map(res => {
      if (res.examen?.nombre) return res.examen.nombre;
      const ex = this.examenesCatalogo().find(e => e.id === res.examen_id);
      return ex?.nombre || `Examen #${res.examen_id}`;
    });
  }

  cambiarFiltroOrdenesTab(tab: 'todas' | 'proceso' | 'firmadas' | 'cobro_pendiente') {
    this.filtroOrdenesTab.set(tab);
    this.paginaOrdenes.set(1);
  }

  cambiarFiltroFechaOrdenes(f: 'todas' | 'hoy' | 'semana' | 'mes') {
    this.filtroFechaOrdenes.set(f);
    this.paginaOrdenes.set(1);
  }

  onBusquedaOrdenesChange(val: string) {
    this.busquedaOrdenes.set(val);
    this.paginaOrdenes.set(1);
  }

  private inicioDia(d: Date): Date {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  pasaFiltroFecha(ord: Orden): boolean {
    const f = this.filtroFechaOrdenes();
    if (f === 'todas') return true;
    const fc = new Date(ord.fecha_creacion);
    const hoy = this.inicioDia(new Date());
    const ordDia = this.inicioDia(fc);
    if (f === 'hoy') return ordDia.getTime() === hoy.getTime();
    if (f === 'semana') return (hoy.getTime() - ordDia.getTime()) <= 7 * 86400000;
    if (f === 'mes') return fc.getMonth() === hoy.getMonth() && fc.getFullYear() === hoy.getFullYear();
    return true;
  }

  ordenarPor(campo: string) {
    if (this.ordenSortCampo() === campo) {
      this.ordenSortAsc.update(v => !v);
    } else {
      this.ordenSortCampo.set(campo);
      this.ordenSortAsc.set(campo === 'paciente' || campo === 'codigo');
    }
    this.paginaOrdenes.set(1);
  }

  sortIcon(campo: string): string {
    if (this.ordenSortCampo() !== campo) return '↕';
    return this.ordenSortAsc() ? '↑' : '↓';
  }

  cambiarPaginaOrdenes(delta: number) {
    const next = this.paginaOrdenes() + delta;
    if (next >= 1 && next <= this.totalPaginasOrdenes()) {
      this.paginaOrdenes.set(next);
    }
  }

  labelEstadoLab(estado: string): string {
    if (estado === 'COMPLETADO') return 'Firmado';
    if (estado === 'PROCESANDO') return 'Resultados cargados';
    return 'En análisis';
  }

  claseEstadoLab(estado: string): string {
    if (estado === 'COMPLETADO') return 'pill-success';
    if (estado === 'PROCESANDO') return 'pill-info';
    return 'pill-warning';
  }

  abrirDetalleOrden(ord: Orden) {
    this.ordenDetalle.set(ord);
    this.mostrarDetalleOrden.set(true);
  }

  cerrarDetalleOrden() {
    this.mostrarDetalleOrden.set(false);
    this.ordenDetalle.set(null);
  }

  reimprimirTicket(ord: Orden, $event?: Event) {
    $event?.stopPropagation();
    const ticket: Orden = {
      ...ord,
      paciente: { ...ord.paciente },
      resultados: ord.resultados.map(res => ({
        ...res,
        examen_nombre: res.examen?.nombre
          || this.examenesCatalogo().find(e => e.id === res.examen_id)?.nombre
          || 'Examen Clínico'
      }))
    };
    this.ticketOrden.set(ticket);
    this.mostrarTicketModal.set(true);
  }

  togglePrioridadUrgente(ord: Orden) {
    const nueva = (ord.prioridad || 'NORMAL') === 'URGENTE' ? 'NORMAL' : 'URGENTE';
    this.api.patch<Orden>(`/ordenes/${ord.id}/meta`, { prioridad: nueva }).subscribe({
      next: (updated) => {
        this.ordenes.update(list =>
          list.map(o => (o.id === updated.id ? { ...o, ...updated } : o))
        );
        if (this.ordenDetalle()?.id === updated.id) {
          this.ordenDetalle.set({ ...this.ordenDetalle()!, ...updated });
        }
      },
      error: (err) => alert('Error al cambiar prioridad: ' + (err.error?.detail || err.message))
    });
  }

  actualizarEstadoPago(orden: Orden, estado: 'PENDIENTE' | 'PAGADO') {
    const payload: { estado_pago: string; metodo_pago?: string } = { estado_pago: estado };
    if (estado === 'PAGADO') {
      payload.metodo_pago = this.metodoPagoRapido();
    }

    this.api.patch<Orden>(`/ordenes/${orden.id}/pago`, payload).subscribe({
      next: (updated) => {
        this.ordenes.update(list =>
          list.map(o => (o.id === updated.id ? { ...o, ...updated } : o))
        );
      },
      error: (err) => alert('Error al actualizar pago: ' + (err.error?.detail || err.message))
    });
  }

  // Activar/Desactivar visibilidad de examen (Solo Admin)
  toggleVisibilidadExamen(examen: Examen) {
    // Actualización optimista: cambia el estado visual inmediatamente sin esperar al backend
    const listaActualizada = this.examenesCatalogo().map(ex =>
      ex.id === examen.id ? { ...ex, visible: !ex.visible } : ex
    );
    this.examenesCatalogo.set(listaActualizada);

    this.api.put<Examen>(`/examenes/${examen.id}/visibilidad`, {}).subscribe({
      next: () => {
        // Sincroniza con el backend para confirmar el estado real
        this.cargarExamenesCatalogo();
      },
      error: (err: any) => {
        // Revierte el cambio visual si el backend falla
        this.cargarExamenesCatalogo();
        alert('Error al cambiar visibilidad: ' + (err.error?.detail || err.message));
      }
    });
  }

  // Agregar reactivo nuevo al inventario (Solo Admin)
  crearNuevoReactivo() {
    if (!this.nuevoReactivoNombre() || !this.nuevoReactivoUnidad()) {
      alert('Por favor ingrese el nombre del reactivo y la unidad de medida.');
      return;
    }

    const payload = {
      nombre: this.nuevoReactivoNombre(),
      stock_actual: this.nuevoReactivoStockInicial(),
      stock_minimo: this.nuevoReactivoMin(),
      unidad_medida: this.nuevoReactivoUnidad(),
      lote: this.nuevoReactivoLote() || null,
      fecha_vencimiento: this.nuevoReactivoVencimiento() || null,
      proveedor_id: this.nuevoReactivoProveedorId()
    };

    this.api.post('/inventario/reactivos', payload).subscribe({
      next: () => {
        alert('Reactivo registrado con éxito en la bodega del laboratorio.');
        this.mostrarNuevoReactivoModal.set(false);
        this.limpiarFormularioReactivo();
        this.cargarDatosInventario();
      },
      error: (err) => alert('Error al registrar reactivo: ' + (err.error?.detail || err.message))
    });
  }

  limpiarFormularioReactivo() {
    this.nuevoReactivoNombre.set('');
    this.nuevoReactivoStockInicial.set(0);
    this.nuevoReactivoMin.set(10);
    this.nuevoReactivoUnidad.set('unidades');
    this.nuevoReactivoLote.set('');
    this.nuevoReactivoVencimiento.set('');
    this.nuevoReactivoProveedorId.set(null);
  }

  // Configuración de Fórmula de Consumo dinámica en creación de Examen
  agregarFilaReceta() {
    this.recetaInsumos.set([
      ...this.recetaInsumos(),
      { reactivo_id: this.reactivos()[0]?.id || 0, cantidad_consumo: 1 }
    ]);
  }

  eliminarFilaReceta(index: number) {
    const receta = [...this.recetaInsumos()];
    receta.splice(index, 1);
    this.recetaInsumos.set(receta);
  }

  crearNuevoExamen() {
    if (!this.nuevoExamenNombre() || this.nuevoExamenPrecio() <= 0) {
      alert('Por favor ingrese el nombre del examen y un precio válido.');
      return;
    }

    // Filtrar recetas sin insumo asignado
    const formulas = this.recetaInsumos().filter(f => f.reactivo_id > 0);

    const payload = {
      nombre: this.nuevoExamenNombre(),
      descripcion: this.nuevoExamenDesc(),
      preparacion: this.nuevoExamenPrep(),
      precio_usd: this.nuevoExamenPrecio(),
      tiempo_entrega_horas: this.nuevoExamenEntrega(),
      visible: this.nuevoExamenVisible(),
      formulas: formulas
    };

    this.api.post('/examenes/', payload).subscribe({
      next: () => {
        alert('Nuevo examen y su fórmula de consumo MRP creados con éxito.');
        this.mostrarNuevoExamenModal.set(false);
        this.limpiarFormularioExamen();
        this.cargarExamenesCatalogo();
      },
      error: (err) => alert('Error al crear examen: ' + (err.error?.detail || err.message))
    });
  }

  limpiarFormularioExamen() {
    this.nuevoExamenNombre.set('');
    this.nuevoExamenDesc.set('');
    this.nuevoExamenPrep.set('');
    this.nuevoExamenPrecio.set(0);
    this.nuevoExamenEntrega.set(24);
    this.nuevoExamenVisible.set(true);
    this.recetaInsumos.set([]);
  }

  abrirEdicionExamen(examen: Examen) {
    this.examenEditando.set(examen);
    this.editExamenNombre.set(examen.nombre);
    this.editExamenDesc.set(examen.descripcion || '');
    this.editExamenPrep.set(examen.preparacion || '');
    this.editExamenPrecio.set(examen.precio_usd);
    this.editExamenEntrega.set(examen.tiempo_entrega_horas);
    this.editExamenVisible.set(examen.visible);
    // Cargar fórmulas existentes del examen
    const formulas = (examen.formulas || []).map((f: any) => ({
      reactivo_id: f.reactivo_id,
      cantidad_consumo: f.cantidad_consumo
    }));
    this.editRecetaInsumos.set(formulas);
  }

  guardarEdicionExamen() {
    const examen = this.examenEditando();
    if (!examen) return;
    if (!this.editExamenNombre() || this.editExamenPrecio() <= 0) {
      alert('Por favor ingrese el nombre del examen y un precio válido.');
      return;
    }
    const formulas = this.editRecetaInsumos().filter(f => f.reactivo_id > 0);
    const payload = {
      nombre: this.editExamenNombre(),
      descripcion: this.editExamenDesc(),
      preparacion: this.editExamenPrep(),
      precio_usd: this.editExamenPrecio(),
      tiempo_entrega_horas: this.editExamenEntrega(),
      visible: this.editExamenVisible(),
      formulas: formulas
    };
    this.api.put(`/examenes/${examen.id}`, payload).subscribe({
      next: () => {
        alert('Análisis clínico actualizado con éxito.');
        this.examenEditando.set(null);
        this.cargarExamenesCatalogo();
      },
      error: (err: any) => alert('Error al actualizar examen: ' + (err.error?.detail || err.message))
    });
  }

  cancelarEdicionExamen() {
    this.examenEditando.set(null);
  }

  agregarFilaEditReceta() {
    this.editRecetaInsumos.set([
      ...this.editRecetaInsumos(),
      { reactivo_id: this.reactivos()[0]?.id || 0, cantidad_consumo: 1 }
    ]);
  }

  eliminarFilaEditReceta(index: number) {
    const receta = [...this.editRecetaInsumos()];
    receta.splice(index, 1);
    this.editRecetaInsumos.set(receta);
  }

  abrirDialogoCargarResultados(orden: Orden) {
    this.ordenSeleccionadaResultados.set(orden);
    this.valoresResultados.set(this.construirCamposResultados(orden));
    this.referenciasResultados.set(this.construirReferenciasResultados(orden));
  }

  parametroClave(p: ParametroExamen): string {
    return p.unidad ? `${p.nombre} (${p.unidad})` : p.nombre;
  }

  formatReferencia(p: ParametroExamen): string {
    if (p.valor_min != null && p.valor_max != null) {
      return `${p.valor_min} – ${p.valor_max}${p.unidad ? ' ' + p.unidad : ''}`;
    }
    if (p.valor_max != null) return `≤ ${p.valor_max}${p.unidad ? ' ' + p.unidad : ''}`;
    if (p.valor_min != null) return `≥ ${p.valor_min}${p.unidad ? ' ' + p.unidad : ''}`;
    return '';
  }

  construirCamposResultados(orden: Orden): Record<string, string> {
    const valores: Record<string, string> = {};
    orden.resultados.forEach(res => {
      const examen = this.examenesCatalogo().find(e => e.id === res.examen_id);
      const params = this.parametrosDeExamen(examen, res.examen_id);
      params.forEach(p => {
        const key = this.parametroClave(p);
        if (res.valor_resultado) {
          valores[key] = res.valor_resultado[key] ?? res.valor_resultado[p.nombre] ?? '';
        } else {
          valores[key] = '';
        }
      });
    });
    return valores;
  }

  construirReferenciasResultados(orden: Orden): Record<string, string> {
    const refs: Record<string, string> = {};
    orden.resultados.forEach(res => {
      const examen = this.examenesCatalogo().find(e => e.id === res.examen_id);
      this.parametrosDeExamen(examen, res.examen_id).forEach(p => {
        const ref = this.formatReferencia(p);
        if (ref) refs[this.parametroClave(p)] = ref;
      });
    });
    return refs;
  }

  parametrosDeExamen(examen: Examen | undefined, examenId: number): ParametroExamen[] {
    if (examen?.parametros?.length) {
      return [...examen.parametros].sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0));
    }
    const nombre = examen?.nombre || `Examen #${examenId}`;
    return [{ nombre: `Resultado ${nombre}`, unidad: '' }];
  }

  buildPayloadResultados(orden: Orden) {
    return orden.resultados.map(res => {
      const examen = this.examenesCatalogo().find(e => e.id === res.examen_id);
      const valor: Record<string, string> = {};
      this.parametrosDeExamen(examen, res.examen_id).forEach(p => {
        const key = this.parametroClave(p);
        valor[key] = this.valoresResultados()[key] ?? '';
      });
      return { examen_id: res.examen_id, valor_resultado: valor, pdf_url: null };
    });
  }

  qrOrdenUrl(codigo: string | undefined | null): string {
    if (!codigo) return '';
    return `${this.api.apiBaseUrl}/ordenes/qr/${codigo}`;
  }

  guardarBorradorResultados() {
    const orden = this.ordenSeleccionadaResultados();
    if (!orden) return;

    this.api.post(`/ordenes/${orden.id}/valores`, this.buildPayloadResultados(orden)).subscribe({
      next: () => {
        alert('Borrador de resultados guardado correctamente.');
        this.ordenSeleccionadaResultados.set(null);
        this.cargarDatosOrdenes();
      },
      error: (err) => alert('Error al guardar borrador: ' + (err.error?.detail || err.message))
    });
  }

  // Validar, firmar y descontar stock automáticamente
  firmarYAprobarResultados() {
    const orden = this.ordenSeleccionadaResultados();
    if (!orden) return;

    this.api.post(`/ordenes/${orden.id}/valores`, this.buildPayloadResultados(orden)).subscribe({
      next: () => {
        this.api.post(`/ordenes/${orden.id}/aprobar`, {}).subscribe({
          next: () => {
            alert('¡Resultados firmados electrónicamente con éxito! Se ha generado el informe oficial protegido e iniciado el descuento automático de insumos en bodega (MRP).');
            this.ordenSeleccionadaResultados.set(null);
            this.cargarDatosOrdenes();
            this.cargarDatosInventario();
          },
          error: (err) => alert('Error al firmar: ' + (err.error?.detail || err.message))
        });
      },
      error: (err) => alert('Error al guardar valores preliminares: ' + (err.error?.detail || err.message))
    });
  }

  buscarHistorialPaciente() {
    const dni = this.busquedaDniHistorial().trim();
    if (!dni) return;

    this.historialCargando.set(true);
    this.historialError.set(null);
    this.historialOrdenes.set([]);
    this.pacienteHistorialCargado.set(null);

    this.api.get<Orden[]>(`/ordenes/pacientes/${dni}/historial`).subscribe({
      next: (data) => {
        this.historialOrdenes.set(data);
        if (data.length > 0) {
          const primerOrden = data[0];
          this.pacienteHistorialCargado.set({
            dni: primerOrden.paciente.dni,
            nombre: primerOrden.paciente.nombre,
            apellido: primerOrden.paciente.apellido
          });
        } else {
          this.historialError.set('No se encontraron órdenes registradas para el paciente.');
        }
        this.historialCargando.set(false);
      },
      error: (err) => {
        console.error('Error al cargar historial:', err);
        this.historialError.set('Paciente no encontrado en el sistema.');
        this.historialCargando.set(false);
      }
    });
  }

  onBusquedaPacienteInput(valor: string) {
    this.busquedaPacienteHistorial.set(valor);
    clearTimeout(this.busquedaPacienteDebounce);
    if (valor.length < 2) {
      this.pacientesEncontrados.set([]);
      this.mostrarDropdownPacientes.set(false);
      return;
    }
    this.busquedaPacienteDebounce = setTimeout(() => {
      this.api.get<{ dni: string; nombre: string; apellido: string }[]>(
        `/ordenes/pacientes/buscar?q=${encodeURIComponent(valor)}`
      ).subscribe({
        next: (data) => {
          this.pacientesEncontrados.set(data);
          this.mostrarDropdownPacientes.set(data.length > 0);
        },
        error: () => {
          this.pacientesEncontrados.set([]);
          this.mostrarDropdownPacientes.set(false);
        }
      });
    }, 300);
  }

  seleccionarPacienteHistorial(paciente: { dni: string; nombre: string; apellido: string }) {
    this.busquedaPacienteHistorial.set(`${paciente.nombre} ${paciente.apellido} (${paciente.dni})`);
    this.mostrarDropdownPacientes.set(false);
    this.pacientesEncontrados.set([]);
    // Cargar historial del paciente seleccionado
    this.historialCargando.set(true);
    this.historialError.set(null);
    this.historialOrdenes.set([]);
    this.pacienteHistorialCargado.set(null);
    this.api.get<Orden[]>(`/ordenes/pacientes/${paciente.dni}/historial`).subscribe({
      next: (data) => {
        this.historialOrdenes.set(data);
        if (data.length > 0) {
          this.pacienteHistorialCargado.set(paciente);
        } else {
          this.historialError.set('No se encontraron órdenes registradas para este paciente.');
        }
        this.historialCargando.set(false);
      },
      error: (err) => {
        this.historialError.set('Error al cargar el historial del paciente.');
        this.historialCargando.set(false);
      }
    });
  }

  ocultarDropdownPacientesConRetraso() {
    setTimeout(() => {
      this.mostrarDropdownPacientes.set(false);
    }, 200);
  }

  limpiarBusquedaHistorial() {
    this.busquedaPacienteHistorial.set('');
    this.pacientesEncontrados.set([]);
    this.mostrarDropdownPacientes.set(false);
    this.historialOrdenes.set([]);
    this.pacienteHistorialCargado.set(null);
    this.historialError.set(null);
  }

  abrirCargaInventario(reactivo: Reactivo) {
    this.reactivoSeleccionadoReorden.set(reactivo);
    this.cantidadIngreso.set(100);
    this.loteIngreso.set('');
    this.vencimientoIngreso.set('');
  }

  registrarEntradaStock() {
    const reactivo = this.reactivoSeleccionadoReorden();
    if (!reactivo) return;

    const cantidad = this.cantidadIngreso();
    const lote = this.loteIngreso().trim();
    const vencimiento = this.vencimientoIngreso();

    if (!cantidad || cantidad <= 0) {
      alert('Ingresa una cantidad válida mayor a cero.');
      return;
    }
    if (!lote) {
      alert('Ingresa el código de lote.');
      return;
    }
    if (!vencimiento) {
      alert('Ingresa la fecha de vencimiento del lote.');
      return;
    }

    const payload = {
      reactivo_id: reactivo.id,
      codigo_lote: lote,
      cantidad_disponible: cantidad,
      fecha_vencimiento: vencimiento,
      descripcion: `Reabastecimiento lote ${lote}`
    };

    this.api.post('/inventario/lotes', payload).subscribe({
      next: () => {
        alert('Lote registrado y stock actualizado correctamente.');
        this.reactivoSeleccionadoReorden.set(null);
        if (this.reactivoExpandido() === reactivo.id) {
          this.cargarLotesReactivo(reactivo.id);
        }
        this.cargarDatosInventario();
      },
      error: (err) => alert('Error al registrar stock: ' + (err.error?.detail || err.message))
    });
  }

  generarInformePDF(orden: Orden) {
    this.api.getBlob(`/ordenes/informe/${orden.codigo_orden}/pdf`).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: () => alert('No se pudo descargar el informe PDF. Verifique que la orden esté firmada.')
    });
  }

  objectKeys(obj: any): string[] {
    return obj ? Object.keys(obj) : [];
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/']);
  }
}
