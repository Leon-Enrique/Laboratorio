import { Component, inject, signal, OnInit, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { CatalogoAnalyticsService } from '../../../core/services/catalogo-analytics.service';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';
import {
  AREAS_DIAGNOSTICAS,
  TIPOS_MUESTRA_FILTRO,
  ExamenPublico,
  codigoExamen,
  filtrarCatalogoGrid,
  iconoAreaExamen
} from '../exam-catalog.utils';

@Component({
  selector: 'app-catalogo-examenes',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PublicNavbarComponent],
  templateUrl: './catalogo-examenes.html',
  styleUrl: './catalogo-examenes.scss'
})
export class CatalogoExamenesComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);
  private analytics = inject(CatalogoAnalyticsService);
  private route = inject(ActivatedRoute);
  private busquedaDebounce: ReturnType<typeof setTimeout> | null = null;
  private scrollExamenTimer: ReturnType<typeof setTimeout> | null = null;

  readonly areas = AREAS_DIAGNOSTICAS;
  readonly tiposMuestra = TIPOS_MUESTRA_FILTRO;
  readonly whatsappUrl = 'https://wa.me/59175548529';
  readonly codigoExamen = codigoExamen;
  readonly iconoAreaExamen = iconoAreaExamen;

  examenes = signal<ExamenPublico[]>([]);
  cargando = signal(true);
  error = signal<string | null>(null);
  filtroTexto = signal('');
  categoriaActiva = signal('todos');
  materialesActivos = signal<string[]>([]);
  prepVisibleId = signal<number | null>(null);
  detalleVisibleId = signal<number | null>(null);

  examenesFiltrados = computed(() =>
    filtrarCatalogoGrid(
      this.examenes(),
      this.filtroTexto(),
      this.categoriaActiva(),
      this.materialesActivos()
    )
  );

  ngOnInit() {
    this.api.get<ExamenPublico[]>('/examenes').subscribe({
      next: data => {
        this.examenes.set(data);
        this.cargando.set(false);
        this.aplicarExamenDesdeUrl();
      },
      error: () => {
        this.error.set('No se pudo cargar el catálogo. Intenta de nuevo en unos minutos.');
        this.cargando.set(false);
      }
    });
  }

  ngOnDestroy() {
    if (this.busquedaDebounce) clearTimeout(this.busquedaDebounce);
    if (this.scrollExamenTimer) clearTimeout(this.scrollExamenTimer);
  }

  private aplicarExamenDesdeUrl() {
    const idParam = this.route.snapshot.queryParamMap.get('examen');
    if (!idParam) return;

    const id = Number(idParam);
    if (!Number.isFinite(id)) return;

    const examen = this.examenes().find(ex => ex.id === id);
    if (!examen) return;

    this.filtroTexto.set('');
    this.categoriaActiva.set('todos');
    this.materialesActivos.set([]);
    this.detalleVisibleId.set(id);
    this.prepVisibleId.set(null);

    if (this.scrollExamenTimer) clearTimeout(this.scrollExamenTimer);
    this.scrollExamenTimer = setTimeout(() => {
      document.getElementById(`examen-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 150);
  }

  onBuscar(valor: string) {
    this.filtroTexto.set(valor.toLowerCase());
    this.prepVisibleId.set(null);
    this.detalleVisibleId.set(null);

    if (this.busquedaDebounce) clearTimeout(this.busquedaDebounce);
    this.busquedaDebounce = setTimeout(() => {
      const termino = valor.trim();
      const ids = this.examenesFiltrados().map(ex => ex.id);
      this.analytics.registrarBusqueda(termino, ids);
    }, 700);
  }

  seleccionarArea(id: string) {
    this.categoriaActiva.set(id);
    this.prepVisibleId.set(null);
    this.detalleVisibleId.set(null);
  }

  toggleMaterial(id: string) {
    this.materialesActivos.update(list =>
      list.includes(id) ? list.filter(x => x !== id) : [...list, id]
    );
    this.prepVisibleId.set(null);
    this.detalleVisibleId.set(null);
  }

  materialActivo(id: string): boolean {
    return this.materialesActivos().includes(id);
  }

  limpiarFiltros(input?: HTMLInputElement) {
    if (input) input.value = '';
    this.filtroTexto.set('');
    this.categoriaActiva.set('todos');
    this.materialesActivos.set([]);
    this.prepVisibleId.set(null);
    this.detalleVisibleId.set(null);
  }

  togglePrep(id: number, event: Event) {
    event.stopPropagation();
    this.prepVisibleId.update(actual => (actual === id ? null : id));
  }

  toggleDetalle(id: number) {
    const abriendo = this.detalleVisibleId() !== id;
    this.detalleVisibleId.update(actual => (actual === id ? null : id));
    this.prepVisibleId.set(null);
    if (abriendo) {
      this.analytics.registrarClic(id);
    }
  }

  cerrarPrep() {
    this.prepVisibleId.set(null);
  }

  whatsappCita(ex: ExamenPublico): string {
    const msg = encodeURIComponent(
      `Hola Genotipia, quisiera solicitar una cita para: ${ex.nombre} (${codigoExamen(ex)}).`
    );
    return `${this.whatsappUrl}?text=${msg}`;
  }

  reintentar() {
    this.error.set(null);
    this.cargando.set(true);
    this.ngOnInit();
  }
}
