import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { Orden } from '../../panel.models';
import { objectKeys } from '../../panel.utils';
import { PanelNotifyService } from '../../panel-notify.service';

@Component({
  selector: 'app-panel-historial-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './panel-historial-tab.html'
})
export class PanelHistorialTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  readonly moneda = MONEDA_CODIGO;
  readonly objectKeys = objectKeys;

  busquedaPacienteHistorial = signal('');
  pacientesEncontrados = signal<{ dni: string; nombre: string; apellido: string }[]>([]);
  mostrarDropdownPacientes = signal(false);
  historialOrdenes = signal<Orden[]>([]);
  pacienteHistorialCargado = signal<{ dni: string; nombre: string; apellido: string } | null>(null);
  historialError = signal<string | null>(null);
  historialCargando = signal(false);

  private busquedaPacienteDebounce: ReturnType<typeof setTimeout> | null = null;

  onBusquedaPacienteInput(valor: string) {
    this.busquedaPacienteHistorial.set(valor);
    if (this.busquedaPacienteDebounce) clearTimeout(this.busquedaPacienteDebounce);
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
    this.cargarHistorial(paciente.dni, paciente);
  }

  private cargarHistorial(dni: string, paciente?: { dni: string; nombre: string; apellido: string }) {
    this.historialCargando.set(true);
    this.historialError.set(null);
    this.historialOrdenes.set([]);
    this.pacienteHistorialCargado.set(null);

    this.api.get<Orden[]>(`/ordenes/pacientes/${dni}/historial`).subscribe({
      next: (data) => {
        this.historialOrdenes.set(data);
        if (data.length > 0) {
          this.pacienteHistorialCargado.set(paciente ?? {
            dni: data[0].paciente.dni,
            nombre: data[0].paciente.nombre,
            apellido: data[0].paciente.apellido
          });
        } else {
          this.historialError.set('No se encontraron órdenes registradas para este paciente.');
        }
        this.historialCargando.set(false);
      },
      error: () => {
        this.historialError.set('Error al cargar el historial del paciente.');
        this.historialCargando.set(false);
      }
    });
  }

  ocultarDropdownPacientesConRetraso() {
    setTimeout(() => this.mostrarDropdownPacientes.set(false), 200);
  }

  limpiarBusquedaHistorial() {
    this.busquedaPacienteHistorial.set('');
    this.pacientesEncontrados.set([]);
    this.mostrarDropdownPacientes.set(false);
    this.historialOrdenes.set([]);
    this.pacienteHistorialCargado.set(null);
    this.historialError.set(null);
  }

  nombreExamen(res: Orden['resultados'][number]): string {
    return res.examen?.nombre || res.examen_nombre || `Análisis #${res.examen_id}`;
  }

  generarInformePDF(orden: Orden) {
    this.api.getBlob(`/ordenes/informe/${orden.codigo_orden}/pdf`).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: () => this.notify.mostrarToast('No se pudo descargar el informe PDF. Verifique que la orden esté firmada.', 'error')
    });
  }
}
