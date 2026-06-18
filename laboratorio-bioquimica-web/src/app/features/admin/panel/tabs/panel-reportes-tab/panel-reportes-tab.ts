import { Component, ViewEncapsulation, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../../../core/services/api.service';
import { MONEDA_CODIGO } from '../../../../../core/constants/moneda';
import { DashboardReporte, ReporteDiario } from '../../panel.models';
import { alturaBarra, formatearVariacion, labelMetodoPago } from '../../panel.utils';

@Component({
  selector: 'app-panel-reportes-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-reportes-tab.html',
  styleUrl: '../../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelReportesTabComponent implements OnInit {
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
  vistaReporte = signal<'dia' | 'mes'>('dia');

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

  ngOnInit() {
    this.cargarReportes();
  }

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
    this.cargarReporteDia();
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

  cambiarVistaReporte(vista: 'dia' | 'mes') {
    this.vistaReporte.set(vista);
  }
}
