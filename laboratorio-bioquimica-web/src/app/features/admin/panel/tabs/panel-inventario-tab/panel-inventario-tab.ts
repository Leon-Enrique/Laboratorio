import { Component, ViewEncapsulation, inject, signal, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import {
  Reactivo,
  Lote,
  MovimientoInventario,
  AuditoriaInventario,
  Proveedor
} from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';

@Component({
  selector: 'app-panel-inventario-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-inventario-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelInventarioTabComponent implements OnInit {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  @Input() rolUsuario = '';

  reactivos = signal<Reactivo[]>([]);
  alertasInventario = signal<{ id: number; nombre: string; stock_actual: number; stock_minimo: number; unidad_medida: string; lotes_afectados?: number; alertas: string[] }[]>([]);
  proveedores = signal<Proveedor[]>([]);

  mostrarNuevoReactivoModal = signal<boolean>(false);
  nuevoReactivoNombre = signal<string>('');
  nuevoReactivoMin = signal<number>(10);
  nuevoReactivoUnidad = signal<string>('unidades');
  nuevoReactivoStockInicial = signal<number>(0);
  nuevoReactivoLote = signal<string>('');
  nuevoReactivoVencimiento = signal<string>('');
  nuevoReactivoProveedorId = signal<number | null>(null);

  reactivoSeleccionadoReorden = signal<Reactivo | null>(null);
  cantidadIngreso = signal<number>(100);
  loteIngreso = signal<string>('');
  vencimientoIngreso = signal<string>('');

  reactivoExpandido = signal<number | null>(null);
  lotesPorReactivo = signal<Record<number, Lote[]>>({});
  lotesCargando = signal<number | null>(null);
  mostrarHistorialInventario = signal<boolean>(false);
  movimientosInventario = signal<MovimientoInventario[]>([]);
  filtroMovimientoReactivo = signal<number | null>(null);
  auditoriaInventario = signal<AuditoriaInventario | null>(null);
  mostrarAuditoriaInventario = signal<boolean>(false);

  mostrarBajaLoteModal = signal(false);
  loteBajaTarget = signal<{ lote: Lote; reactivoId: number } | null>(null);
  motivoBajaLote = signal('Retiro por vencimiento');

  ngOnInit() {
    this.cargarDatosInventario();
    this.cargarProveedores();
  }

  cargarDatosInventario() {
    this.api.get<Reactivo[]>('/inventario/reactivos').subscribe(data => this.reactivos.set(data));
    this.api.get<{ id: number; nombre: string; stock_actual: number; stock_minimo: number; unidad_medida: string; lotes_afectados?: number; alertas: string[] }[]>('/inventario/alertas').subscribe(data => this.alertasInventario.set(data));
    if (this.mostrarAuditoriaInventario()) {
      this.cargarAuditoriaInventario();
    }
  }

  cargarProveedores() {
    this.api.get<Proveedor[]>('/inventario/proveedores').subscribe(data => this.proveedores.set(data));
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

  abrirModalBajaLote(lote: Lote, reactivoId: number) {
    this.loteBajaTarget.set({ lote, reactivoId });
    this.motivoBajaLote.set('Retiro por vencimiento');
    this.mostrarBajaLoteModal.set(true);
  }

  confirmarBajaLote() {
    const target = this.loteBajaTarget();
    if (!target) return;
    const motivo = this.motivoBajaLote().trim();
    if (!motivo) {
      this.notify.mostrarToast('Indique el motivo de baja del lote.', 'error');
      return;
    }
    this.api.post(`/inventario/lotes/${target.lote.id}/baja`, { motivo }).subscribe({
      next: () => {
        this.mostrarBajaLoteModal.set(false);
        this.loteBajaTarget.set(null);
        this.notify.mostrarToast('Lote dado de baja correctamente.', 'success');
        this.cargarLotesReactivo(target.reactivoId);
        this.cargarDatosInventario();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al dar de baja el lote')
    });
  }

  darBajaLote(lote: Lote, reactivoId: number) {
    this.abrirModalBajaLote(lote, reactivoId);
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

  crearNuevoReactivo() {
    if (!this.nuevoReactivoNombre() || !this.nuevoReactivoUnidad()) {
      this.notify.mostrarToast('Por favor ingrese el nombre del reactivo y la unidad de medida.', 'error');
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
        this.notify.mostrarToast('Reactivo registrado con éxito en la bodega del laboratorio.', 'success');
        this.mostrarNuevoReactivoModal.set(false);
        this.limpiarFormularioReactivo();
        this.cargarDatosInventario();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al registrar reactivo')
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
      this.notify.mostrarToast('Ingresa una cantidad válida mayor a cero.', 'error');
      return;
    }
    if (!lote) {
      this.notify.mostrarToast('Ingresa el código de lote.', 'error');
      return;
    }
    if (!vencimiento) {
      this.notify.mostrarToast('Ingresa la fecha de vencimiento del lote.', 'error');
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
        this.notify.mostrarToast('Lote registrado y stock actualizado correctamente.', 'success');
        this.reactivoSeleccionadoReorden.set(null);
        if (this.reactivoExpandido() === reactivo.id) {
          this.cargarLotesReactivo(reactivo.id);
        }
        this.cargarDatosInventario();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al registrar stock')
    });
  }
}
