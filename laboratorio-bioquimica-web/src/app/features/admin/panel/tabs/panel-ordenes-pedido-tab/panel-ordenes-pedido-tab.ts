import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { OrdenPedido, Reactivo, Proveedor } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';
import { PanelCacheService } from '../../panel-cache.service';

@Component({
  selector: 'app-panel-ordenes-pedido-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-ordenes-pedido-tab.html'
})
export class PanelOrdenesPedidoTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);
  private cache = inject(PanelCacheService);

  readonly labNombre = "Laboratorio Genotipia";
  readonly whatsappLaboratorio = '59175548529';

  ordenes = signal<OrdenPedido[]>([]);
  reactivos = signal<Reactivo[]>([]);
  proveedores = signal<Proveedor[]>([]);
  cargando = signal(false);

  mostrarWhatsappModal = signal(false);
  ordenWhatsapp = signal<OrdenPedido | null>(null);

  cargarDatos() {
    this.cargando.set(true);
    this.api.get<OrdenPedido[]>('/inventario/ordenes-pedido').subscribe({
      next: (data) => {
        this.ordenes.set(data);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
    this.api.get<Reactivo[]>('/inventario/reactivos').subscribe(data => this.reactivos.set(data));
    this.cache.proveedoresLista().subscribe(data => this.proveedores.set(data));
  }

  iniciarEnvio(orden: OrdenPedido) {
    this.ordenWhatsapp.set(orden);
    this.mostrarWhatsappModal.set(true);
  }

  cerrarWhatsappModal() {
    this.mostrarWhatsappModal.set(false);
    this.ordenWhatsapp.set(null);
  }

  normalizarTelefonoBolivia(telefono?: string | null): string | null {
    if (!telefono) return null;
    const digits = telefono.replace(/\D/g, '');
    if (digits.startsWith('591') && digits.length >= 11) return digits;
    if (digits.length === 8) return `591${digits}`;
    if (digits.length === 9 && digits.startsWith('7')) return `591${digits}`;
    return digits.length >= 8 ? digits : null;
  }

  mensajeWhatsappPedido(orden: OrdenPedido): string {
    const reactivo = this.reactivos().find(r => r.id === orden.reactivo_id);
    const unidad = reactivo?.unidad_medida || 'unidades';
    let msg =
      `Hola${orden.proveedor_nombre ? ` ${orden.proveedor_nombre}` : ''}, ` +
      `solicitamos pedido desde ${this.labNombre}.\n\n` +
      `Insumo: ${orden.reactivo_nombre || reactivo?.nombre || '—'}\n` +
      `Cantidad: ${orden.cantidad_pedida} ${unidad}\n`;
    if (orden.fecha_esperada) {
      const fecha = new Date(orden.fecha_esperada + 'T12:00:00');
      msg += `Fecha esperada: ${fecha.toLocaleDateString('es-BO')}\n`;
    }
    if (orden.notas) {
      msg += `Notas: ${orden.notas}\n`;
    }
    msg += `\nGracias.`;
    return msg;
  }

  telefonoDestino(orden: OrdenPedido): string | null {
    const telOrden = this.normalizarTelefonoBolivia(orden.proveedor_telefono);
    if (telOrden) return telOrden;
    if (orden.proveedor_id) {
      const prov = this.proveedores().find(p => p.id === orden.proveedor_id);
      return this.normalizarTelefonoBolivia(prov?.telefono);
    }
    return null;
  }

  urlWhatsappPedido(orden: OrdenPedido): string {
    const tel = this.telefonoDestino(orden) || this.whatsappLaboratorio;
    return `https://wa.me/${tel}?text=${encodeURIComponent(this.mensajeWhatsappPedido(orden))}`;
  }

  confirmarEnvioWhatsapp(orden: OrdenPedido) {
    if (!this.telefonoDestino(orden)) {
      this.notify.mostrarToast(
        'Este proveedor no tiene teléfono. Configure el número en Catálogo de Proveedores.',
        'error'
      );
      return;
    }
    window.open(this.urlWhatsappPedido(orden), '_blank', 'noopener');
    this.api.patch<OrdenPedido>(`/inventario/ordenes-pedido/${orden.id}`, { estado: 'ENVIADA' }).subscribe({
      next: (updated) => {
        this.ordenes.update(list => list.map(o => (o.id === updated.id ? updated : o)));
        this.notify.mostrarToast('Pedido marcado como enviado.', 'success');
        this.cerrarWhatsappModal();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al actualizar pedido')
    });
  }

  cambiarEstado(orden: OrdenPedido, estado: string) {
    this.api.patch<OrdenPedido>(`/inventario/ordenes-pedido/${orden.id}`, { estado }).subscribe({
      next: (updated) => {
        this.ordenes.update(list => list.map(o => (o.id === updated.id ? updated : o)));
        this.notify.mostrarToast('Estado del pedido actualizado.', 'success');
      },
      error: (err) => this.notify.mostrarError(err, 'Error al actualizar pedido')
    });
  }

  claseEstadoPedido(estado: string): string {
    if (estado === 'RECIBIDA') return 'pill-success';
    if (estado === 'ENVIADA') return 'pill-info';
    if (estado === 'CANCELADA') return 'pill-danger';
    return 'pill-warning';
  }
}
