import { Component, inject, signal, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';
import { obtenerArticulosDestacados, BlogArticulo } from '../blog/blog-articles.data';

interface Examen {
  id: number;
  nombre: string;
  descripcion: string;
  preparacion: string;
  precio_usd: number;
  tiempo_entrega_horas: number;
}

interface CategoriaFiltro {
  id: string;
  label: string;
  keywords: string[];
}

interface TecnologiaItem {
  num: string;
  titulo: string;
  descripcion: string;
  tags: string[];
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
  imports: [CommonModule, RouterLink, FormsModule, BrandLogoComponent],
  templateUrl: './inicio.html',
  styleUrl: './inicio.scss'
})
export class InicioComponent implements OnInit {
  private api = inject(ApiService);

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

  readonly tecnologias: TecnologiaItem[] = [
    {
      num: '01',
      titulo: 'Bioquímica automatizada',
      descripcion: 'Analizadores de alta precisión para química clínica, electrolitos y perfiles metabólicos con control de calidad continuo.',
      tags: ['Química clínica', 'Perfiles', 'Electrolitos'],
    },
    {
      num: '02',
      titulo: 'Hematología e inmunología',
      descripcion: 'Hemogramas completos, coagulación y marcadores inmunológicos procesados con tecnología automatizada y validación experta.',
      tags: ['Hemograma', 'Coagulación', 'Inmunología'],
    },
    {
      num: '03',
      titulo: 'Biología molecular',
      descripcion: 'Detección de patógenos y estudios genéticos con técnicas moleculares de alta sensibilidad y especificidad.',
      tags: ['PCR', 'Genética', 'Molecular'],
    },
    {
      num: '04',
      titulo: 'Resultados digitales',
      descripcion: 'Portal seguro para pacientes y acceso profesional para médicos. Informes firmados electrónicamente por bioquímico regente.',
      tags: ['Online', 'Seguro', 'Trazabilidad'],
    },
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

  readonly beneficiosMedicos = [
    'Órdenes médicas registradas en el sistema LIS',
    'Resultados validados y firmados digitalmente',
    'Trazabilidad completa de muestras y reactivos',
    'Panel de acceso para personal autorizado',
  ];

  readonly beneficiosEmpresas = [
    'Programas de salud ocupacional a medida',
    'Exámenes de ingreso, periódicos y pre-retiro',
    'Facturación corporativa y reportes periódicos',
    'Coordinación de tomas de muestra para equipos',
  ];

  readonly categorias: CategoriaFiltro[] = [
    { id: 'todos', label: 'Todos', keywords: [] },
    { id: 'hematologia', label: 'Hematología', keywords: ['hemograma', 'hemat', 'sangre', 'coagul', 'plaqueta'] },
    { id: 'quimica', label: 'Química sanguínea', keywords: ['glucosa', 'colesterol', 'lipíd', 'lipid', 'renal', 'hepát', 'hepat', 'creatinina', 'urea', 'química', 'quimica'] },
    { id: 'hormonas', label: 'Hormonas', keywords: ['hormon', 'tsh', 'tiro', 'cortisol', 'insulin'] },
    { id: 'molecular', label: 'Biología molecular', keywords: ['pcr', 'molecular', 'genét', 'genet', 'adn', 'dna'] },
    { id: 'micro', label: 'Microbiología', keywords: ['orina', 'uro', 'cultivo', 'bacter', 'parasit'] },
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
  filtroTexto = signal<string>('');
  categoriaActiva = signal<string>('todos');
  examenesFiltrados = signal<Examen[]>([]);
  cargando = signal<boolean>(true);

  totalExamenes = computed(() => this.examenes().length);

  ngOnInit() {
    this.cargarExamenes();
  }

  cargarExamenes() {
    this.api.get<Examen[]>('/examenes').subscribe({
      next: (data) => {
        this.examenes.set(data);
        this.aplicarFiltros();
        this.cargando.set(false);
      },
      error: (err) => {
        console.error('Error al cargar catálogo de exámenes:', err);
        this.cargando.set(false);
      }
    });
  }

  filtrarExamenes(event: Event) {
    this.filtroTexto.set((event.target as HTMLInputElement).value.toLowerCase());
    this.aplicarFiltros();
  }

  seleccionarCategoria(id: string) {
    this.categoriaActiva.set(id);
    this.aplicarFiltros();
  }

  limpiarFiltros(input?: HTMLInputElement) {
    if (input) input.value = '';
    this.filtroTexto.set('');
    this.categoriaActiva.set('todos');
    this.aplicarFiltros();
  }

  private aplicarFiltros() {
    const query = this.filtroTexto().trim();
    const catId = this.categoriaActiva();
    const cat = this.categorias.find(c => c.id === catId);

    let lista = this.examenes();

    if (cat && cat.keywords.length > 0) {
      lista = lista.filter(ex => {
        const texto = `${ex.nombre} ${ex.descripcion}`.toLowerCase();
        return cat.keywords.some(kw => texto.includes(kw));
      });
    }

    if (query) {
      lista = lista.filter(ex =>
        ex.nombre.toLowerCase().includes(query) ||
        ex.descripcion.toLowerCase().includes(query)
      );
    }

    this.examenesFiltrados.set(lista);
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
