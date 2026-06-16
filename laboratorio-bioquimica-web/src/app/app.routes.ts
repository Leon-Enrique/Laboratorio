import { Routes } from '@angular/router';
import { InicioComponent } from './features/publico/inicio/inicio';
import { ResultadosPacienteComponent } from './features/publico/resultados-paciente/resultados-paciente';
import { LoginComponent } from './features/auth/login/login';
import { PanelAdminComponent } from './features/admin/panel/panel';
import { BlogListComponent } from './features/publico/blog/blog-list';
import { BlogArticuloComponent } from './features/publico/blog/blog-articulo';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', component: InicioComponent },
  { path: 'blog', component: BlogListComponent },
  { path: 'blog/:slug', component: BlogArticuloComponent },
  { path: 'resultados', component: ResultadosPacienteComponent },
  { path: 'login', component: LoginComponent },
  { 
    path: 'admin', 
    component: PanelAdminComponent, 
    canActivate: [authGuard] 
  },
  { path: '**', redirectTo: '' }
];
