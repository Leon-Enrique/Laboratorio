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
  ExamenPublico,
  tituloDestacado,
  subtituloDestacado,
  descripcionDestacado
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

interface TechProcesoVisual {
  titulo: string;
  descripcion: string;
  imagen: string;
  etiqueta: string;
}

interface GaleriaItem {
  titulo: string;
  subtitulo: string;
  imagen: string;
  etiqueta: string;
}

interface HorarioItem {
  dias: string;
  horas: string;
  destacado?: boolean;
}

interface RedesPost {
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
  readonly email = 'contacto@genotipia-lab.com';
  readonly direccion = 'Av. Japón N° 3555, 3er. Anillo Externo — Diagonal entrada Emergencias Hospital Japonés, Santa Cruz de la Sierra';
  readonly mapsUrl = 'https://maps.app.goo.gl/VkYj2TjRARZuUaFE7';
  readonly instagramUrl = 'https://www.instagram.com/genotipia';
  readonly instagramHandle = '@genotipia';
  readonly tiktokUrl = 'https://www.tiktok.com/@genotipia.lab';
  readonly tiktokHandle = '@genotipia.lab';

  readonly instagramPosts: RedesPost[] = [
    { titulo: 'Precisión en cada análisis', etiqueta: 'Laboratorio', tema: 'lab' },
    { titulo: 'Biología molecular y genética', etiqueta: 'Tecnología', tema: 'adn' },
    { titulo: 'Cuida tu salud con chequeos', etiqueta: 'Prevención', tema: 'salud' },
  ];

  readonly tiktokPosts: RedesPost[] = [
    { titulo: 'Detrás del laboratorio', etiqueta: 'Genotipia', tema: 'lab' },
    { titulo: 'Tips de salud en 60 segundos', etiqueta: 'Consejos', tema: 'salud' },
    { titulo: 'Pruebas de ADN explicadas', etiqueta: 'ADN', tema: 'adn' },
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
      titulo: 'Bioquímica clínica',
      descripcion: 'Perfiles metabólicos, electrolitos y química sanguínea con analizadores automatizados y control de calidad en cada corrida.',
      tags: ['Perfiles', 'Electrolitos', 'Glucosa'],
      icono: '⚗️',
      accent: 'green',
      destacado: true,
    },
    {
      num: '02',
      titulo: 'Hematología',
      descripcion: 'Hemogramas, coagulación e inmunología con validación por personal especializado antes de liberar el informe.',
      tags: ['Hemograma', 'Coagulación', 'Inmunología'],
      icono: '🔬',
      accent: 'blue',
    },
    {
      num: '03',
      titulo: 'Biología molecular',
      descripcion: 'PCR, genética y detección de patógenos con protocolos de alta sensibilidad para estudios especializados.',
      tags: ['PCR', 'Genética', 'ADN'],
      icono: '🧬',
      accent: 'teal',
    },
    {
      num: '04',
      titulo: 'Informes digitales',
      descripcion: 'Portal seguro para pacientes y médicos. Resultados firmados por bioquímico regente, disponibles cuando estén validados.',
      tags: ['Online', 'Seguro', 'Firma digital'],
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

  /** Stock clínico (Unsplash, guardado en public/) — reemplazable por fotos propias */
  readonly techHeroImagen = '/imagenes/laboratorio/stock/hero-lab.jpg';

  readonly techProcesos: TechProcesoVisual[] = [
    {
      titulo: 'Automatización analítica',
      descripcion: 'Analizadores de última generación para química clínica con control en cada corrida.',
      imagen: '/imagenes/laboratorio/stock/automatizacion.jpg',
      etiqueta: 'Precisión',
    },
    {
      titulo: 'Control de calidad',
      descripcion: 'Verificación continua y trazabilidad LIS en todo el flujo de muestras.',
      imagen: '/imagenes/laboratorio/stock/control-calidad.jpg',
      etiqueta: 'Confianza',
    },
    {
      titulo: 'Biología molecular',
      descripcion: 'PCR y genética con protocolos de alta sensibilidad para estudios especializados.',
      imagen: '/imagenes/laboratorio/stock/molecular.jpg',
      etiqueta: 'Genética',
    },
  ];

  readonly techAdnImagen = '/imagenes/laboratorio/stock/adn-banner.jpg';

  /**
   * Galería de instalaciones.
   * Cuando tengas fotos, guárdalas en public/imagenes/laboratorio/
   * y asigna la ruta en el campo `imagen` de cada ítem.
   */
  readonly galeria: GaleriaItem[] = [
    {
      titulo: 'Entrada principal',
      subtitulo: 'Fachada de Genotipia — Laboratorio Clínico',
      imagen: '/imagenes/laboratorio/fachada.png',
      etiqueta: 'Instalaciones',
    },
    {
      titulo: 'Toma de muestras',
      subtitulo: 'Área de extracción con bioseguridad y atención al paciente',
      imagen: '/imagenes/laboratorio/toma_muestras.png',
      etiqueta: 'Extracción',
    },
    {
      titulo: 'Atención al paciente',
      subtitulo: 'Recepción y orientación en toma de muestras',
      imagen: '/imagenes/laboratorio/recepcion.png',
      etiqueta: 'Recepción',
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

  readonly tituloDestacado = tituloDestacado;
  readonly subtituloDestacado = subtituloDestacado;
  readonly descripcionDestacado = descripcionDestacado;

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
        this.cargarDestacados();
      },
      error: () => {
        this.errorDestacados.set('No se pudieron cargar los exámenes destacados.');
        this.cargandoDestacados.set(false);
      }
    });
  }

  cargarDestacados() {
    this.api.get<Examen[]>('/examenes?destacados=true').subscribe({
      next: data => {
        this.examenesDestacados.set(data.slice(0, MAX_DESTACADOS_INICIO));
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
    this.cargarDestacados();
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
      `Nombre: ${nombre}\nEmail: ${email}\n\nMensaje:\n${mensaje}\n\n— Enviado desde genotipia-lab.com`
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
