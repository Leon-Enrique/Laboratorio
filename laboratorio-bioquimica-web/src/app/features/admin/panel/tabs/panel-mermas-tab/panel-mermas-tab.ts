import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../../../core/services/api.service';
import { MermaInventario } from '../../panel.models';

@Component({
  selector: 'app-panel-mermas-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './panel-mermas-tab.html'
})
export class PanelMermasTabComponent {
  private api = inject(ApiService);

  mermas = signal<MermaInventario[]>([]);
  cargando = signal(false);

  cargarMermas() {
    this.cargando.set(true);
    this.api.get<MermaInventario[]>('/inventario/mermas').subscribe({
      next: (data) => {
        this.mermas.set(data);
        this.cargando.set(false);
      },
      error: () => this.cargando.set(false)
    });
  }

  etiquetaMotivo(motivo: string): string {
    return motivo;
  }
}
