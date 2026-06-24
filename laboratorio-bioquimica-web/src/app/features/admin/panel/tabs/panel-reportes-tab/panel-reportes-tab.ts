import { Component, ViewEncapsulation, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { DashboardReporte, PuntoSerie, ReporteDiario } from '../../panel.models';
import {
  alturaBarra,
  buildDualLineChart,
  formatearVariacion,
  labelMetodoPago
} from '../../panel.utils';

type VistaReporte = 'panel' | 'dia' | 'mes';
type PeriodoGrafico = 'diario' | 'semanal' | 'mensual';

interface StatCard {
  id: string;
  label: string;
  value: string;
  sub?: string;
  icon: string;
  color: string;
  vista?: VistaReporte;
}

interface TopExamenRanking {
  examen_id: number;
  nombre: string;
  cantidad: number;
  ingresos: number;
  pct: number;
}

@Component({
  selector: 'app-panel-reportes-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-reportes-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelReportesTabComponent {
  private api = inject(ApiService);

  readonly moneda = MONEDA_CODIGO;
  readonly labelMetodoPago = labelMetodoPago;
  readonly alturaBarra = alturaBarra;
  readonly formatearVariacion = formatearVariacion;

  reportes = signal<DashboardReporte | null>(null);
  reportesCargando = signal(false);
  reportesError = signal<string | null>(null);
  fechaConsultaReporte = signal(new Date().toISOString().slice(0, 10));
  filtroTipoDia = signal<'todos' | 'entradas' | 'salidas'>('todos');
  reporteDia = signal<ReporteDiario | null>(null);
  reporteDiaCargando = signal(false);
  reporteDiaError = signal<string | null>(null);
  vistaReporte = signal<VistaReporte>('panel');
  periodoGrafico = signal<PeriodoGrafico>('mensual');

  maxOrdenesGrafico = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return Math.max(...meses.map(m => m.ordenes_entradas), 1);
  });

  maxIngresosGrafico = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return Math.max(...meses.map(m => m.ingresos_entradas), 1);
  });

  mesesTablaDesc = computed(() => {
    const meses = this.reportes()?.meses ?? [];
    return [...meses].reverse();
  });

  serieActiva = computed((): PuntoSerie[] => {
    const rep = this.reportes();
    if (!rep) return [];
    switch (this.periodoGrafico()) {
      case 'diario':
        return rep.serie_diaria ?? [];
      case 'semanal':
        return rep.serie_semanal ?? [];
      default:
        return rep.meses.slice(-7).map(m => ({
          etiqueta: m.etiqueta_corta,
          ordenes_entradas: m.ordenes_entradas,
          ordenes_completadas: m.ordenes_completadas,
          ingresos_entradas: m.ingresos_entradas,
          ingresos_completadas: m.ingresos_completadas
        }));
    }
  });

  chartOrdenes = computed(() => {
    const serie = this.serieActiva();
    return buildDualLineChart(
      serie.map(p => p.ordenes_entradas),
      serie.map(p => p.ordenes_completadas),
      serie.map(p => p.etiqueta)
    );
  });

  chartIngresos = computed(() => {
    const serie = this.serieActiva();
    return buildDualLineChart(
      serie.map(p => p.ingresos_entradas),
      serie.map(p => p.ingresos_completadas),
      serie.map(p => p.etiqueta)
    );
  });

  totalOrdenesSerie = computed(() =>
    this.serieActiva().reduce((sum, p) => sum + p.ordenes_entradas, 0)
  );

  totalesIngresosSerie = computed(() => {
    const serie = this.serieActiva();
    const entradas = serie.reduce((sum, p) => sum + p.ingresos_entradas, 0);
    const completadas = serie.reduce((sum, p) => sum + p.ingresos_completadas, 0);
    return { entradas, completadas, neto: entradas - completadas };
  });

  statCards = computed((): StatCard[] => {
    const rep = this.reportes();
    if (!rep) return [];
    return [
      {
        id: 'ordenes_hoy',
        label: 'Órdenes hoy',
        value: String(rep.resumen_hoy.ordenes_entradas),
        sub: `${rep.resumen_hoy.ingresos_entradas.toFixed(0)} ${rep.moneda}`,
        icon: '📋',
        color: 'blue',
        vista: 'dia'
      },
      {
        id: 'completadas_hoy',
        label: 'Completadas hoy',
        value: String(rep.resumen_hoy.ordenes_completadas),
        sub: `${rep.resumen_hoy.ingresos_completadas.toFixed(0)} ${rep.moneda}`,
        icon: '✅',
        color: 'green',
        vista: 'dia'
      },
      {
        id: 'ordenes_mes',
        label: 'Órdenes del mes',
        value: String(rep.resumen_mes_actual.ordenes_entradas),
        sub: rep.resumen_mes_actual.etiqueta,
        icon: '📅',
        color: 'yellow',
        vista: 'mes'
      },
      {
        id: 'ingresos_mes',
        label: 'Ingresos del mes',
        value: `${rep.resumen_mes_actual.ingresos_entradas.toFixed(0)}`,
        sub: rep.moneda,
        icon: '💰',
        color: 'red',
        vista: 'mes'
      },
      {
        id: 'pendientes',
        label: 'Órdenes pendientes',
        value: String(rep.pendientes_total),
        sub: `${rep.resumen_mes_actual.pendientes_del_mes} este mes`,
        icon: '⏳',
        color: 'navy',
        vista: 'dia'
      },
      {
        id: 'examenes',
        label: 'Exámenes en catálogo',
        value: String(rep.total_examenes ?? 0),
        sub: `${rep.total_pacientes ?? 0} pacientes`,
        icon: '🧪',
        color: 'purple',
        vista: 'mes'
      }
    ];
  });

  topExamenesRanking = computed((): TopExamenRanking[] => {
    const lista = this.reportes()?.top_examenes_mes ?? [];
    const max = Math.max(...lista.map(e => e.cantidad), 1);
    return lista.map(ex => ({
      ...ex,
      pct: Math.round((ex.cantidad / max) * 100)
    }));
  });

  etiquetaPeriodoGrafico = computed(() => {
    switch (this.periodoGrafico()) {
      case 'diario':
        return 'últimos 7 días';
      case 'semanal':
        return 'últimas 8 semanas';
      default:
        return 'últimos 7 meses';
    }
  });

  cargarReportes() {
    this.reportesCargando.set(true);
    this.reportesError.set(null);
    this.api.get<DashboardReporte>('/reportes/dashboard?meses=12').subscribe({
      next: (data) => {
        this.reportes.set(data);
        this.reportesCargando.set(false);
      },
      error: (err) => {
        this.reportesError.set('No se pudieron cargar los reportes. ' + (err.error?.detail || err.message));
        this.reportesCargando.set(false);
      }
    });
  }

  cargarReporteDia() {
    this.reporteDiaCargando.set(true);
    this.reporteDiaError.set(null);
    const fecha = this.fechaConsultaReporte();
    const tipo = this.filtroTipoDia();
    this.api.get<ReporteDiario>(`/reportes/dia?fecha=${fecha}&tipo=${tipo}`).subscribe({
      next: (data) => {
        this.reporteDia.set(data);
        this.reporteDiaCargando.set(false);
      },
      error: (err) => {
        this.reporteDiaError.set('No se pudo cargar el detalle del día. ' + (err.error?.detail || err.message));
        this.reporteDiaCargando.set(false);
      }
    });
  }

  cambiarFiltroDia(tipo: 'todos' | 'entradas' | 'salidas') {
    this.filtroTipoDia.set(tipo);
    this.cargarReporteDia();
  }

  irADiaRelativo(offset: number) {
    const base = new Date(this.fechaConsultaReporte() + 'T12:00:00');
    base.setDate(base.getDate() + offset);
    this.fechaConsultaReporte.set(base.toISOString().slice(0, 10));
    this.cargarReporteDia();
  }

  irAHoyReporte() {
    this.fechaConsultaReporte.set(new Date().toISOString().slice(0, 10));
    this.cargarReporteDia();
  }

  cambiarVistaReporte(vista: VistaReporte) {
    this.vistaReporte.set(vista);
    if (vista === 'dia') {
      this.cargarReporteDia();
    }
  }

  cambiarPeriodoGrafico(periodo: PeriodoGrafico) {
    this.periodoGrafico.set(periodo);
  }

  irADetalleStat(card: StatCard) {
    if (card.vista) {
      this.cambiarVistaReporte(card.vista);
    }
  }
}
