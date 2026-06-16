import { Injectable, inject, signal } from '@angular/core';
import { ApiService } from './api.service';
import { Observable, tap } from 'rxjs';

interface TokenResponse {
  access_token: string;
  token_type: string;
  rol: string;
  nombre: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private api = inject(ApiService);
  
  // Signals reactivos para el estado de autenticación
  currentUser = signal<string | null>(localStorage.getItem('nombre'));
  currentRole = signal<string | null>(localStorage.getItem('rol'));
  isAuthenticated = signal<boolean>(!!localStorage.getItem('token'));

  login(email: string, password: string): Observable<TokenResponse> {
    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);

    return this.api.postForm<TokenResponse>('/auth/login', body).pipe(
      tap(res => {
        localStorage.setItem('token', res.access_token);
        localStorage.setItem('rol', res.rol);
        localStorage.setItem('nombre', res.nombre);
        
        // Actualizar signals
        this.currentUser.set(res.nombre);
        this.currentRole.set(res.rol);
        this.isAuthenticated.set(true);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('rol');
    localStorage.removeItem('nombre');
    
    this.currentUser.set(null);
    this.currentRole.set(null);
    this.isAuthenticated.set(false);
  }

  hasRole(roles: string[]): boolean {
    const rol = this.currentRole();
    return rol ? roles.includes(rol) : false;
  }
}
