export const TIPOS_PRUEBA = ['Laboratorio', 'Imagenología', 'Patología', 'Otros'] as const;

export const GRUPOS_PRUEBA = [
  'BIOQUIMICA',
  'HEMATOLOGIA',
  'BACTERIOLOGIA',
  'INMUNOLOGIA',
  'HORMONAS',
  'ORINA',
  'COPROLOGIA',
  'GENETICA',
  'UROANALISIS',
  'OTROS'
] as const;

export const MATERIALES_MUESTRA = [
  'Sangre',
  'Suero',
  'Plasma',
  'Orina',
  'Heces',
  'Esputo',
  'Hisopado',
  'LCR',
  'Otros'
] as const;

export const ESTADOS_PRUEBA = ['Activo', 'Inactivo'] as const;

export const TIPOS_RESULTADO = ['Numero', 'Texto', 'Texto Area', 'Fecha', 'Hora'] as const;

export const UNIDADES_MEDIDA = [
  '',
  'mg/dL',
  'g/dL',
  'mmol/L',
  'UI/L',
  'U/L',
  'mEq/L',
  '%',
  'ng/mL',
  'pg/mL',
  'µg/dL',
  'cel/µL',
  'fL',
  'pg',
  'g/L',
  'mIU/L',
  'µIU/mL',
  'copias/mL',
  'mm/h',
  'seg',
  'ratio',
  'Índice',
  'N/A'
] as const;

export type TipoPrueba = (typeof TIPOS_PRUEBA)[number];
export type TipoResultado = (typeof TIPOS_RESULTADO)[number];

/** El nombre del análisis ya aparece como título del bloque; no se pide en el formulario. */
export const PARAMETROS_RESULTADO_OCULTOS = ['Nombre'] as const;

export function esParametroResultadoVisible(nombre: string): boolean {
  const n = nombre.trim().toLowerCase();
  return !PARAMETROS_RESULTADO_OCULTOS.some(p => p.toLowerCase() === n);
}

export function examenTieneFormularioResultados(
  parametros?: readonly { nombre: string }[] | null
): boolean {
  if (!parametros?.length) return false;
  return parametros.some(p => esParametroResultadoVisible(p.nombre));
}

export function examenFaltaCrearResultados(
  parametros?: readonly { nombre: string }[] | null
): boolean {
  return !examenTieneFormularioResultados(parametros);
}

export function normalizarTipoResultado(tipo?: string | null): TipoResultado {
  if (tipo && (TIPOS_RESULTADO as readonly string[]).includes(tipo)) {
    return tipo as TipoResultado;
  }
  return 'Numero';
}

/** step para input numérico según decimales configurados */
export function stepDecimales(decimales?: number | null): string {
  const d = decimales ?? 2;
  if (d <= 0) return '1';
  return `0.${'0'.repeat(Math.max(0, d - 1))}1`;
}
