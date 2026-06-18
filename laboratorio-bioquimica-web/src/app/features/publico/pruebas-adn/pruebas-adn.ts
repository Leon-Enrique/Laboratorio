import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';

interface PasoProceso {
  num: string;
  titulo: string;
  descripcion: string;
}

interface FaqItem {
  id: string;
  pregunta: string;
  respuesta: string;
}

@Component({
  selector: 'app-pruebas-adn',
  standalone: true,
  imports: [CommonModule, RouterLink, PublicNavbarComponent],
  templateUrl: './pruebas-adn.html',
  styleUrl: './pruebas-adn.scss'
})
export class PruebasAdnComponent {
  readonly whatsappUrl = 'https://wa.me/59175548529?text=' + encodeURIComponent(
    'Hola Genotipia, quisiera información sobre pruebas de paternidad / ADN.'
  );
  readonly telefono = '+591 75548529';

  faqAbierta = signal<string | null>(null);

  readonly pasos: PasoProceso[] = [
    {
      num: '01',
      titulo: 'Consulta inicial',
      descripcion: 'Te orientamos por WhatsApp o en el laboratorio sobre el tipo de estudio y los participantes necesarios.'
    },
    {
      num: '02',
      titulo: 'Registro',
      descripcion: 'Presentación de documentos de identidad y firma de consentimiento informado.'
    },
    {
      num: '03',
      titulo: 'Toma de muestra',
      descripcion: 'Hisopado bucal u otro tipo de muestra según el caso. Rápido, indoloro y con protocolo de cadena de custodia.'
    },
    {
      num: '04',
      titulo: 'Análisis genético',
      descripcion: 'Comparación de perfiles STR en nuestra unidad de biología molecular con interpretación estadística.'
    },
    {
      num: '05',
      titulo: 'Entrega del informe',
      descripcion: 'Resultado en 3 a 5 días hábiles. Informe físico y orientación para comprender el resultado.'
    }
  ];

  readonly faqs: FaqItem[] = [
    {
      id: 'que-es',
      pregunta: '¿Qué es una prueba de paternidad por ADN?',
      respuesta:
        'Es un análisis genético que compara perfiles de ADN para confirmar o descartar un vínculo biológico entre padre/madre e hijo/a. Utiliza marcadores STR con precisión superior al 99.9%.'
    },
    {
      id: 'tipos',
      pregunta: '¿Qué tipos de estudios de filiación realizan?',
      respuesta:
        'Paternidad, maternidad, parentesco entre hermanos y estudios de linaje (abuelos, tíos) cuando no está disponible el presunto padre. Te asesoramos para elegir el estudio adecuado.'
    },
    {
      id: 'legal',
      pregunta: '¿Puede ser privada o con validez legal?',
      respuesta:
        'Sí. Ofrecemos modalidad privada (confidencial) y modalidad con cadena de custodia para procesos legales. Los requisitos varían según el caso; coordínalo con nosotros antes de la toma de muestra.'
    },
    {
      id: 'muestra',
      pregunta: '¿Qué tipo de muestra se utiliza?',
      respuesta:
        'Lo más habitual es hisopado bucal (mucosa de la mejilla). También se puede trabajar con sangre, cabello con raíz u otras muestras según disponibilidad y objetivo del estudio.'
    },
    {
      id: 'tiempo',
      pregunta: '¿En cuánto tiempo entregan los resultados?',
      respuesta: 'El tiempo promedio es de 3 a 5 días hábiles, según el tipo de estudio y la cantidad de participantes.'
    },
    {
      id: 'confidencial',
      pregunta: '¿Qué tan confidencial es el proceso?',
      respuesta:
        'Aplicamos protocolos estrictos de resguardo de identidad, manejo de muestras y entrega controlada. Solo se informa a las personas autorizadas en el consentimiento.'
    },
    {
      id: 'sin-padre',
      pregunta: '¿Se puede hacer si falta el presunto padre?',
      respuesta:
        'En algunos casos se evalúa parentesco mediante abuelos paternos, tíos o hermanos. Nuestro equipo te orienta sobre la viabilidad estadística de cada opción.'
    }
  ];

  toggleFaq(id: string) {
    this.faqAbierta.update(actual => (actual === id ? null : id));
  }
}
