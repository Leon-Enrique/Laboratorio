import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    // Permitir acceso solo si es admin o bioquímico
    if (authService.hasRole(['admin', 'bioquimico'])) {
      return true;
    }
  }
  
  router.navigate(['/login']);
  return false;
};
