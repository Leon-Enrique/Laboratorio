import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { ComprobanteResumen } from '../../panel.models';
import { labelMetodoPago } from '../../panel.utils';
import { PanelNotifyService } from '../../panel-notify.service';

@Component({
  selector: 'app-panel-facturas-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-facturas-tab.html'
})
export class PanelFacturasTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  readonly moneda = MONEDA_CODIGO;
  readonly labelMetodoPago = labelMetodoPago;

  comprobantes = signal<ComprobanteResumen[]>([]);
  cargando = signal(false);
  busqueda = signal('');
  filtroPago = signal<'TODOS' | 'PAGADO' | 'PENDIENTE'>('TODOS');
  soloFactura = signal(false);

  private busquedaDebounce: ReturnType<typeof setTimeout> | null = null;

  cargarComprobantes() {
    this.cargando.set(true);
    const params = new URLSearchParams();
    const q = this.busqueda().trim();
    if (q) params.set('q', q);
    if (this.filtroPago() !== 'TODOS') params.set('estado_pago', this.filtroPago());
    if (this.soloFactura()) params.set('solo_factura', 'true');

    const qs = params.toString();
    this.api.get<ComprobanteResumen[]>(`/ordenes/comprobantes${qs ? `?${qs}` : ''}`).subscribe({
      next: (data) => {
        this.comprobantes.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.cargando.set(false);
        this.notify.mostrarError(err, 'No se pudo cargar el historial de comprobantes');
      }
    });
  }

  onBusquedaInput(valor: string) {
    this.busqueda.set(valor);
    if (this.busquedaDebounce) clearTimeout(this.busquedaDebounce);
    this.busquedaDebounce = setTimeout(() => this.cargarComprobantes(), 350);
  }

  onFiltroChange() {
    this.cargarComprobantes();
  }

  descargarPdf(item: ComprobanteResumen) {
    this.api.getBlob(`/ordenes/comprobante/${item.codigo_orden}/pdf`).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: (err) => this.notify.mostrarError(err, 'No se pudo descargar el comprobante PDF')
    });
  }

  tituloComprobante(item: ComprobanteResumen): string {
    const num = item.numero_comprobante ?? item.id;
    return item.requiere_factura ? `Factura Nº ${num}` : `Orden Nº ${num}`;
  }
}
