import { Component, ViewEncapsulation, inject, signal, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { Proveedor } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';

@Component({
  selector: 'app-panel-proveedores-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-proveedores-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelProveedoresTabComponent implements OnInit {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  @Input() rolUsuario = '';

  proveedores = signal<Proveedor[]>([]);
  cargando = signal(false);

  mostrarModal = signal(false);
  editando = signal<Proveedor | null>(null);
  formNombre = signal('');
  formTelefono = signal('');
  formEmail = signal('');
  formDireccion = signal('');

  ngOnInit() {
    this.cargarProveedores();
  }

  cargarProveedores() {
    this.cargando.set(true);
    this.api.get<Proveedor[]>('/inventario/proveedores').subscribe({
      next: (data) => {
        this.proveedores.set(data);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }

  abrirNuevo() {
    this.editando.set(null);
    this.formNombre.set('');
    this.formTelefono.set('');
    this.formEmail.set('');
    this.formDireccion.set('');
    this.mostrarModal.set(true);
  }

  abrirEditar(prov: Proveedor) {
    this.editando.set(prov);
    this.formNombre.set(prov.nombre);
    this.formTelefono.set(prov.telefono || '');
    this.formEmail.set(prov.email || '');
    this.formDireccion.set(prov.direccion || '');
    this.mostrarModal.set(true);
  }

  cerrarModal() {
    this.mostrarModal.set(false);
    this.editando.set(null);
  }

  guardar() {
    const nombre = this.formNombre().trim();
    if (!nombre) {
      this.notify.mostrarToast('Ingrese el nombre del proveedor.', 'error');
      return;
    }

    const payload = {
      nombre,
      telefono: this.formTelefono().trim() || null,
      email: this.formEmail().trim() || null,
      direccion: this.formDireccion().trim() || null
    };

    const edit = this.editando();
    const req = edit
      ? this.api.patch<Proveedor>(`/inventario/proveedores/${edit.id}`, payload)
      : this.api.post<Proveedor>('/inventario/proveedores', payload);

    req.subscribe({
      next: () => {
        this.notify.mostrarToast(edit ? 'Proveedor actualizado.' : 'Proveedor registrado.', 'success');
        this.cerrarModal();
        this.cargarProveedores();
      },
      error: (err) => this.notify.mostrarError(err, 'Error al guardar proveedor')
    });
  }
}
