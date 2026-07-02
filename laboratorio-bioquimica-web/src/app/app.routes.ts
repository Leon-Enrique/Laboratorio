import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/publico/inicio/inicio').then(m => m.InicioComponent),
  },
  {
    path: 'examenes',
    loadComponent: () =>
      import('./features/publico/catalogo-examenes/catalogo-examenes').then(
        m => m.CatalogoExamenesComponent
      ),
  },
  {
    path: 'adn',
    loadComponent: () =>
      import('./features/publico/pruebas-adn/pruebas-adn').then(m => m.PruebasAdnComponent),
  },
  {
    path: 'blog',
    loadComponent: () =>
      import('./features/publico/blog/blog-list').then(m => m.BlogListComponent),
  },
  {
    path: 'blog/:slug',
    loadComponent: () =>
      import('./features/publico/blog/blog-articulo').then(m => m.BlogArticuloComponent),
  },
  {
    path: 'resultados',
    loadComponent: () =>
      import('./features/publico/resultados-paciente/resultados-paciente').then(
        m => m.ResultadosPacienteComponent
      ),
  },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then(m => m.LoginComponent),
  },
  {
    path: 'admin',
    loadComponent: () =>
      import('./features/admin/panel/panel').then(m => m.PanelAdminComponent),
    canActivate: [authGuard],
  },
  { path: '**', redirectTo: '' },
];
