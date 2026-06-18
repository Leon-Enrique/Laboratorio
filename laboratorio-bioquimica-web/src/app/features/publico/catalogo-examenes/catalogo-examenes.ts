import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';
import { MONEDA_CODIGO } from '../../../core/constants/moneda';
import {
  CATEGORIAS_EXAMEN,
  ExamenPublico,
  agruparExamenes,
  resumenCategorias
} from '../exam-catalog.utils';

@Component({
  selector: 'app-catalogo-examenes',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PublicNavbarComponent],
  templateUrl: './catalogo-examenes.html',
  styleUrl: './catalogo-examenes.scss'
})
export class CatalogoExamenesComponent implements OnInit {
  private api = inject(ApiService);

  readonly moneda = MONEDA_CODIGO;
  readonly categorias = CATEGORIAS_EXAMEN;
  readonly whatsappUrl = 'https://wa.me/59175548529';

  examenes = signal<ExamenPublico[]>([]);
  cargando = signal(true);
  error = signal<string | null>(null);
  filtroTexto = signal('');
  categoriaActiva = signal('todos');
  expandidoId = signal<number | null>(null);

  secciones = computed(() =>
    agruparExamenes(this.examenes(), this.filtroTexto(), this.categoriaActiva())
  );

  resumen = computed(() => resumenCategorias(this.examenes()));

  totalFiltrados = computed(() =>
    this.secciones().reduce((n, s) => n + s.examenes.length, 0)
  );

  totalEspecialidades = computed(() => this.resumen().length);

  ngOnInit() {
    this.api.get<ExamenPublico[]>('/examenes').subscribe({
      next: data => {
        this.examenes.set(data);
        this.cargando.set(false);
      },
      error: () => {
        this.error.set('No se pudo cargar el catálogo. Intenta de nuevo en unos minutos.');
        this.cargando.set(false);
      }
    });
  }

  onBuscar(valor: string) {
    this.filtroTexto.set(valor.toLowerCase());
    this.expandidoId.set(null);
  }

  seleccionarCategoria(id: string) {
    this.categoriaActiva.set(id);
    this.expandidoId.set(null);
    if (id !== 'todos') {
      setTimeout(() => this.scrollACategoria(id), 50);
    }
  }

  irACategoria(id: string) {
    this.categoriaActiva.set(id);
    this.expandidoId.set(null);
    setTimeout(() => this.scrollACategoria(id), 50);
  }

  limpiarFiltros(input?: HTMLInputElement) {
    if (input) input.value = '';
    this.filtroTexto.set('');
    this.categoriaActiva.set('todos');
    this.expandidoId.set(null);
  }

  toggleDetalle(id: number) {
    this.expandidoId.update(actual => (actual === id ? null : id));
  }

  scrollACategoria(id: string) {
    document.getElementById(`cat-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  reintentar() {
    this.error.set(null);
    this.cargando.set(true);
    this.ngOnInit();
  }
}
