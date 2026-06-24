export function labelMetodoPago(metodo: string | null | undefined): string {
  const map: Record<string, string> = {
    EFECTIVO: 'Efectivo',
    TRANSFERENCIA: 'Transferencia',
    TARJETA: 'Tarjeta',
    QR: 'QR'
  };
  return metodo ? (map[metodo] || metodo) : '';
}

export function tituloPalabras(texto: string): string {
  if (!texto) return '';
  return texto.trim().split(/\s+/).map(p => p.charAt(0).toUpperCase() + p.slice(1).toLowerCase()).join(' ');
}

export function objectKeys(obj: Record<string, unknown> | null | undefined): string[] {
  return obj ? Object.keys(obj) : [];
}

export function formatearVariacion(pct: number): string {
  const signo = pct > 0 ? '+' : '';
  return `${signo}${pct}%`;
}

export function alturaBarra(valor: number, maximo: number): number {
  if (!maximo || valor <= 0) return 4;
  return Math.max(8, Math.round((valor / maximo) * 100));
}

export interface LineChartGeometry {
  lineA: string;
  lineB: string;
  areaA: string;
  labels: string[];
  maxValue: number;
}

export function buildDualLineChart(
  valuesA: number[],
  valuesB: number[],
  labels: string[],
  width = 320,
  height = 140,
  padding = 12
): LineChartGeometry {
  const maxValue = Math.max(...valuesA, ...valuesB, 1);
  const innerW = width - padding * 2;
  const innerH = height - padding * 2;
  const count = Math.max(valuesA.length, valuesB.length, 1);
  const step = count > 1 ? innerW / (count - 1) : 0;

  const toPoints = (values: number[]) =>
    values.map((value, index) => {
      const x = padding + index * step;
      const y = padding + innerH * (1 - value / maxValue);
      return { x, y };
    });

  const toPath = (points: { x: number; y: number }[]) =>
    points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');

  const toArea = (points: { x: number; y: number }[]) => {
    if (!points.length) return '';
    const baseY = padding + innerH;
    const line = points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
    const last = points[points.length - 1];
    const first = points[0];
    return `${line} L ${last.x} ${baseY} L ${first.x} ${baseY} Z`;
  };

  const pointsA = toPoints(valuesA);
  const pointsB = toPoints(valuesB);

  return {
    lineA: toPath(pointsA),
    lineB: toPath(pointsB),
    areaA: toArea(pointsA),
    labels,
    maxValue
  };
}
