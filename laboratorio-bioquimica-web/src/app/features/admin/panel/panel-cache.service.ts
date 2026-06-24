import { Injectable, inject } from '@angular/core';
import { Observable, of, tap } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { Examen, Proveedor } from './panel.models';

const TTL_MS = 5 * 60 * 1000;

@Injectable({ providedIn: 'root' })
export class PanelCacheService {
  private api = inject(ApiService);

  private examenesPanel: Examen[] | null = null;
  private examenesPanelAt = 0;
  private proveedores: Proveedor[] | null = null;
  private proveedoresAt = 0;

  examenesParaPanel(force = false): Observable<Examen[]> {
    if (!force && this.examenesPanel && Date.now() - this.examenesPanelAt < TTL_MS) {
      return of(this.examenesPanel);
    }
    return this.api.get<Examen[]>('/examenes/admin-lista?ligero=true').pipe(
      tap(data => {
        this.examenesPanel = data;
        this.examenesPanelAt = Date.now();
      })
    );
  }

  proveedoresLista(force = false): Observable<Proveedor[]> {
    if (!force && this.proveedores && Date.now() - this.proveedoresAt < TTL_MS) {
      return of(this.proveedores);
    }
    return this.api.get<Proveedor[]>('/inventario/proveedores').pipe(
      tap(data => {
        this.proveedores = data;
        this.proveedoresAt = Date.now();
      })
    );
  }

  invalidarExamenes() {
    this.examenesPanel = null;
    this.examenesPanelAt = 0;
  }

  invalidarProveedores() {
    this.proveedores = null;
    this.proveedoresAt = 0;
  }

  invalidarInventario() {
    this.invalidarProveedores();
  }
}
