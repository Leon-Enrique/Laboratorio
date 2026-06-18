import { Component, ViewEncapsulation, computed, inject, signal, viewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';
import { PanelNavId, PanelTabId } from './panel.models';
import { PanelNotifyService } from './panel-notify.service';
import { PanelOverlaysComponent } from './overlays/panel-overlays';
import { PanelOrdenesTabComponent } from './tabs/panel-ordenes-tab/panel-ordenes-tab';
import { PanelInventarioTabComponent } from './tabs/panel-inventario-tab/panel-inventario-tab';
import { PanelReportesTabComponent } from './tabs/panel-reportes-tab/panel-reportes-tab';
import { PanelHistorialTabComponent } from './tabs/panel-historial-tab/panel-historial-tab';
import { PanelCatalogoTabComponent } from './tabs/panel-catalogo-tab/panel-catalogo-tab';
import { PanelAnalisisTabComponent } from './tabs/panel-analisis-tab/panel-analisis-tab';

interface BreadcrumbItem {
  label: string;
}

@Component({
  selector: 'app-panel-admin',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    BrandLogoComponent,
    PanelOverlaysComponent,
    PanelOrdenesTabComponent,
    PanelInventarioTabComponent,
    PanelReportesTabComponent,
    PanelHistorialTabComponent,
    PanelCatalogoTabComponent,
    PanelAnalisisTabComponent
  ],
  providers: [PanelNotifyService],
  templateUrl: './panel.html',
  styleUrl: './panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelAdminComponent {
  private auth = inject(AuthService);
  private router = inject(Router);

  readonly labNombre = "Laboratorio 'Genotipia'";
  readonly labDireccion =
    'Av. Japón N° 3555, 3er. Anillo Externo — Diagonal entrada Emergencias Hospital Japonés';
  readonly labTelefono = '75548529';

  nombreUsuario = this.auth.currentUser;
  rolUsuario = this.auth.currentRole;

  navActivo = signal<PanelNavId>('ordenes-lista');
  tabActiva = signal<PanelTabId>('ordenes');
  sidebarColapsado = signal(false);
  sidebarMovilAbierto = signal(false);
  gruposExpandidos = signal<Record<string, boolean>>({
    ordenes: true,
    reportes: true,
    config: true
  });

  ordenesTab = viewChild(PanelOrdenesTabComponent);
  inventarioTab = viewChild(PanelInventarioTabComponent);
  catalogoTab = viewChild(PanelCatalogoTabComponent);
  analisisTab = viewChild(PanelAnalisisTabComponent);

  readonly vistaOrdenes = computed<'lista' | 'nueva' | 'cobros_pendiente'>(() => {
    const nav = this.navActivo();
    if (nav === 'ordenes-nueva') return 'nueva';
    if (nav === 'ordenes-cobros') return 'cobros_pendiente';
    return 'lista';
  });

  tituloPagina = computed(() => {
    const map: Record<PanelNavId, string> = {
      'ordenes-lista': 'Cola de trabajo',
      'ordenes-nueva': 'Nueva orden',
      'ordenes-cobros': 'Cobros pendientes',
      inventario: 'Inventario y planificación',
      'reportes-stats': 'Reportes y estadísticas',
      'reportes-paciente': 'Historial por paciente',
      'config-catalogo': 'Catálogo de exámenes',
      'config-catalogo-nuevo': 'Nuevo análisis'
    };
    return map[this.navActivo()] ?? 'Panel';
  });

  breadcrumbs = computed<BreadcrumbItem[]>(() => {
    const nav = this.navActivo();
    const base: BreadcrumbItem[] = [{ label: 'Panel' }];

    if (nav.startsWith('ordenes')) {
      return [...base, { label: 'Órdenes' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('reportes')) {
      return [...base, { label: 'Reportes' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('config-catalogo')) {
      return [...base, { label: 'Configuración' }, { label: this.tituloPagina() }];
    }
    if (nav === 'inventario') {
      return [...base, { label: 'Laboratorio' }, { label: this.tituloPagina() }];
    }
    return base;
  });

  navegar(nav: PanelNavId) {
    this.navActivo.set(nav);
    this.tabActiva.set(this.tabDesdeNav(nav));
    this.sidebarMovilAbierto.set(false);

    if (nav.startsWith('ordenes')) {
      this.gruposExpandidos.update(g => ({ ...g, ordenes: true }));
    }
    if (nav.startsWith('reportes')) {
      this.gruposExpandidos.update(g => ({ ...g, reportes: true }));
    }
    if (nav.startsWith('config-catalogo')) {
      this.gruposExpandidos.update(g => ({ ...g, config: true }));
    }

    setTimeout(() => this.aplicarVistaNav(nav), 0);
  }

  onGrupoClick(grupo: string, navPorDefecto: PanelNavId) {
    if (this.sidebarColapsado()) {
      this.navegar(navPorDefecto);
      return;
    }
    this.toggleGrupo(grupo);
  }

  toggleGrupo(grupo: string) {
    if (this.sidebarColapsado()) return;
    this.gruposExpandidos.update(g => ({ ...g, [grupo]: !g[grupo] }));
  }

  toggleSidebar() {
    if (typeof window !== 'undefined' && window.innerWidth <= 900) {
      this.sidebarMovilAbierto.update(v => !v);
      return;
    }
    this.sidebarColapsado.update(v => !v);
  }

  cerrarSidebarMovil() {
    this.sidebarMovilAbierto.set(false);
  }

  esNavActivo(nav: PanelNavId): boolean {
    return this.navActivo() === nav;
  }

  grupoActivo(grupo: string): boolean {
    const nav = this.navActivo();
    if (grupo === 'ordenes') return nav.startsWith('ordenes');
    if (grupo === 'reportes') return nav.startsWith('reportes');
    if (grupo === 'config') return nav.startsWith('config-catalogo');
    return false;
  }

  onInventarioChanged() {
    this.inventarioTab()?.cargarDatosInventario();
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/']);
  }

  private tabDesdeNav(nav: PanelNavId): PanelTabId {
    if (nav.startsWith('ordenes')) return 'ordenes';
    if (nav === 'reportes-stats') return 'reportes';
    if (nav === 'reportes-paciente') return 'historial';
    if (nav === 'config-catalogo') return 'config-catalogo';
    if (nav === 'config-catalogo-nuevo') return 'config-analisis';
    return 'inventario';
  }

  private aplicarVistaNav(nav: PanelNavId) {
    if (nav.startsWith('ordenes')) {
      const vista =
        nav === 'ordenes-nueva' ? 'nueva' : nav === 'ordenes-cobros' ? 'cobros_pendiente' : 'lista';
      this.ordenesTab()?.aplicarVista(vista);
      this.ordenesTab()?.refresh();
      return;
    }
    if (nav === 'inventario') {
      this.inventarioTab()?.cargarDatosInventario();
    }
    if (nav === 'config-catalogo') {
      this.catalogoTab()?.cargarExamenesCatalogo();
    }
    if (nav === 'config-catalogo-nuevo') {
      this.analisisTab()?.refresh();
    }
  }
}
