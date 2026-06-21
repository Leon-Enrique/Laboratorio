import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';

/** Registro anónimo de búsquedas/clics en el catálogo público (fire-and-forget). */
@Injectable({ providedIn: 'root' })
export class CatalogoAnalyticsService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  /** Evita contar la misma búsqueda varias veces en la misma sesión del navegador. */
  private busquedasRegistradas = new Set<string>();
  private clicsRegistrados = new Set<number>();

  registrarBusqueda(termino: string, examenIds: number[]): void {
    const t = termino.trim().toLowerCase();
    if (t.length < 2 || !examenIds.length) return;

    const key = `${t}|${examenIds.slice(0, 8).join(',')}`;
    if (this.busquedasRegistradas.has(key)) return;
    this.busquedasRegistradas.add(key);

    this.http
      .post(`${this.baseUrl}/examenes/analytics/busqueda`, {
        termino: t,
        examen_ids: examenIds.slice(0, 20)
      })
      .subscribe({ error: () => {} });
  }

  registrarClic(examenId: number): void {
    if (this.clicsRegistrados.has(examenId)) return;
    this.clicsRegistrados.add(examenId);

    this.http
      .post(`${this.baseUrl}/examenes/analytics/clic`, { examen_id: examenId })
      .subscribe({ error: () => {} });
  }
}
