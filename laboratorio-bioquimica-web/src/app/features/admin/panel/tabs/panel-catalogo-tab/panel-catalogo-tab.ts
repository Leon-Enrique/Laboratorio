import { Component, ViewEncapsulation, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { Examen } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';
import { PanelCacheService } from '../../panel-cache.service';

@Component({
  selector: 'app-panel-catalogo-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-catalogo-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelCatalogoTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);
  private cache = inject(PanelCacheService);

  readonly moneda = MONEDA_CODIGO;

  examenesCatalogo = signal<Examen[]>([]);
  busquedaCatalogo = signal('');

  cargarExamenesCatalogo() {
    this.cache.examenesParaPanel(true).subscribe(data => this.examenesCatalogo.set(data));
  }

  examenesFiltrados(): Examen[] {
    const q = this.busquedaCatalogo().trim().toLowerCase();
    if (!q) return this.examenesCatalogo();
    return this.examenesCatalogo().filter(ex =>
      ex.nombre.toLowerCase().includes(q) ||
      (ex.grupo?.toLowerCase().includes(q) ?? false)
    );
  }

  toggleVisibilidadExamen(examen: Examen) {
    const listaActualizada = this.examenesCatalogo().map(ex =>
      ex.id === examen.id ? { ...ex, visible: !ex.visible, destacado: ex.visible ? false : ex.destacado } : ex
    );
    this.examenesCatalogo.set(listaActualizada);

    this.api.put<Examen>(`/examenes/${examen.id}/visibilidad`, {}).subscribe({
      next: () => {
        this.cache.invalidarExamenes();
        this.cargarExamenesCatalogo();
      },
      error: (err) => {
        this.cargarExamenesCatalogo();
        this.notify.mostrarError(err, 'Error al cambiar visibilidad');
      }
    });
  }
}
