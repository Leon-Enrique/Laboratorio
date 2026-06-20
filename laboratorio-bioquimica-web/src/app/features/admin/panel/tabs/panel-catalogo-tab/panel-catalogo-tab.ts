import { Component, ViewEncapsulation, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { Examen } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';

@Component({
  selector: 'app-panel-catalogo-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-catalogo-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelCatalogoTabComponent implements OnInit {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);

  readonly moneda = MONEDA_CODIGO;
  readonly maxDestacados = 6;

  examenesCatalogo = signal<Examen[]>([]);
  busquedaCatalogo = signal('');

  ngOnInit() {
    this.cargarExamenesCatalogo();
  }

  cargarExamenesCatalogo() {
    this.api.get<Examen[]>('/examenes/admin-lista').subscribe(data => this.examenesCatalogo.set(data));
  }

  examenesFiltrados(): Examen[] {
    const q = this.busquedaCatalogo().trim().toLowerCase();
    if (!q) return this.examenesCatalogo();
    return this.examenesCatalogo().filter(ex =>
      ex.nombre.toLowerCase().includes(q) ||
      (ex.grupo?.toLowerCase().includes(q) ?? false)
    );
  }

  cantidadDestacados(): number {
    return this.examenesCatalogo().filter(ex => ex.destacado && ex.visible).length;
  }

  toggleVisibilidadExamen(examen: Examen) {
    const listaActualizada = this.examenesCatalogo().map(ex =>
      ex.id === examen.id ? { ...ex, visible: !ex.visible, destacado: ex.visible ? false : ex.destacado } : ex
    );
    this.examenesCatalogo.set(listaActualizada);

    this.api.put<Examen>(`/examenes/${examen.id}/visibilidad`, {}).subscribe({
      next: () => this.cargarExamenesCatalogo(),
      error: (err) => {
        this.cargarExamenesCatalogo();
        this.notify.mostrarError(err, 'Error al cambiar visibilidad');
      }
    });
  }

  toggleDestacadoExamen(examen: Examen) {
    if (!examen.visible) return;
    if (!examen.destacado && this.cantidadDestacados() >= this.maxDestacados) {
      this.notify.mostrarToast(`Máximo ${this.maxDestacados} pruebas destacadas en el inicio.`, 'error');
      return;
    }

    const listaActualizada = this.examenesCatalogo().map(ex =>
      ex.id === examen.id ? { ...ex, destacado: !ex.destacado } : ex
    );
    this.examenesCatalogo.set(listaActualizada);

    this.api.put<Examen>(`/examenes/${examen.id}/destacado`, {}).subscribe({
      next: () => this.cargarExamenesCatalogo(),
      error: (err) => {
        this.cargarExamenesCatalogo();
        this.notify.mostrarError(err, 'Error al cambiar destacado');
      }
    });
  }
}
