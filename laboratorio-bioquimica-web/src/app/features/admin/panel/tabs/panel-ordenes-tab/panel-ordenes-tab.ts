import {
  Component,
  ViewEncapsulation,
  inject,
  signal,
  computed,
  output,
  input,
  effect
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { BrandLogoComponent } from '../../../../../shared/components/brand-logo/brand-logo';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { Examen, Orden, ParametroExamen } from '../../panel.models';
import {
  labelMetodoPago,
  tituloPalabras,
  objectKeys
} from '../../panel.utils';
import { PanelNotifyService } from '../../panel-notify.service';
import { PanelCacheService } from '../../panel-cache.service';
import { normalizarTipoResultado, stepDecimales, esParametroResultadoVisible, examenFaltaCrearResultados } from '../../catalogo-examen.options';

type ExamenOrdenItem = {
  examenId: number;
  nombre: string;
  crearResultadoPendiente: boolean;
};

type CampoResultadoForm = {
  key: string;
  param: ParametroExamen;
  examenNombre: string;
  examenId: number;
};

@Component({
  selector: 'app-panel-ordenes-tab',
  standalone: true,
  imports: [CommonModule, FormsModule, BrandLogoComponent],
  templateUrl: './panel-ordenes-tab.html'
})
export class PanelOrdenesTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);
  private cache = inject(PanelCacheService);

  /** Emite cuando la firma de resultados descuenta stock (el padre puede refrescar inventario). */
  inventarioChanged = output<void>();
  volverLista = output<void>();

  /** Vista controlada por el menú lateral del panel. */
  vista = input<'lista' | 'nueva' | 'cobros_pendiente'>('lista');

  readonly moneda = MONEDA_CODIGO;
  readonly labelMetodoPago = labelMetodoPago;
  readonly objectKeys = objectKeys;
  readonly hoyIso = new Date().toISOString().slice(0, 10);
  readonly itemsPorPagina = 8;
  readonly whatsappLaboratorio = '59175548529';
  readonly portalResultadosUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/resultados`
    : 'http://localhost:4200/resultados';

  ordenes = signal<Orden[]>([]);
  examenesCatalogo = signal<Examen[]>([]);
  busquedaOrdenes = signal('');
  filtroOrdenesTab = signal<'todas' | 'proceso' | 'firmadas' | 'cobro_pendiente'>('todas');
  filtroFechaOrdenes = signal<'todas' | 'hoy' | 'semana' | 'mes'>('todas');
  paginaOrdenes = signal(1);
  ordenSortCampo = signal('fecha');
  ordenSortAsc = signal(false);
  ordenDetalle = signal<Orden | null>(null);
  mostrarDetalleOrden = signal(false);

  nuevoDni = signal('');
  nuevoNombre = signal('');
  nuevoApellido = signal('');
  nuevaFechaNac = signal('');
  nuevoGenero = signal('M');
  nuevoTelefono = signal('');
  nuevaDireccion = signal('');
  nuevoMedicoSolicitante = signal('');
  nuevaOrdenUrgente = signal(false);
  examenesSeleccionados = signal<number[]>([]);
  precioTotalAcumulado = signal(0);
  ordenCobradaEnRecepcion = signal(false);
  metodoPagoRecepcion = signal('EFECTIVO');
  metodoPagoRapido = signal('EFECTIVO');
  requiereFactura = signal(false);
  nitFactura = signal('');
  razonSocialFactura = signal('');
  busquedaExamen = signal('');
  mostrarDropdownExamenes = signal(false);

  mostrarTicketModal = signal(false);
  ticketOrden = signal<Orden | null>(null);

  ordenSeleccionadaResultados = signal<Orden | null>(null);
  firmandoResultados = signal(false);
  descargandoPdf = signal(false);
  valoresResultados = signal<Record<string, string>>({});
  referenciasResultados = signal<Record<string, string>>({});
  camposResultadoForm = signal<CampoResultadoForm[]>([]);

  mostrarWhatsappResultadoModal = signal(false);
  ordenFirmadaWhatsapp = signal<Orden | null>(null);
  detalleTab = signal<'orden' | 'resultados' | 'otros'>('orden');

  resumenOrdenes = computed(() => {
    const list = this.ordenes();
    return {
      total: list.length,
      proceso: list.filter(o => o.estado !== 'COMPLETADO').length,
      firmadas: list.filter(o => o.estado === 'COMPLETADO').length,
      cobroPendiente: list.filter(o => (o.estado_pago || 'PENDIENTE') !== 'PAGADO').length
    };
  });

  examenesFiltradosBusqueda = computed(() => {
    const query = this.busquedaExamen().toLowerCase().trim();
    const seleccionados = this.examenesSeleccionados();
    return this.examenesCatalogo().filter(ex => {
      const match = !query || ex.nombre.toLowerCase().includes(query)
        || (ex.descripcion && ex.descripcion.toLowerCase().includes(query));
      return match && !seleccionados.includes(ex.id);
    });
  });

  examenesSeleccionadosObjetos = computed(() => {
    const seleccionados = this.examenesSeleccionados();
    return this.examenesCatalogo().filter(ex => seleccionados.includes(ex.id));
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
      return ord.codigo_orden.toLowerCase().includes(q)
        || paciente.includes(q)
        || examenes.includes(q)
        || medico.includes(q);
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
        case 'fecha':
          cmp = new Date(a.fecha_creacion).getTime() - new Date(b.fecha_creacion).getTime();
          if (cmp === 0) cmp = a.codigo_orden.localeCompare(b.codigo_orden);
          break;
        case 'paciente':
          cmp = this.nombrePacienteDisplay(a).localeCompare(this.nombrePacienteDisplay(b), 'es', {
            sensitivity: 'base'
          });
          break;
        case 'total':
          cmp = a.precio_total - b.precio_total;
          break;
        case 'estado':
          cmp = a.estado.localeCompare(b.estado);
          break;
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

  private readonly sincronizarVista = effect(() => {
    const v = this.vista();
    if (v === 'cobros_pendiente') {
      this.filtroOrdenesTab.set('cobro_pendiente');
    } else if (v === 'lista') {
      this.filtroOrdenesTab.set('todas');
    }
    if (v !== 'nueva') {
      this.paginaOrdenes.set(1);
    }
  });

  /** Recarga la cola de órdenes (p. ej. al activar la pestaña desde el padre). */
  aplicarVista(_vista: 'lista' | 'nueva' | 'cobros_pendiente') {
    // La vista la controla el input `vista`; los filtros se sincronizan en el effect.
  }

  refresh() {
    this.ensureCatalogo();
    this.api.get<Orden[]>('/ordenes/').subscribe(data => this.ordenes.set(data));
  }

  ensureCatalogo(onLoaded?: (data: Examen[]) => void) {
    if (this.examenesCatalogo().length) {
      onLoaded?.(this.examenesCatalogo());
      return;
    }
    this.cache.examenesParaPanel().subscribe(data => {
      this.examenesCatalogo.set(data);
      onLoaded?.(data);
    });
  }

  cargarExamenesCatalogo(onLoaded?: (data: Examen[]) => void) {
    this.cache.examenesParaPanel(true).subscribe(data => {
      this.examenesCatalogo.set(data);
      onLoaded?.(data);
    });
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
    setTimeout(() => this.mostrarDropdownExamenes.set(false), 200);
  }

  calcularPrecioTotalAcumulado() {
    const seleccionados = this.examenesSeleccionados();
    let total = 0;
    seleccionados.forEach(id => {
      const examen = this.examenesCatalogo().find(ex => ex.id === id);
      if (examen) total += examen.precio_bob;
    });
    this.precioTotalAcumulado.set(total);
  }

  validarFechaNacimiento(fecha: string): boolean {
    if (!fecha) return false;
    const d = new Date(`${fecha}T12:00:00`);
    const hoy = new Date();
    hoy.setHours(23, 59, 59, 999);
    return !Number.isNaN(d.getTime()) && d.getFullYear() >= 1900 && d <= hoy;
  }

  crearNuevaOrden() {
    if (this.examenesSeleccionados().length === 0 || !this.nuevoDni() || !this.nuevoNombre() || !this.nuevoApellido()) {
      this.notify.mostrarToast('Por favor complete todos los datos requeridos y seleccione al menos una prueba.', 'error');
      return;
    }

    if (!this.validarFechaNacimiento(this.nuevaFechaNac())) {
      this.notify.mostrarToast('La fecha de nacimiento no es válida. Revise el año (entre 1900 y hoy).', 'error');
      return;
    }

    if (this.requiereFactura()) {
      const nit = this.nitFactura().trim();
      const razon = this.razonSocialFactura().trim();
      if (!nit || nit.replace(/\D/g, '').length < 5) {
        this.notify.mostrarToast('Ingrese un NIT válido para la factura (mín. 5 dígitos).', 'error');
        return;
      }
      if (!razon) {
        this.notify.mostrarToast('Ingrese la razón social o nombre para factura.', 'error');
        return;
      }
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
      prioridad: this.nuevaOrdenUrgente() ? 'URGENTE' : 'NORMAL',
      requiere_factura: this.requiereFactura(),
      nit_factura: this.requiereFactura() ? this.nitFactura().trim() : null,
      razon_social_factura: this.requiereFactura() ? this.razonSocialFactura().trim() : null,
    };

    this.api.post<Orden>('/ordenes/', payload).subscribe({
      next: (data) => {
        if (data.resultados) {
          data.resultados.forEach(res => {
            const ex = this.examenesCatalogo().find(e => e.id === res.examen_id);
            res.examen_nombre = ex ? ex.nombre : 'Prueba clínica';
          });
        }
        this.ticketOrden.set(data);
        this.mostrarTicketModal.set(true);
        this.limpiarFormularioOrden();
        this.refresh();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al crear orden')
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
    this.requiereFactura.set(false);
    this.nitFactura.set('');
    this.razonSocialFactura.set('');
    this.metodoPagoRecepcion.set('EFECTIVO');
  }

  nombrePacienteDisplay(ord: Orden): string {
    return `${tituloPalabras(ord.paciente.nombre)} ${tituloPalabras(ord.paciente.apellido)}`.trim();
  }

  examenesOrdenLista(ord: Orden): string[] {
    return this.examenesOrdenItems(ord).map(i => i.nombre);
  }

  examenesOrdenItems(ord: Orden): ExamenOrdenItem[] {
    if (!ord.resultados?.length) return [];
    return ord.resultados.map(res => {
      const examen = this.examenDeResultado(res);
      const parametros = examen?.parametros ?? res.examen?.parametros;
      return {
        examenId: res.examen_id,
        nombre: this.nombreExamenDeResultado(res),
        crearResultadoPendiente: examenFaltaCrearResultados(parametros)
      };
    });
  }

  faltaCrearResultadosExamenId(examenId: number): boolean {
    const examen = this.examenesCatalogo().find(e => e.id === examenId);
    return examenFaltaCrearResultados(examen?.parametros);
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
      // Primer clic: descendente (más reciente, mayor total, Z→A en paciente)
      this.ordenSortAsc.set(false);
    }
    this.paginaOrdenes.set(1);
  }

  sortIcon(campo: string): string {
    if (this.ordenSortCampo() !== campo) return '↕';
    // ↓ = más reciente / mayor primero · ↑ = más antiguo / menor primero
    return this.ordenSortAsc() ? '↑' : '↓';
  }

  sortTitle(campo: string): string {
    if (this.ordenSortCampo() !== campo) return 'Clic para ordenar';
    return this.ordenSortAsc()
      ? 'Ascendente (más antiguo primero). Clic para invertir.'
      : 'Descendente (más reciente primero). Clic para invertir.';
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
    return 'En prueba';
  }

  claseEstadoLab(estado: string): string {
    if (estado === 'COMPLETADO') return 'pill-success';
    if (estado === 'PROCESANDO') return 'pill-info';
    return 'pill-warning';
  }

  abrirDetalleOrden(ord: Orden) {
    this.ordenDetalle.set(ord);
    this.detalleTab.set('orden');
    this.mostrarDetalleOrden.set(true);
  }

  abrirDetalleEnResultados(ord: Orden) {
    this.ordenDetalle.set(ord);
    this.detalleTab.set('resultados');
    this.mostrarDetalleOrden.set(true);
  }

  cambiarDetalleTab(tab: 'orden' | 'resultados' | 'otros') {
    this.detalleTab.set(tab);
  }

  ordenCompletada(ord: Orden | null | undefined): boolean {
    return ord?.estado === 'COMPLETADO';
  }

  ordenTieneResultadosRellenados(ord: Orden | null | undefined): boolean {
    if (!ord) return false;
    if (ord.estado === 'PROCESANDO' || ord.estado === 'COMPLETADO') return true;
    return ord.resultados.some(res => {
      const valores = res.valor_resultado;
      if (!valores || Object.keys(valores).length === 0) return false;
      return Object.values(valores).some(v => v != null && String(v).trim() !== '');
    });
  }

  tituloModalResultados(ord: Orden): string {
    if (this.ordenCompletada(ord)) return 'Informe de resultados';
    if (this.ordenTieneResultadosRellenados(ord)) return 'Resultados de la prueba';
    return 'Rellenar resultado';
  }

  nombreExamenDeResultado(res: Orden['resultados'][number]): string {
    return (
      res.examen?.nombre
      || res.examen_nombre
      || this.examenesCatalogo().find(e => e.id === res.examen_id)?.nombre
      || 'Prueba'
    );
  }

  cerrarDetalleOrden() {
    this.mostrarDetalleOrden.set(false);
    this.ordenDetalle.set(null);
    this.detalleTab.set('orden');
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
          || 'Prueba clínica'
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
      error: (err) => this.notify.mostrarError(err, 'Error al cambiar prioridad')
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
      error: (err) => this.notify.mostrarError(err, 'Error al actualizar pago')
    });
  }

  abrirDialogoCargarResultados(orden: Orden) {
    const abrir = () => {
      this.ordenSeleccionadaResultados.set(orden);
      this.valoresResultados.set(this.construirCamposResultados(orden));
      this.referenciasResultados.set(this.construirReferenciasResultados(orden));
      this.camposResultadoForm.set(this.construirCamposResultadoForm(orden));
    };
    if (this.examenesCatalogo().length) {
      abrir();
      return;
    }
    this.cargarExamenesCatalogo(() => abrir());
  }

  construirCamposResultadoForm(orden: Orden): CampoResultadoForm[] {
    const campos: CampoResultadoForm[] = [];
    orden.resultados.forEach(res => {
      const examen = this.examenDeResultado(res);
      const examenNombre = examen?.nombre || res.examen?.nombre || `Prueba #${res.examen_id}`;
      this.parametrosDeExamen(examen, res).forEach(p => {
        campos.push({
          key: this.claveValorResultado(res.examen_id, p),
          param: p,
          examenNombre,
          examenId: res.examen_id
        });
      });
    });
    return campos;
  }

  tipoCampoResultado(param: ParametroExamen): string {
    return normalizarTipoResultado(param.tipo);
  }

  stepCampoNumerico(param: ParametroExamen): string {
    return stepDecimales(param.decimales);
  }

  parametroClave(p: ParametroExamen): string {
    return p.unidad ? `${p.nombre} (${p.unidad})` : p.nombre;
  }

  /** Clave interna del formulario: evita colisión cuando varios exámenes tienen el mismo nombre de campo. */
  claveValorResultado(examenId: number, p: ParametroExamen): string {
    return `${examenId}::${this.parametroClave(p)}`;
  }

  formatReferencia(p: ParametroExamen): string {
    if (p.valor_referencia?.trim()) return p.valor_referencia.trim();
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
      const examen = this.examenDeResultado(res);
      const params = this.parametrosDeExamen(examen, res);
      params.forEach(p => {
        const formKey = this.claveValorResultado(res.examen_id, p);
        const storageKey = this.parametroClave(p);
        if (res.valor_resultado) {
          valores[formKey] =
            res.valor_resultado[storageKey]
            ?? (p.llave ? res.valor_resultado[p.llave] : undefined)
            ?? res.valor_resultado[p.nombre]
            ?? p.valor_defecto
            ?? '';
        } else {
          valores[formKey] = p.valor_defecto ?? '';
        }
      });
    });
    return valores;
  }

  construirReferenciasResultados(orden: Orden): Record<string, string> {
    const refs: Record<string, string> = {};
    orden.resultados.forEach(res => {
      const examen = this.examenDeResultado(res);
      this.parametrosDeExamen(examen, res).forEach(p => {
        const ref = this.formatReferencia(p);
        if (ref) refs[this.claveValorResultado(res.examen_id, p)] = ref;
      });
    });
    return refs;
  }

  examenDeResultado(res: Orden['resultados'][number]): Examen | undefined {
    const desdeCatalogo = this.examenesCatalogo().find(e => e.id === res.examen_id);
    if (desdeCatalogo?.parametros?.length) {
      return desdeCatalogo;
    }
    if (res.examen?.parametros?.length) {
      return res.examen as Examen;
    }
    return desdeCatalogo ?? (res.examen as Examen | undefined);
  }

  parametrosDeExamen(
    examen: Examen | undefined,
    res: Orden['resultados'][number]
  ): ParametroExamen[] {
    const filtrar = (lista: ParametroExamen[]) =>
      [...lista]
        .filter(p => esParametroResultadoVisible(p.nombre))
        .sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0));

    if (examen?.parametros?.length) {
      return filtrar(examen.parametros);
    }
    const desdeOrden = res.examen?.parametros;
    if (desdeOrden?.length) {
      return filtrar(desdeOrden);
    }
    const nombre = examen?.nombre || res.examen?.nombre || `Prueba #${res.examen_id}`;
    return [{ nombre: `Resultado ${nombre}`, unidad: '', tipo: 'Texto' }];
  }

  buildPayloadResultados(orden: Orden) {
    return orden.resultados.map(res => {
      const examen = this.examenDeResultado(res);
      const valor: Record<string, string> = {};
      this.parametrosDeExamen(examen, res).forEach(p => {
        const formKey = this.claveValorResultado(res.examen_id, p);
        const storageKey = this.parametroClave(p);
        valor[storageKey] = this.valoresResultados()[formKey] ?? '';
      });
      return { examen_id: res.examen_id, valor_resultado: valor, pdf_url: null };
    });
  }

  gruposCamposResultado(): { examenNombre: string; examenId: number; campos: CampoResultadoForm[] }[] {
    const grupos = new Map<number, { examenNombre: string; examenId: number; campos: CampoResultadoForm[] }>();
    for (const campo of this.camposResultadoForm()) {
      let bloque = grupos.get(campo.examenId);
      if (!bloque) {
        bloque = { examenNombre: campo.examenNombre, examenId: campo.examenId, campos: [] };
        grupos.set(campo.examenId, bloque);
      }
      bloque.campos.push(campo);
    }
    return [...grupos.values()];
  }

  qrOrdenUrl(codigo: string | undefined | null): string {
    if (!codigo) return '';
    return `${this.api.apiBaseUrl}/ordenes/qr/${codigo}`;
  }

  guardarBorradorResultados() {
    const orden = this.ordenSeleccionadaResultados();
    if (!orden) return;

    this.api.post<Orden>(`/ordenes/${orden.id}/valores`, this.buildPayloadResultados(orden)).subscribe({
      next: (updated) => {
        this.actualizarOrdenEnLista(updated);
        this.notify.mostrarToast('Borrador de resultados guardado correctamente.', 'success');
        this.ordenSeleccionadaResultados.set(null);
      },
      error: (err) => this.notify.mostrarError(err, 'Error al guardar borrador')
    });
  }

  firmarYAprobarResultados() {
    const orden = this.ordenSeleccionadaResultados();
    if (!orden || this.firmandoResultados()) return;

    this.firmandoResultados.set(true);
    this.api.post<Orden>(`/ordenes/${orden.id}/aprobar`, {
      resultados: this.buildPayloadResultados(orden)
    }).subscribe({
      next: (updated) => {
        this.firmandoResultados.set(false);
        this.notify.mostrarToast('Resultados firmados e informe PDF generado correctamente.', 'success');
        this.ordenSeleccionadaResultados.set(null);
        this.ordenFirmadaWhatsapp.set(updated);
        this.mostrarWhatsappResultadoModal.set(true);
        this.actualizarOrdenEnLista(updated);
        this.inventarioChanged.emit();
      },
      error: (err) => {
        this.firmandoResultados.set(false);
        this.notify.mostrarError(err, 'Error al firmar');
      }
    });
  }

  reabrirResultadosParaEdicion(orden: Orden) {
    const firmada = this.ordenCompletada(orden);
    const mensaje = firmada
      ? '¿Anular la firma y volver a rellenar los resultados desde cero? Se borrarán los valores cargados y el informe PDF anterior quedará invalidado.'
      : '¿Vaciar los resultados cargados y volver a rellenar desde cero?';

    if (typeof window !== 'undefined' && !window.confirm(mensaje)) {
      return;
    }

    this.api.post<Orden>(`/ordenes/${orden.id}/reabrir-resultados`, {}).subscribe({
      next: (updated) => {
        this.actualizarOrdenEnLista(updated);
        this.ordenSeleccionadaResultados.set(null);
        this.notify.mostrarToast('Orden reiniciada. Use «Rellenar resultado» para cargar los datos de nuevo.', 'success');
      },
      error: (err) => this.notify.mostrarError(err, 'No se pudo reiniciar la orden')
    });
  }

  private actualizarOrdenEnLista(updated: Orden) {
    this.ordenes.update(list => list.map(o => (o.id === updated.id ? { ...o, ...updated } : o)));
    if (this.ordenDetalle()?.id === updated.id) {
      this.ordenDetalle.set({ ...this.ordenDetalle()!, ...updated });
    }
  }

  generarInformePDF(orden: Orden) {
    if (this.descargandoPdf()) return;
    this.descargandoPdf.set(true);
    this.api.getBlob(`/ordenes/informe/${orden.codigo_orden}/pdf`).subscribe({
      next: (blob) => {
        this.descargandoPdf.set(false);
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: (err) => {
        this.descargandoPdf.set(false);
        this.notify.mostrarError(err, 'No se pudo descargar el informe PDF');
      }
    });
  }

  descargarComprobantePDF(orden: Orden, $event?: Event) {
    $event?.stopPropagation();
    if (this.descargandoPdf()) return;
    this.descargandoPdf.set(true);
    this.api.getBlob(`/ordenes/comprobante/${orden.codigo_orden}/pdf`).subscribe({
      next: (blob) => {
        this.descargandoPdf.set(false);
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: (err) => {
        this.descargandoPdf.set(false);
        this.notify.mostrarError(err, 'No se pudo descargar el comprobante PDF');
      }
    });
  }

  normalizarTelefonoBolivia(telefono?: string | null): string | null {
    if (!telefono) return null;
    const digits = telefono.replace(/\D/g, '');
    if (digits.startsWith('591') && digits.length >= 11) return digits;
    if (digits.length === 8) return `591${digits}`;
    if (digits.length === 9 && digits.startsWith('7')) return `591${digits}`;
    return digits.length >= 8 ? digits : null;
  }

  mensajeWhatsappResultado(ord: Orden): string {
    const paciente = ord.paciente;
    return (
      `Hola ${paciente.nombre}, sus resultados en Genotipia están listos.\n` +
      `Orden: ${ord.codigo_orden}\n` +
      `Consulte en: ${this.portalResultadosUrl}?codigo=${ord.codigo_orden}\n` +
      `Use su CI y fecha de nacimiento para ver el informe.`
    );
  }

  urlWhatsappResultado(ord: Orden): string {
    const tel = this.normalizarTelefonoBolivia(ord.paciente.telefono) || this.whatsappLaboratorio;
    return `https://wa.me/${tel}?text=${encodeURIComponent(this.mensajeWhatsappResultado(ord))}`;
  }

  abrirWhatsappResultado(ord: Orden) {
    window.open(this.urlWhatsappResultado(ord), '_blank', 'noopener');
  }

  cerrarWhatsappResultadoModal() {
    this.mostrarWhatsappResultadoModal.set(false);
    this.ordenFirmadaWhatsapp.set(null);
  }
}
