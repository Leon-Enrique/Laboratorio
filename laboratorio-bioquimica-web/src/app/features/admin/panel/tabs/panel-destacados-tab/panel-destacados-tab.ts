import { Component, ViewEncapsulation, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { Examen } from '../../panel.models';
import { PanelNotifyService } from '../../panel-notify.service';
import { PanelCacheService } from '../../panel-cache.service';
import {
  MAX_DESTACADOS_INICIO,
  descripcionDestacado,
  tituloDestacado
} from '../../../../publico/exam-catalog.utils';

interface DestacadoForm {
  examen_id: number | null;
  titulo_destacado: string;
  subtitulo_destacado: string;
  descripcion_destacado: string;
  orden_destacado: number | null;
}

interface MasBuscadoItem {
  examen_id: number;
  nombre: string;
  grupo?: string | null;
  contador_busquedas: number;
  contador_clics: number;
  puntuacion: number;
  ya_destacado: boolean;
  visible: boolean;
}

@Component({
  selector: 'app-panel-destacados-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-destacados-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelDestacadosTabComponent {
  private api = inject(ApiService);
  private notify = inject(PanelNotifyService);
  private cache = inject(PanelCacheService);

  readonly moneda = MONEDA_CODIGO;
  readonly maxDestacados = MAX_DESTACADOS_INICIO;
  readonly tituloDestacado = tituloDestacado;
  readonly descripcionDestacado = descripcionDestacado;

  examenesCatalogo = signal<Examen[]>([]);
  masBuscados = signal<MasBuscadoItem[]>([]);
  cargandoSugerencias = signal(true);
  mostrarFormulario = signal(false);
  editandoId = signal<number | null>(null);
  guardando = signal(false);
  formulario = signal<DestacadoForm>(this.formularioVacio());

  destacadosActuales = computed(() =>
    this.examenesCatalogo()
      .filter(ex => ex.destacado && ex.visible)
      .sort((a, b) => (a.orden_destacado ?? 999) - (b.orden_destacado ?? 999) || a.nombre.localeCompare(b.nombre))
  );

  examenesDisponibles = computed(() => {
    const editId = this.editandoId();
    return this.examenesCatalogo().filter(
      ex => ex.visible && (!ex.destacado || ex.id === editId)
    );
  });

  examenEditando = computed(() => {
    const id = this.editandoId();
    if (!id) return null;
    return this.examenesCatalogo().find(ex => ex.id === id) ?? null;
  });

  sugerenciasDisponibles = computed(() =>
    this.masBuscados().filter(item => item.visible && !item.ya_destacado)
  );

  cargarExamenes() {
    this.cache.examenesParaPanel(true).subscribe(data => this.examenesCatalogo.set(data));
  }

  cargarMasBuscados() {
    this.cargandoSugerencias.set(true);
    this.api.get<MasBuscadoItem[]>('/examenes/analytics/mas-buscados?limite=10').subscribe({
      next: data => {
        this.masBuscados.set(data);
        this.cargandoSugerencias.set(false);
      },
      error: () => {
        this.masBuscados.set([]);
        this.cargandoSugerencias.set(false);
      }
    });
  }

  abrirNuevo() {
    if (this.destacadosActuales().length >= this.maxDestacados) {
      this.notify.mostrarToast(`Máximo ${this.maxDestacados} destacados en el inicio.`, 'error');
      return;
    }
    const siguienteOrden = Math.min(this.destacadosActuales().length + 1, this.maxDestacados);
    this.editandoId.set(null);
    this.formulario.set({
      ...this.formularioVacio(),
      orden_destacado: siguienteOrden
    });
    this.mostrarFormulario.set(true);
  }

  abrirEditar(examen: Examen) {
    this.editandoId.set(examen.id);
    this.formulario.set({
      examen_id: examen.id,
      titulo_destacado: examen.titulo_destacado?.trim() || examen.nombre,
      subtitulo_destacado: examen.subtitulo_destacado ?? '',
      descripcion_destacado: examen.descripcion_destacado?.trim() || (examen.descripcion ?? '').slice(0, 200),
      orden_destacado: examen.orden_destacado ?? null
    });
    this.mostrarFormulario.set(true);
  }

  cancelarFormulario() {
    this.mostrarFormulario.set(false);
    this.editandoId.set(null);
    this.formulario.set(this.formularioVacio());
  }

  onExamenSeleccionado(examenId: number | null) {
    if (!examenId) return;
    const examen = this.examenesCatalogo().find(ex => ex.id === examenId);
    if (!examen) return;
    this.formulario.update(f => ({
      ...f,
      examen_id: examenId,
      titulo_destacado: f.titulo_destacado || examen.nombre,
      descripcion_destacado: f.descripcion_destacado || (examen.descripcion ?? '').slice(0, 160)
    }));
  }

  agregarDesdeSugerencia(item: MasBuscadoItem) {
    if (this.destacadosActuales().length >= this.maxDestacados) {
      this.notify.mostrarToast(`Máximo ${this.maxDestacados} destacados en el inicio.`, 'error');
      return;
    }
    const examen = this.examenesCatalogo().find(ex => ex.id === item.examen_id);
    if (!examen) return;

    this.editandoId.set(null);
    this.formulario.set({
      examen_id: examen.id,
      titulo_destacado: examen.nombre,
      subtitulo_destacado: 'Más buscado en catálogo',
      descripcion_destacado: (examen.descripcion ?? '').slice(0, 200),
      orden_destacado: Math.min(this.destacadosActuales().length + 1, this.maxDestacados)
    });
    this.mostrarFormulario.set(true);
  }

  guardar() {
    const form = this.formulario();
    const examenId = this.editandoId() ?? form.examen_id;
    if (!examenId) {
      this.notify.mostrarToast('Selecciona una prueba del catálogo.', 'error');
      return;
    }

    this.guardando.set(true);
    this.api
      .put<Examen>(`/examenes/${examenId}/destacado-config`, {
        destacado: true,
        titulo_destacado: form.titulo_destacado.trim() || null,
        subtitulo_destacado: form.subtitulo_destacado.trim() || null,
        descripcion_destacado: form.descripcion_destacado.trim() || null,
        orden_destacado: form.orden_destacado
      })
      .subscribe({
        next: () => {
          this.guardando.set(false);
          this.cache.invalidarExamenes();
          this.notify.mostrarToast('Destacado guardado.', 'success');
          this.cancelarFormulario();
          this.cargarExamenes();
          this.cargarMasBuscados();
        },
        error: err => {
          this.guardando.set(false);
          this.notify.mostrarError(err, 'Error al guardar destacado');
        }
      });
  }

  quitar(examen: Examen) {
    if (!confirm(`¿Quitar "${examen.nombre}" de los destacados del inicio?`)) return;

    this.api
      .put<Examen>(`/examenes/${examen.id}/destacado-config`, { destacado: false })
      .subscribe({
        next: () => {
          this.cache.invalidarExamenes();
          this.notify.mostrarToast('Destacado eliminado.', 'success');
          this.cargarExamenes();
          this.cargarMasBuscados();
        },
        error: err => this.notify.mostrarError(err, 'Error al quitar destacado')
      });
  }

  private formularioVacio(): DestacadoForm {
    return {
      examen_id: null,
      titulo_destacado: '',
      subtitulo_destacado: '',
      descripcion_destacado: '',
      orden_destacado: null
    };
  }
}
