import { Component, inject, signal, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { SugerenciaCompra, Proveedor } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';
import { PanelCacheService } from '../../panel-cache.service';

@Component({
  selector: 'app-panel-sugerencias-compra-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-sugerencias-compra-tab.html'
})
export class PanelSugerenciasCompraTabComponent implements OnChanges {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);
  private cache = inject(PanelCacheService);

  @Input() rolUsuario = '';
  @Input() filtroReactivoId: number | null = null;
  @Output() limpiarFiltro = new EventEmitter<void>();

  sugerencias = signal<SugerenciaCompra[]>([]);
  proveedores = signal<Proveedor[]>([]);
  cargando = signal(false);

  reactivoEditando = signal<number | null>(null);
  editLeadTime = signal(7);
  editStockSeguridad = signal(0);
  editStockMinimo = signal(10);

  ngOnChanges(changes: SimpleChanges) {
    if (changes['filtroReactivoId'] && !changes['filtroReactivoId'].firstChange) {
      this.cargarSugerencias();
    }
  }

  cargarProveedores() {
    this.cache.proveedoresLista().subscribe(data => this.proveedores.set(data));
  }

  cargarSugerencias() {
    this.cargarProveedores();
    this.cargando.set(true);
    const params = this.filtroReactivoId ? `?reactivo_id=${this.filtroReactivoId}` : '';
    this.api.get<SugerenciaCompra[]>(`/inventario/sugerencias-compra${params}`).subscribe({
      next: (data) => {
        this.sugerencias.set(data);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }

  onLimpiarFiltro() {
    this.limpiarFiltro.emit();
  }

  abrirEditarMrp(s: SugerenciaCompra) {
    this.reactivoEditando.set(s.reactivo_id);
    this.editLeadTime.set(s.tiempo_entrega_proveedor_dias);
    this.editStockSeguridad.set(s.stock_de_seguridad ?? 0);
    this.editStockMinimo.set(s.stock_minimo ?? 10);
  }

  guardarMrp(reactivoId: number) {
    this.api.patch(`/inventario/reactivos/${reactivoId}`, {
      tiempo_entrega_proveedor_dias: this.editLeadTime(),
      stock_de_seguridad: this.editStockSeguridad(),
      stock_minimo: this.editStockMinimo()
    }).subscribe({
      next: () => {
        this.notify.mostrarToast('Parámetros MRP actualizados.', 'success');
        this.reactivoEditando.set(null);
        this.cargarSugerencias();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al guardar parámetros MRP')
    });
  }

  crearPedido(s: SugerenciaCompra) {
    this.api.post('/inventario/ordenes-pedido', {
      reactivo_id: s.reactivo_id,
      cantidad_pedida: s.cantidad_sugerida,
      proveedor_id: s.proveedor_id,
      notas: `Pedido sugerido MRP — punto reorden ${s.punto_reorden}`
    }).subscribe({
      next: () => this.notify.mostrarToast(`Pedido registrado para ${s.nombre}.`, 'success'),
      error: (err) => this.notify.mostrarError(err, 'Error al crear pedido')
    });
  }
}
