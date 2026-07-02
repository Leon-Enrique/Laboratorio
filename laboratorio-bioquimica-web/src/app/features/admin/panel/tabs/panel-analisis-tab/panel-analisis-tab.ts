import { Component, ViewEncapsulation, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { Examen, Reactivo, ParametroExamen } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';
import {
  TIPOS_PRUEBA,
  GRUPOS_PRUEBA,
  MATERIALES_MUESTRA,
  ESTADOS_PRUEBA,
  TIPOS_RESULTADO,
  UNIDADES_MEDIDA,
  normalizarTipoResultado,
  stepDecimales,
  esParametroResultadoVisible,
  esCampoFijoResultado,
  CAMPOS_FIJOS_RESULTADO,
  examenFaltaCrearResultados,
  TipoResultado
} from '../../catalogo-examen.options';

type ParametroFormRow = {
  tipo: string;
  grupo: string;
  seccion: string;
  nombre: string;
  llave: string;
  valor_defecto: string;
  unidad: string;
  decimales: number;
  metodo_prueba: string;
  valor_referencia: string;
  valor_min: number | null;
  valor_max: number | null;
};

type PanelAnalisis = 'prueba' | 'insumos' | 'resultados';

@Component({
  selector: 'app-panel-analisis-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-analisis-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelAnalisisTabComponent implements OnInit {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  readonly tiposPrueba = TIPOS_PRUEBA;
  readonly gruposPrueba = GRUPOS_PRUEBA;
  readonly materialesMuestra = MATERIALES_MUESTRA;
  readonly estadosPrueba = ESTADOS_PRUEBA;
  readonly tiposResultado = TIPOS_RESULTADO;
  readonly unidadesMedida = UNIDADES_MEDIDA;
  readonly stepDecimales = stepDecimales;

  examenes = signal<Examen[]>([]);
  reactivos = signal<Reactivo[]>([]);
  busqueda = signal('');
  examenSeleccionadoId = signal<number | null>(null);
  panelAbierto = signal<PanelAnalisis | null>(null);

  mostrarRegistroRapido = signal(false);
  registroNombre = signal('');
  registroPrecio = signal<number>(0);

  examenTipo = signal('Laboratorio');
  examenGrupo = signal('');
  examenGrupoImpresion = signal('');
  examenNombre = signal('');
  examenDerivacion = signal('');
  examenMaterial = signal('');
  examenEstado = signal('Activo');
  examenCodigoAbrev = signal('');
  examenPrecioDerivacion = signal<number>(0);
  examenEtiqueta = signal('');
  examenDesc = signal('');
  examenPrep = signal('');
  examenPrecio = signal<number>(0);
  examenEntrega = signal<number>(24);
  recetaInsumos = signal<{ reactivo_id: number; cantidad_consumo: number }[]>([]);
  examenParametros = signal<ParametroFormRow[]>([]);
  camposFijosResultado = signal<ParametroFormRow[]>([]);

  readonly nombresCamposFijos = CAMPOS_FIJOS_RESULTADO;

  parametroFormModel: ParametroFormRow = this.parametroVacio();

  mostrarMiniAdicionar = signal(false);
  nuevoCampoNombre = '';

  ngOnInit() {
    this.cargarExamenes();
    this.cargarReactivos();
  }

  refresh() {
    this.cargarExamenes();
    this.cargarReactivos();
  }

  cargarExamenes(onLoaded?: (data: Examen[]) => void) {
    this.api.get<Examen[]>('/examenes/admin-lista').subscribe({
      next: data => {
        this.examenes.set(data);
        const id = this.examenSeleccionadoId();
        if (id && !data.some(e => e.id === id)) {
          this.examenSeleccionadoId.set(null);
          this.panelAbierto.set(null);
        }
        onLoaded?.(data);
      },
      error: err => this.notify.mostrarError(err, 'No se pudo cargar la lista de pruebas')
    });
  }

  cargarReactivos() {
    this.api.get<Reactivo[]>('/inventario/reactivos').subscribe(data => this.reactivos.set(data));
  }

  examenesFiltrados(): Examen[] {
    const q = this.busqueda().trim().toLowerCase();
    if (!q) return this.examenes();
    return this.examenes().filter(ex =>
      ex.nombre.toLowerCase().includes(q) ||
      (ex.grupo?.toLowerCase().includes(q) ?? false) ||
      (ex.codigo_abrev?.toLowerCase().includes(q) ?? false)
    );
  }

  examenSeleccionado(): Examen | null {
    const id = this.examenSeleccionadoId();
    if (!id) return null;
    return this.examenes().find(e => e.id === id) ?? null;
  }

  faltaCrearResultados(ex: Examen): boolean {
    return examenFaltaCrearResultados(ex.parametros);
  }

  seleccionarExamen(examen: Examen) {
    this.examenSeleccionadoId.set(examen.id);
    this.panelAbierto.set(null);
    this.cargarFormularioDesdeExamen(examen);
  }

  pedirEliminarExamen() {
    const examen = this.examenSeleccionado();
    if (!examen) return;

    this.notify.pedirConfirmacion(
      'Eliminar prueba',
      `¿Eliminar "${examen.nombre}"? Esta acción no se puede deshacer. Si la prueba ya tiene órdenes o resultados, no se podrá eliminar.`,
      () => this.eliminarExamen(examen.id)
    );
  }

  private eliminarExamen(examenId: number) {
    this.api.delete(`/examenes/${examenId}`).subscribe({
      next: () => {
        this.notify.mostrarToast('Prueba eliminada correctamente.', 'success');
        this.examenSeleccionadoId.set(null);
        this.panelAbierto.set(null);
        this.cargarExamenes();
      },
      error: (err) => this.notify.mostrarError(err, 'No se pudo eliminar la prueba')
    });
  }

  abrirPanel(panel: PanelAnalisis) {
    if (!this.examenSeleccionadoId()) {
      this.notify.mostrarToast('Selecciona una prueba de la lista.', 'error');
      return;
    }
    const abierto = this.panelAbierto() === panel ? null : panel;
    this.panelAbierto.set(abierto);
    if (abierto === 'resultados') {
      this.prepararPanelResultados();
    }
  }

  insumosResumen(): { nombre: string; unidad: string; cantidad: number }[] {
    return this.recetaInsumos()
      .filter(f => f.reactivo_id > 0)
      .map(f => {
        const r = this.reactivos().find(x => x.id === f.reactivo_id);
        return {
          nombre: r?.nombre ?? `Insumo #${f.reactivo_id}`,
          unidad: r?.unidad_medida ?? '',
          cantidad: f.cantidad_consumo
        };
      });
  }

  prepararPanelResultados() {
    this.parametroFormModel = this.parametroVacio();
    if (!this.camposFijosResultado().length) {
      this.camposFijosResultado.set(this.definicionCamposFijos());
    }
  }

  esCampoFijo(nombre: string): boolean {
    return esCampoFijoResultado(nombre);
  }

  private definicionCamposFijos(): ParametroFormRow[] {
    const defs: Array<{ nombre: string; tipo: string }> = [
      { nombre: 'Grupo', tipo: 'Texto' },
      { nombre: 'Método de prueba', tipo: 'Texto' },
      { nombre: 'Valor de referencia', tipo: 'Texto' },
      { nombre: 'Material de prueba', tipo: 'Texto' }
    ];
    return defs.map(d => ({
      ...this.parametroVacio(),
      nombre: d.nombre,
      tipo: d.tipo,
      llave: this.slugLlave(d.nombre)
    }));
  }

  private initCamposFijosDesdeCargados(cargados: ParametroFormRow[]): ParametroFormRow[] {
    const porNombre = new Map(
      cargados.filter(p => this.esCampoFijo(p.nombre)).map(p => [p.nombre.toLowerCase(), p])
    );
    return this.definicionCamposFijos().map(d => {
      const cargado = porNombre.get(d.nombre.toLowerCase());
      return cargado ? { ...cargado, tipo: d.tipo } : d;
    });
  }

  private separarParametrosCargados(parametros?: ParametroExamen[]) {
    const todos = this.parametrosDesdeExamen(parametros).filter(p =>
      esParametroResultadoVisible(p.nombre)
    );
    this.camposFijosResultado.set(this.initCamposFijosDesdeCargados(todos));
    this.examenParametros.set(todos.filter(p => !this.esCampoFijo(p.nombre)));
  }

  todosParametrosResultado(): ParametroFormRow[] {
    return [...this.camposFijosResultado(), ...this.examenParametros()];
  }

  toggleRegistroRapido() {
    this.mostrarRegistroRapido.update(v => !v);
    if (this.mostrarRegistroRapido()) {
      this.registroNombre.set('');
      this.registroPrecio.set(0);
    }
  }

  registrarAnalisis() {
    if (!this.registroNombre().trim() || this.registroPrecio() <= 0) {
      this.notify.mostrarToast('Ingresa el nombre y un precio válido.', 'error');
      return;
    }

    const payload = {
      nombre: this.registroNombre().trim(),
      precio_bob: this.registroPrecio(),
      tiempo_entrega_horas: 24,
      visible: false,
      destacado: false,
      tipo: 'Laboratorio',
      estado: 'Activo',
      formulas: [],
      parametros: []
    };

    this.api.post<Examen>('/examenes/', payload).subscribe({
      next: (creado) => {
        this.notify.mostrarToast(
          `"${creado.nombre}" registrada. Actívala en Catálogo de pruebas para publicarla en la web.`,
          'success'
        );
        this.mostrarRegistroRapido.set(false);
        this.cargarExamenes();
        this.examenSeleccionadoId.set(creado.id);
        this.cargarFormularioDesdeExamen(creado);
        this.panelAbierto.set('prueba');
      },
      error: (err) => this.notify.mostrarError(err, 'Error al registrar prueba')
    });
  }

  guardarAnalisis() {
    const examen = this.examenSeleccionado();
    if (!examen) return;
    if (!this.examenNombre().trim() || this.examenPrecio() <= 0) {
      this.notify.mostrarToast('El nombre y precio de venta son obligatorios.', 'error');
      return;
    }

    if (this.panelAbierto() === 'resultados' && !this.examenParametros().length) {
      this.notify.mostrarToast('Agrega al menos un campo analítico con Adicionar.', 'error');
      return;
    }

    const payload = this.buildPayloadCompleto(examen.visible, examen.destacado ?? false);
    const examenId = examen.id;
    this.api.put(`/examenes/${examen.id}`, payload).subscribe({
      next: () => {
        this.notify.mostrarToast('Cambios guardados correctamente.', 'success');
        this.panelAbierto.set(null);
        this.cargarExamenes(data => {
          const actualizado = data.find(e => e.id === examenId);
          if (actualizado) this.cargarFormularioDesdeExamen(actualizado);
        });
      },
      error: (err) => this.notify.mostrarError(err, 'Error al guardar')
    });
  }

  private buildPayloadCompleto(visible: boolean, destacado: boolean) {
    return {
      nombre: this.examenNombre().trim(),
      descripcion: this.examenDesc(),
      preparacion: this.examenPrep(),
      precio_bob: this.examenPrecio(),
      tiempo_entrega_horas: this.examenEntrega(),
      visible,
      destacado,
      tipo: this.examenTipo(),
      grupo: this.examenGrupo() || null,
      grupo_impresion: this.examenGrupoImpresion() || null,
      derivacion: this.examenDerivacion() || null,
      material_muestra: this.examenMaterial() || null,
      estado: this.examenEstado(),
      codigo_abrev: this.examenCodigoAbrev() || null,
      precio_derivacion: this.examenPrecioDerivacion(),
      etiqueta: this.examenEtiqueta() || null,
      formulas: this.recetaInsumos().filter(f => f.reactivo_id > 0),
      parametros: this.buildParametrosPayload(this.todosParametrosResultado())
    };
  }

  private cargarFormularioDesdeExamen(examen: Examen) {
    this.examenTipo.set(examen.tipo || 'Laboratorio');
    this.examenGrupo.set(examen.grupo || '');
    this.examenGrupoImpresion.set(examen.grupo_impresion || '');
    this.examenNombre.set(examen.nombre);
    this.examenDerivacion.set(examen.derivacion || '');
    this.examenMaterial.set(examen.material_muestra || '');
    this.examenEstado.set(examen.estado || 'Activo');
    this.examenCodigoAbrev.set(examen.codigo_abrev || '');
    this.examenPrecioDerivacion.set(examen.precio_derivacion ?? 0);
    this.examenEtiqueta.set(examen.etiqueta || '');
    this.examenDesc.set(examen.descripcion || '');
    this.examenPrep.set(examen.preparacion || '');
    this.examenPrecio.set(examen.precio_bob);
    this.examenEntrega.set(examen.tiempo_entrega_horas);
    this.recetaInsumos.set((examen.formulas || []).map(f => ({
      reactivo_id: f.reactivo_id,
      cantidad_consumo: f.cantidad_consumo
    })));
    this.separarParametrosCargados(examen.parametros);
    if (this.panelAbierto() === 'resultados' && !this.camposFijosResultado().length) {
      this.camposFijosResultado.set(this.definicionCamposFijos());
    }
  }

  private parametroVacio(): ParametroFormRow {
    return {
      tipo: 'Texto',
      grupo: '',
      seccion: '',
      nombre: '',
      llave: '',
      valor_defecto: '',
      unidad: '',
      decimales: 0,
      metodo_prueba: '',
      valor_referencia: '',
      valor_min: null,
      valor_max: null
    };
  }

  private slugLlave(nombre: string): string {
    return nombre
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_|_$/g, '');
  }

  private parametrosDesdeExamen(parametros?: ParametroExamen[]): ParametroFormRow[] {
    if (!parametros?.length) return [];
    return [...parametros]
      .sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0))
      .map(p => ({
        tipo: p.tipo || 'Texto',
        grupo: p.grupo ?? '',
        seccion: p.seccion ?? '',
        nombre: p.nombre,
        llave: p.llave ?? '',
        valor_defecto: p.valor_defecto ?? '',
        unidad: p.unidad ?? '',
        decimales: p.decimales ?? 2,
        metodo_prueba: p.metodo_prueba ?? '',
        valor_referencia: p.valor_referencia ?? '',
        valor_min: p.valor_min ?? null,
        valor_max: p.valor_max ?? null
      }));
  }

  private buildParametrosPayload(rows: ParametroFormRow[]) {
    return rows
      .filter(p => p.nombre.trim() && esParametroResultadoVisible(p.nombre))
      .filter(p => {
        if (!this.esCampoFijo(p.nombre)) return true;
        return Boolean(p.valor_referencia.trim() || p.valor_defecto.trim());
      })
      .map((p, i) => ({
        nombre: p.nombre.trim(),
        tipo: p.tipo || 'Texto',
        grupo: p.grupo.trim() || null,
        seccion: p.seccion.trim() || null,
        llave: (p.llave.trim() || this.slugLlave(p.nombre)) || null,
        valor_defecto: p.valor_defecto.trim() || null,
        unidad: p.unidad.trim() || null,
        decimales: p.decimales ?? 2,
        metodo_prueba: p.metodo_prueba.trim() || null,
        valor_referencia: p.valor_referencia.trim() || null,
        valor_min: p.valor_min,
        valor_max: p.valor_max,
        orden: i
      }));
  }

  abrirMiniAdicionar() {
    this.nuevoCampoNombre = '';
    this.mostrarMiniAdicionar.set(true);
  }

  cerrarMiniAdicionar() {
    this.mostrarMiniAdicionar.set(false);
    this.nuevoCampoNombre = '';
  }

  aceptarNuevoCampoNombre() {
    const nombre = this.nuevoCampoNombre.trim();
    if (!nombre) {
      this.notify.mostrarToast('Escribe el nombre del nuevo campo.', 'error');
      return;
    }
    if (this.esCampoFijo(nombre)) {
      this.notify.mostrarToast(`"${nombre}" ya forma parte del formulario base.`, 'error');
      return;
    }
    if (this.examenParametros().some(p => p.nombre.toLowerCase() === nombre.toLowerCase())) {
      this.notify.mostrarToast('Ya existe un campo con ese nombre.', 'error');
      return;
    }
    const modelo = this.parametroFormModel;
    const fila: ParametroFormRow = {
      ...this.parametroVacio(),
      tipo: modelo.tipo,
      grupo: modelo.grupo,
      seccion: modelo.seccion,
      nombre,
      llave: this.slugLlave(nombre),
      valor_defecto: modelo.valor_defecto,
      unidad: modelo.unidad,
      decimales: modelo.decimales,
      metodo_prueba: modelo.metodo_prueba,
      valor_referencia: modelo.valor_referencia,
      valor_min: modelo.valor_min,
      valor_max: modelo.valor_max
    };
    this.examenParametros.set([...this.examenParametros(), fila]);
    this.parametroFormModel = this.parametroVacio();
    this.cerrarMiniAdicionar();
  }

  eliminarParametroResultado(index: number) {
    const lista = [...this.examenParametros()];
    lista.splice(index, 1);
    this.examenParametros.set(lista);
  }

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

  tipoResultadoForm(): TipoResultado {
    return normalizarTipoResultado(this.parametroFormModel.tipo);
  }

  tipoParametro(p: ParametroFormRow): TipoResultado {
    return normalizarTipoResultado(p.tipo);
  }

  stepValorDefecto(): string {
    return stepDecimales(this.parametroFormModel.decimales);
  }

  onCambioTipoResultado() {
    this.parametroFormModel.valor_defecto = '';
    this.parametroFormModel.valor_referencia = '';
  }
}
