import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { ApiService } from '../../../core/services/api.service';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';
import { esParametroResultadoVisible } from '../../admin/panel/catalogo-examen.options';

interface ParametroExamen {
  id: number;
  nombre: string;
  unidad?: string | null;
  valor_min?: number | null;
  valor_max?: number | null;
  orden?: number;
}

interface Paciente {
  dni: string;
  nombre: string;
  apellido: string;
  fecha_nacimiento?: string;
}

interface Resultado {
  id: number;
  examen_id: number;
  valor_resultado: Record<string, string> | null;
  pdf_url: string | null;
  fecha_registro: string;
  examen?: {
    id: number;
    nombre: string;
    parametros?: ParametroExamen[];
  };
}

interface Orden {
  id: number;
  codigo_orden: string;
  fecha_creacion: string;
  estado: string;
  paciente: Paciente;
  resultados: Resultado[];
}

interface FilaResultado {
  label: string;
  valor: string;
  referencia: string;
  estado: { label: string; clase: string };
}

@Component({
  selector: 'app-resultados-paciente',
  standalone: true,
  imports: [CommonModule, FormsModule, PublicNavbarComponent],
  templateUrl: './resultados-paciente.html',
  styleUrl: './resultados-paciente.scss'
})
export class ResultadosPacienteComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  codigoBusqueda = signal<string>('');
  dniVerificacion = signal<string>('');
  fechaNacVerificacion = signal<string>('');
  paso = signal<1 | 2>(1);
  codigoValido = signal<boolean | null>(null);

  orden = signal<Orden | null>(null);
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

  ngOnInit() {
    const codigo = this.route.snapshot.queryParamMap.get('codigo');
    if (codigo) {
      this.codigoBusqueda.set(codigo.toUpperCase());
      this.verificarCodigo();
    }
  }

  continuarVerificacion() {
    this.verificarCodigo();
  }

  verificarCodigo() {
    const codigo = this.codigoBusqueda().trim().toUpperCase();
    if (!codigo) return;

    this.cargando.set(true);
    this.error.set(null);
    this.codigoValido.set(null);

    this.api.get<{ existe: boolean; mensaje: string }>(`/ordenes/consulta/verificar/${codigo}`).subscribe({
      next: (data) => {
        this.codigoValido.set(data.existe);
        if (data.existe) {
          this.paso.set(2);
          this.error.set(null);
        } else {
          this.error.set(data.mensaje);
          this.paso.set(1);
        }
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set(err.error?.detail || 'No se pudo verificar el código.');
        this.cargando.set(false);
      }
    });
  }

  buscarResultados() {
    const codigo = this.codigoBusqueda().trim().toUpperCase();
    const dni = this.dniVerificacion().trim();
    const fecha = this.fechaNacVerificacion();
    if (!codigo || !dni || !fecha) {
      this.error.set('Complete el código, CI y fecha de nacimiento.');
      return;
    }

    this.cargando.set(true);
    this.error.set(null);
    this.orden.set(null);

    this.api.post<Orden>('/ordenes/consulta', {
      codigo_orden: codigo,
      dni,
      fecha_nacimiento: fecha
    }).subscribe({
      next: (data) => {
        this.orden.set(data);
        this.cargando.set(false);
      },
      error: (err) => {
        this.error.set(err.error?.detail || 'No se pudieron obtener los resultados. Verifique sus datos.');
        this.cargando.set(false);
      }
    });
  }

  descargarInformePdf() {
    const orden = this.orden();
    if (!orden || orden.estado !== 'COMPLETADO') return;

    this.api.getBlobPublic(`/ordenes/informe/${orden.codigo_orden}/pdf`, {
      dni: this.dniVerificacion().trim(),
      fecha_nacimiento: this.fechaNacVerificacion()
    }).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
      },
      error: () => this.error.set('No se pudo descargar el informe PDF.')
    });
  }

  nombreExamen(res: Resultado): string {
    return res.examen?.nombre || 'Examen Clínico';
  }

  evaluarEstado(res: Resultado, param: ParametroExamen): { label: string; clase: string } {
    const valores = res.valor_resultado || {};
    const clave = this.parametroClave(param);
    const valorStr = valores[clave] ?? valores[param.nombre];
    if (valorStr == null || valorStr === '') {
      return { label: '—', clase: '' };
    }

    const valor = parseFloat(String(valorStr).replace(',', '.'));
    if (Number.isNaN(valor)) {
      const texto = String(valorStr).toLowerCase();
      if (/positivo|reactive|alto|elevado/.test(texto)) {
        return { label: 'Alterado', clase: 'status-danger' };
      }
      if (/negativo|normal|no reactivo/.test(texto)) {
        return { label: 'Normal', clase: 'status-success-light' };
      }
      return { label: '—', clase: '' };
    }

    if (param.valor_min != null && valor < param.valor_min) {
      return { label: 'Bajo', clase: 'status-warn' };
    }
    if (param.valor_max != null && valor > param.valor_max) {
      return { label: 'Alto', clase: 'status-danger' };
    }
    return { label: 'Normal', clase: 'status-success-light' };
  }

  referenciaTextoParam(param: ParametroExamen): string {
    if (param.valor_min != null && param.valor_max != null) {
      return `${param.valor_min} – ${param.valor_max}${param.unidad ? ' ' + param.unidad : ''}`;
    }
    if (param.valor_max != null) {
      return `≤ ${param.valor_max}${param.unidad ? ' ' + param.unidad : ''}`;
    }
    if (param.valor_min != null) {
      return `≥ ${param.valor_min}${param.unidad ? ' ' + param.unidad : ''}`;
    }
    return 'Consultar laboratorio';
  }

  filasResultado(res: Resultado): FilaResultado[] {
    const valores = res.valor_resultado || {};
    const params = [...(res.examen?.parametros || [])]
      .filter(p => esParametroResultadoVisible(p.nombre))
      .sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0));

    if (params.length) {
      return params.map(param => {
        const clave = this.parametroClave(param);
        const valor = valores[clave] ?? valores[param.nombre] ?? '—';
        return {
          label: param.unidad ? `${param.nombre} (${param.unidad})` : param.nombre,
          valor: String(valor),
          referencia: this.referenciaTextoParam(param),
          estado: this.evaluarEstado(res, param)
        };
      });
    }

    return Object.keys(valores).map(key => ({
      label: key,
      valor: String(valores[key]),
      referencia: '—',
      estado: { label: '—', clase: '' }
    }));
  }

  parametroClave(p: ParametroExamen): string {
    return p.unidad ? `${p.nombre} (${p.unidad})` : p.nombre;
  }

  volverPaso1() {
    this.paso.set(1);
    this.orden.set(null);
    this.error.set(null);
  }
}
