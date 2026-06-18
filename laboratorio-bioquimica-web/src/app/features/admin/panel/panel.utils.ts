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
