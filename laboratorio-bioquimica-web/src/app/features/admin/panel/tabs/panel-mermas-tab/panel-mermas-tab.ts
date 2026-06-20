import { Component, ViewEncapsulation, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../../../../core/services/api.service';
import { MermaInventario } from '../../panel.models';

@Component({
  selector: 'app-panel-mermas-tab',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './panel-mermas-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelMermasTabComponent implements OnInit {
  private api = inject(ApiService);

  mermas = signal<MermaInventario[]>([]);
  cargando = signal(false);

  ngOnInit() {
    this.cargarMermas();
  }

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
