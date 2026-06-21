export interface ExamenPublico {
  id: number;
  nombre: string;
  descripcion: string;
  preparacion: string;
  precio_bob: number;
  tiempo_entrega_horas: number;
  destacado?: boolean;
  titulo_destacado?: string | null;
  subtitulo_destacado?: string | null;
  descripcion_destacado?: string | null;
  orden_destacado?: number | null;
  grupo?: string | null;
  material_muestra?: string | null;
  codigo_abrev?: string | null;
  tipo?: string | null;
}

/** Áreas del sidebar — estilo catálogo clínico */
export const AREAS_DIAGNOSTICAS: CategoriaFiltro[] = [
  { id: 'todos', label: 'Todas las áreas', keywords: [] },
  { id: 'quimica', label: 'Bioquímica Clínica', keywords: [] },
  { id: 'genetica', label: 'Genética Molecular (Genética)', keywords: [] },
  { id: 'hematologia', label: 'Hematología', keywords: [] },
  { id: 'serologia', label: 'Inmunología', keywords: [] },
  { id: 'micro', label: 'Microbiología', keywords: [] },
  { id: 'especiales', label: 'Toxicología', keywords: [] },
  { id: 'hormonas', label: 'Chequeos Preventivos', keywords: [] }
];

export const TIPOS_MUESTRA_FILTRO = [
  { id: 'sangre', label: 'Sangre', keywords: ['sangre', 'suero', 'plasma', 'tubo'] },
  { id: 'saliva', label: 'Saliva', keywords: ['saliva'] },
  { id: 'orina', label: 'Orina', keywords: ['orina', 'uro'] },
  { id: 'heces', label: 'Heces / copro', keywords: ['heces', 'copro', 'parasit'] },
  { id: 'otros', label: 'Otros', keywords: ['hisopado', 'esputo', 'lcr', 'otros'] }
] as const;

const ICONOS_AREA: Record<string, string> = {
  quimica: '⚗️',
  genetica: '🧬',
  hematologia: '🔬',
  serologia: '🛡️',
  micro: '🦠',
  molecular: '🧬',
  uro: '💧',
  hormonas: '❤️',
  especiales: '⚠️',
  todos: '🧪'
};

export interface CategoriaFiltro {
  id: string;
  label: string;
  keywords: string[];
}

/** Especialidades del catálogo (sin "Todos") — estilo laboratorio clínico */
export const CATEGORIAS_CATALOGO: CategoriaFiltro[] = [
  {
    id: 'hematologia',
    label: 'Hematología',
    keywords: ['hemograma', 'hemat', 'hemoglobina', 'hematocrito', 'plaqueta', 'coagul', 'grupo sangu', 'vsg', 'reticuloc']
  },
  {
    id: 'serologia',
    label: 'Serología e inmunología',
    keywords: ['serolog', 'anticuerp', 'igg', 'igm', 'vih', 'hepatitis', 'vdrl', 'rpr', 'chagas', 'dengue', 'covid', 'inmunoglob']
  },
  {
    id: 'hormonas',
    label: 'Hormonas',
    keywords: ['hormon', 'tsh', 'tiro', 'cortisol', 'insulin', 'progester', 'testoster', 'estradiol', 'prolactin', 'hcg', 'embarazo']
  },
  {
    id: 'quimica',
    label: 'Química sanguínea',
    keywords: [
      'glucosa', 'colesterol', 'lipíd', 'lipid', 'renal', 'hepát', 'hepat', 'creatinina', 'urea',
      'química', 'quimica', 'triglicer', 'hdl', 'ldl', 'perfil', 'ácido úrico', 'acido urico', 'electrolit'
    ]
  },
  {
    id: 'genetica',
    label: 'Genética y ADN',
    keywords: ['adn', 'paternidad', 'maternidad', 'hermanos', 'filiación', 'filiacion', 'linaje', 'parentesco']
  },
  {
    id: 'molecular',
    label: 'Biología molecular',
    keywords: ['pcr', 'molecular', 'genét', 'genet', 'hpv', 'covid']
  },
  {
    id: 'uro',
    label: 'Uroanálisis',
    keywords: ['orina', 'uro', 'urocult', 'orina completa', 'microalbumin']
  },
  {
    id: 'micro',
    label: 'Bacteriología y parasitología',
    keywords: ['cultivo', 'bacter', 'parasit', 'coprocult', 'hemocult', 'baciloscop']
  },
  {
    id: 'especiales',
    label: 'Exámenes especiales',
    keywords: []
  }
];

export const CATEGORIAS_EXAMEN: CategoriaFiltro[] = [
  { id: 'todos', label: 'Todos', keywords: [] },
  ...CATEGORIAS_CATALOGO.filter(c => c.id !== 'especiales')
];

export const MAX_DESTACADOS_INICIO = 6;

export function tituloDestacado(ex: ExamenPublico): string {
  const custom = ex.titulo_destacado?.trim();
  return custom || ex.nombre;
}

export function subtituloDestacado(ex: ExamenPublico): string | null {
  const custom = ex.subtitulo_destacado?.trim();
  return custom || null;
}

export function descripcionDestacado(ex: ExamenPublico): string {
  const custom = ex.descripcion_destacado?.trim();
  return custom || ex.descripcion || '';
}

export interface GrupoCatalogo {
  id: string;
  label: string;
  examenes: ExamenPublico[];
}

export interface ResumenCategoria {
  id: string;
  label: string;
  count: number;
}

export function categoriaDeExamen(ex: ExamenPublico): string {
  const texto = `${ex.nombre} ${ex.descripcion} ${ex.preparacion}`.toLowerCase();
  for (const cat of CATEGORIAS_CATALOGO) {
    if (cat.id === 'especiales') continue;
    if (cat.keywords.some(kw => texto.includes(kw))) return cat.id;
  }
  return 'especiales';
}

export function filtrarExamenesPorTexto(examenes: ExamenPublico[], query: string): ExamenPublico[] {
  const q = query.trim().toLowerCase();
  let lista = [...examenes];

  if (q) {
    lista = lista.filter(ex => textoBusquedaExamen(ex).includes(q));
  }

  return lista.sort((a, b) => a.nombre.localeCompare(b.nombre, 'es', { sensitivity: 'base' }));
}

function textoBusquedaExamen(ex: ExamenPublico): string {
  return [
    ex.nombre,
    ex.descripcion,
    ex.preparacion,
    ex.grupo,
    ex.material_muestra,
    ex.codigo_abrev,
    codigoExamen(ex)
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

export function codigoExamen(ex: ExamenPublico): string {
  if (ex.codigo_abrev?.trim()) return ex.codigo_abrev.trim().toUpperCase();
  const area = categoriaDeExamen(ex).slice(0, 3).toUpperCase();
  return `${area}-${String(ex.id).padStart(3, '0')}`;
}

export function iconoAreaExamen(ex: ExamenPublico): string {
  return ICONOS_AREA[categoriaDeExamen(ex)] || ICONOS_AREA['todos'];
}

function coincideMaterial(ex: ExamenPublico, materialIds: string[]): boolean {
  if (!materialIds.length) return true;
  const texto = `${ex.material_muestra || ''} ${ex.preparacion} ${ex.nombre} ${ex.descripcion}`.toLowerCase();
  return materialIds.some(id => {
    const filtro = TIPOS_MUESTRA_FILTRO.find(m => m.id === id);
    return filtro?.keywords.some(kw => texto.includes(kw)) ?? false;
  });
}

/** Lista plana para grid de tarjetas */
export function filtrarCatalogoGrid(
  examenes: ExamenPublico[],
  query: string,
  categoriaId: string,
  materiales: string[]
): ExamenPublico[] {
  let lista = filtrarExamenesPorTexto(examenes, query);
  if (categoriaId !== 'todos') {
    lista = lista.filter(ex => categoriaDeExamen(ex) === categoriaId);
  }
  if (materiales.length) {
    lista = lista.filter(ex => coincideMaterial(ex, materiales));
  }
  return lista;
}

/** @deprecated Usar filtrarExamenesPorTexto + agruparExamenes */
export function filtrarExamenes(
  examenes: ExamenPublico[],
  query: string,
  categoriaId: string
): ExamenPublico[] {
  let lista = filtrarExamenesPorTexto(examenes, query);
  if (categoriaId !== 'todos') {
    lista = lista.filter(ex => categoriaDeExamen(ex) === categoriaId);
  }
  return lista;
}

export function agruparExamenes(
  examenes: ExamenPublico[],
  query: string,
  categoriaFiltro: string
): GrupoCatalogo[] {
  let lista = filtrarExamenesPorTexto(examenes, query);

  if (categoriaFiltro !== 'todos') {
    lista = lista.filter(ex => categoriaDeExamen(ex) === categoriaFiltro);
  }

  const map = new Map<string, ExamenPublico[]>();
  for (const cat of CATEGORIAS_CATALOGO) {
    map.set(cat.id, []);
  }

  for (const ex of lista) {
    const cid = categoriaDeExamen(ex);
    map.get(cid)?.push(ex);
  }

  return CATEGORIAS_CATALOGO.map(cat => ({
    id: cat.id,
    label: cat.label,
    examenes: (map.get(cat.id) || []).sort((a, b) =>
      a.nombre.localeCompare(b.nombre, 'es', { sensitivity: 'base' })
    )
  })).filter(g => g.examenes.length > 0);
}

export function resumenCategorias(examenes: ExamenPublico[]): ResumenCategoria[] {
  const map = new Map<string, number>();
  for (const cat of CATEGORIAS_CATALOGO) {
    map.set(cat.id, 0);
  }
  for (const ex of examenes) {
    const cid = categoriaDeExamen(ex);
    map.set(cid, (map.get(cid) || 0) + 1);
  }
  return CATEGORIAS_CATALOGO.filter(c => (map.get(c.id) || 0) > 0).map(cat => ({
    id: cat.id,
    label: cat.label,
    count: map.get(cat.id) || 0
  }));
}
