export interface BlogArticulo {
  slug: string;
  titulo: string;
  resumen: string;
  categoria: string;
  tiempoLectura: string;
  fecha: string;
  destacado?: boolean;
  parrafos: string[];
}

export const BLOG_ARTICULOS: BlogArticulo[] = [
  {
    slug: 'hemograma-completo-guia',
    titulo: 'Hemograma completo: qué mide y cómo interpretarlo',
    resumen: 'Conoce los parámetros principales del hemograma y qué información entrega sobre tu salud sanguínea.',
    categoria: 'Hematología',
    tiempoLectura: '8 min',
    fecha: 'Mayo 2026',
    destacado: true,
    parrafos: [
      'El hemograma completo es uno de los análisis más solicitados en medicina clínica. Permite evaluar glóbulos rojos, glóbulos blancos y plaquetas, ofreciendo una visión general del estado del sistema sanguíneo.',
      'Los glóbulos rojos transportan oxígeno; una disminución puede indicar anemia. Los glóbulos blancos participan en la defensa ante infecciones, y las plaquetas son fundamentales en la coagulación.',
      'En Genotipia procesamos hemogramas con analizadores automatizados y validación por personal bioquímico especializado, garantizando resultados confiables para tu médico tratante.',
    ],
  },
  {
    slug: 'ayuno-analisis-sangre',
    titulo: 'Ayuno para análisis de sangre: mitos y recomendaciones',
    resumen: 'Cuándo es necesario ayunar, cuántas horas y qué exámenes no requieren preparación especial.',
    categoria: 'Preparación',
    tiempoLectura: '6 min',
    fecha: 'Abril 2026',
    destacado: true,
    parrafos: [
      'Muchos pacientes creen que todos los exámenes de sangre requieren ayuno de 12 horas. En realidad, solo algunos estudios —como glucosa, perfil lipídico o triglicéridos— lo necesitan.',
      'La regla general es entre 8 y 12 horas de ayuno, pudiendo beber agua. Evita alcohol, comidas grasas y ejercicio intenso el día previo si tu médico lo indica.',
      'Consulta siempre la preparación específica de cada examen en nuestro catálogo o con nuestro equipo antes de la toma de muestra.',
    ],
  },
  {
    slug: 'perfil-lipidico-colesterol',
    titulo: 'Perfil lipídico: entiende tu colesterol y triglicéridos',
    resumen: 'Qué significan LDL, HDL y triglicéridos, y por qué son clave en la prevención cardiovascular.',
    categoria: 'Química sanguínea',
    tiempoLectura: '10 min',
    fecha: 'Abril 2026',
    destacado: true,
    parrafos: [
      'El perfil lipídico evalúa el colesterol total, LDL (colesterol “malo”), HDL (colesterol “bueno”) y triglicéridos. Es esencial en la evaluación del riesgo cardiovascular.',
      'Valores elevados de LDL y triglicéridos pueden asociarse a mayor riesgo de enfermedad cardíaca. El HDL, en cambio, tiene un rol protector cuando se encuentra en rangos adecuados.',
      'Este examen generalmente requiere ayuno de 10 a 12 horas. Los resultados deben interpretarse siempre junto a tu médico, considerando edad, antecedentes y otros factores de riesgo.',
    ],
  },
  {
    slug: 'glucosa-ayunas',
    titulo: 'Glucosa en ayunas: detección temprana de diabetes',
    resumen: 'Por qué se mide la glucosa en ayunas y qué valores requieren seguimiento médico.',
    categoria: 'Química sanguínea',
    tiempoLectura: '7 min',
    fecha: 'Marzo 2026',
    parrafos: [
      'La glucosa en ayunas mide la concentración de azúcar en sangre tras un período sin alimentos. Es una herramienta básica para detectar diabetes mellitus y prediabetes.',
      'Se recomienda ayuno de 8 a 12 horas. Factores como estrés, infecciones recientes o ciertos medicamentos pueden influir en el resultado.',
      'Un valor fuera de rango no significa diagnóstico definitivo: tu médico puede solicitar pruebas complementarias como hemoglobina glicosilada (HbA1c).',
    ],
  },
  {
    slug: 'resultados-online-seguros',
    titulo: 'Cómo consultar tus resultados online de forma segura',
    resumen: 'Guía para usar el portal de pacientes de Genotipia y proteger tu información clínica.',
    categoria: 'Pacientes',
    tiempoLectura: '5 min',
    fecha: 'Marzo 2026',
    parrafos: [
      'Genotipia ofrece un portal de resultados donde puedes consultar e imprimir tus informes usando el código único de tu orden.',
      'Guarda tu código de forma privada y no lo compartas por canales inseguros. Si detectas algún error en tus datos, contacta al laboratorio de inmediato.',
      'Los informes publicados han sido validados y firmados electrónicamente por nuestro bioquímico regente.',
    ],
  },
  {
    slug: 'salud-ocupacional-empresas',
    titulo: 'Salud ocupacional: exámenes para empresas',
    resumen: 'Qué incluye un programa de salud laboral y cómo Genotipia apoya a las organizaciones.',
    categoria: 'Empresas',
    tiempoLectura: '9 min',
    fecha: 'Febrero 2026',
    parrafos: [
      'Los programas de salud ocupacional incluyen exámenes de ingreso, periódicos y de retiro, adaptados al riesgo de cada puesto de trabajo.',
      'Genotipia ofrece convenios corporativos con facturación personalizada, coordinación de tomas de muestra y entrega de informes en plazos acordados.',
      'Contáctanos por WhatsApp o correo para diseñar un programa a la medida de tu empresa.',
    ],
  },
];

export function obtenerArticuloPorSlug(slug: string): BlogArticulo | undefined {
  return BLOG_ARTICULOS.find(a => a.slug === slug);
}

export function obtenerArticulosDestacados(limite = 3): BlogArticulo[] {
  return BLOG_ARTICULOS.filter(a => a.destacado).slice(0, limite);
}
