import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';
import { MONEDA_CODIGO } from '../../../core/constants/moneda';
import { obtenerArticulosDestacados, BlogArticulo } from '../blog/blog-articles.data';
import {
  MAX_DESTACADOS_INICIO,
  ExamenPublico
} from '../exam-catalog.utils';

interface Examen extends ExamenPublico {}

interface PasoVisita {
  num: string;
  icono: string;
  titulo: string;
  descripcion: string;
}

interface PilarGenotipia {
  num: string;
  icono: string;
  titulo: string;
  descripcion: string;
  accent: 'green' | 'blue' | 'teal' | 'amber';
}

interface TecnologiaItem {
  num: string;
  titulo: string;
  descripcion: string;
  tags: string[];
  icono: string;
  accent: 'green' | 'blue' | 'teal' | 'violet';
  destacado?: boolean;
}

interface GaleriaItem {
  titulo: string;
  subtitulo: string;
  tema: 'central' | 'molecular' | 'equipo' | 'atencion';
  /** Ruta en public/, ej: 'imagenes/laboratorio/central.jpg' — vacío = placeholder */
  imagen?: string;
}

interface HorarioItem {
  dias: string;
  horas: string;
  destacado?: boolean;
}

interface InstagramPost {
  titulo: string;
  etiqueta: string;
  tema: 'adn' | 'lab' | 'salud';
}

@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [CommonModule, RouterLink, FormsModule, BrandLogoComponent, PublicNavbarComponent],
  templateUrl: './inicio.html',
  styleUrl: './inicio.scss'
})
export class InicioComponent implements OnInit {
  private api = inject(ApiService);

  readonly moneda = MONEDA_CODIGO;
  readonly whatsappUrl = 'https://wa.me/59175548529';
  readonly telefono = '755 48529';
  readonly telefonoTel = '+59175548529';
  readonly email = 'contacto@genotipia.com';
  readonly direccion = 'Av. Japón N° 3555, 3er. Anillo Externo — Diagonal entrada Emergencias Hospital Japonés, Santa Cruz de la Sierra';
  readonly mapsUrl = 'https://maps.app.goo.gl/VkYj2TjRARZuUaFE7';
  readonly instagramUrl = 'https://www.instagram.com/genotipia';
  readonly instagramHandle = '@genotipia';

  readonly instagramPosts: InstagramPost[] = [
    { titulo: 'Precisión en cada análisis', etiqueta: 'Laboratorio', tema: 'lab' },
    { titulo: 'Biología molecular y genética', etiqueta: 'Tecnología', tema: 'adn' },
    { titulo: 'Cuida tu salud con chequeos', etiqueta: 'Prevención', tema: 'salud' },
  ];

  readonly blogDestacados: BlogArticulo[] = obtenerArticulosDestacados(3);
  readonly mapsEmbedSafe: SafeResourceUrl = inject(DomSanitizer).bypassSecurityTrustResourceUrl(
    'https://maps.google.com/maps?q=-17.7731508,-63.1541142&hl=es&z=17&output=embed'
  );

  readonly pilares: PilarGenotipia[] = [
    {
      num: '01',
      icono: '🔬',
      titulo: 'Tecnología avanzada',
      descripcion: 'Analizadores automatizados con trazabilidad completa de muestras en cada etapa del proceso.',
      accent: 'green',
    },
    {
      num: '02',
      icono: '⚡',
      titulo: 'Resultados rápidos',
      descripcion: 'Flujo optimizado que reduce tiempos de entrega sin sacrificar precisión ni rigor analítico.',
      accent: 'amber',
    },
    {
      num: '03',
      icono: '🔒',
      titulo: 'Confidencialidad',
      descripcion: 'Acceso seguro y privado a los reportes clínicos. Tu información protegida en todo momento.',
      accent: 'blue',
    },
    {
      num: '04',
      icono: '📋',
      titulo: 'Informes certificados',
      descripcion: 'Resultados validados y firmados electrónicamente por nuestro bioquímico regente.',
      accent: 'teal',
    },
  ];

  readonly aboutDestacados = [
    'Bioquímico regente en cada validación',
    'Protocolos de bioseguridad y control de calidad',
    'Atención cercana en Santa Cruz de la Sierra',
  ];

  readonly tecnologias: TecnologiaItem[] = [
    {
      num: '01',
      titulo: 'Bioquímica automatizada',
      descripcion: 'Analizadores de alta precisión para química clínica, electrolitos y perfiles metabólicos con control de calidad continuo.',
      tags: ['Química clínica', 'Perfiles', 'Electrolitos'],
      icono: '⚗️',
      accent: 'green',
    },
    {
      num: '02',
      titulo: 'Hematología e inmunología',
      descripcion: 'Hemogramas completos, coagulación y marcadores inmunológicos procesados con tecnología automatizada y validación experta.',
      tags: ['Hemograma', 'Coagulación', 'Inmunología'],
      icono: '🔬',
      accent: 'blue',
    },
    {
      num: '03',
      titulo: 'Biología molecular',
      descripcion: 'Detección de patógenos y estudios genéticos con técnicas moleculares de alta sensibilidad y especificidad.',
      tags: ['PCR', 'Genética', 'Molecular'],
      icono: '🧬',
      accent: 'teal',
      destacado: true,
    },
    {
      num: '04',
      titulo: 'Resultados digitales',
      descripcion: 'Portal seguro para pacientes y acceso profesional para médicos. Informes firmados electrónicamente por bioquímico regente.',
      tags: ['Online', 'Seguro', 'Trazabilidad'],
      icono: '📲',
      accent: 'violet',
    },
  ];

  readonly techMetricas = [
    { valor: 'LIS', etiqueta: 'Trazabilidad integral' },
    { valor: '24/7', etiqueta: 'Control de calidad' },
    { valor: '100%', etiqueta: 'Resultados firmados' },
    { valor: 'ISO', etiqueta: '15189 en proceso' },
  ];

  /**
   * Galería de instalaciones.
   * Cuando tengas fotos, guárdalas en public/imagenes/laboratorio/
   * y asigna la ruta en el campo `imagen` de cada ítem.
   */
  readonly galeria: GaleriaItem[] = [
    {
      titulo: 'Entrada principal',
      subtitulo: 'Fachada de Genotipia — Laboratorio Clínico',
      tema: 'central',
      imagen: 'imagenes/laboratorio/fachada.png',
    },
    {
      titulo: 'Unidad Molecular',
      subtitulo: 'Biología molecular y estudios genéticos',
      tema: 'molecular',
      // imagen: 'imagenes/laboratorio/molecular.jpg',
    },
    {
      titulo: 'Toma de muestras',
      subtitulo: 'Área de extracción con bioseguridad y atención al paciente',
      tema: 'equipo',
      imagen: 'imagenes/laboratorio/toma_muestras.png',
    },
    {
      titulo: 'Atención al paciente',
      subtitulo: 'Recepción y orientación en toma de muestras',
      tema: 'atencion',
      imagen: 'imagenes/laboratorio/recepcion.png',
    },
  ];

  readonly horarios: HorarioItem[] = [
    { dias: 'Lunes a viernes', horas: '07:00 – 19:00', destacado: true },
    { dias: 'Sábados', horas: '07:00 – 12:00' },
    { dias: 'Domingos y feriados', horas: 'Cerrado · consultar urgencias' },
  ];

  readonly pasosVisita: PasoVisita[] = [
    {
      num: '01',
      icono: '💬',
      titulo: 'Coordinación',
      descripcion: 'Escríbenos por WhatsApp o acércate al laboratorio. Te orientamos sobre el examen y su preparación.',
    },
    {
      num: '02',
      icono: '🩸',
      titulo: 'Toma de muestra',
      descripcion: 'Registro en recepción y extracción con protocolos de bioseguridad. Rápido y con atención personalizada.',
    },
    {
      num: '03',
      icono: '🔬',
      titulo: 'Análisis en laboratorio',
      descripcion: 'Procesamos tu muestra con equipamiento automatizado y control de calidad en cada etapa.',
    },
    {
      num: '04',
      icono: '📱',
      titulo: 'Resultados',
      descripcion: 'Consulta tu informe online con código de orden y documento, o retíralo en el laboratorio.',
    },
  ];

  readonly tickerItems = [
    'Resultados online',
    'Control de calidad',
    'Análisis bioquímicos',
    'Tecnología automatizada',
    'Atención personalizada',
    'Preparación guiada',
  ];

  reclamoNombre = signal('');
  reclamoEmail = signal('');
  reclamoMensaje = signal('');
  reclamoEnviado = signal(false);
  reclamoError = signal<string | null>(null);
  enviandoReclamo = signal(false);

  examenes = signal<Examen[]>([]);
  examenesDestacados = signal<Examen[]>([]);
  cargandoDestacados = signal<boolean>(true);
  errorDestacados = signal<string | null>(null);

  totalExamenes = computed(() => this.examenes().length);

  ngOnInit() {
    this.cargarCatalogo();
  }

  cargarCatalogo() {
    this.api.get<Examen[]>('/examenes').subscribe({
      next: data => {
        this.examenes.set(data);
        const marcados = data.filter(ex => ex.destacado);
        const lista =
          marcados.length > 0
            ? marcados.slice(0, MAX_DESTACADOS_INICIO)
            : data.slice(0, MAX_DESTACADOS_INICIO);
        this.examenesDestacados.set(lista);
        this.cargandoDestacados.set(false);
      },
      error: () => {
        this.errorDestacados.set('No se pudieron cargar los exámenes destacados.');
        this.cargandoDestacados.set(false);
      }
    });
  }

  reintentarDestacados() {
    this.errorDestacados.set(null);
    this.cargandoDestacados.set(true);
    this.cargarCatalogo();
  }

  enviarReclamo() {
    const nombre = this.reclamoNombre().trim();
    const email = this.reclamoEmail().trim();
    const mensaje = this.reclamoMensaje().trim();

    if (!nombre || !email || !mensaje) {
      this.reclamoError.set('Por favor completa todos los campos.');
      this.reclamoEnviado.set(false);
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      this.reclamoError.set('Ingresa un correo electrónico válido.');
      return;
    }

    this.enviandoReclamo.set(true);
    this.reclamoError.set(null);

    const subject = encodeURIComponent(`Contacto Genotipia — ${nombre}`);
    const body = encodeURIComponent(
      `Nombre: ${nombre}\nEmail: ${email}\n\nMensaje:\n${mensaje}\n\n— Enviado desde genotipia.com`
    );

    window.location.href = `mailto:${this.email}?subject=${subject}&body=${body}`;

    this.reclamoEnviado.set(true);
    this.enviandoReclamo.set(false);
    this.reclamoNombre.set('');
    this.reclamoEmail.set('');
    this.reclamoMensaje.set('');
  }

  enviarReclamoWhatsApp() {
    const nombre = this.reclamoNombre().trim();
    const mensaje = this.reclamoMensaje().trim();
    const texto = encodeURIComponent(
      `Hola Genotipia, soy ${nombre || 'un paciente'}.\n\n${mensaje || 'Quisiera hacer una consulta.'}`
    );
    window.open(`${this.whatsappUrl}?text=${texto}`, '_blank', 'noopener');
  }
}
