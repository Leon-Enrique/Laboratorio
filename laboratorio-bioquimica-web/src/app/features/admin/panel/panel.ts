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
import { PanelMermasTabComponent } from './tabs/panel-mermas-tab/panel-mermas-tab';
import { PanelSugerenciasCompraTabComponent } from './tabs/panel-sugerencias-compra-tab/panel-sugerencias-compra-tab';
import { PanelOrdenesPedidoTabComponent } from './tabs/panel-ordenes-pedido-tab/panel-ordenes-pedido-tab';
import { PanelProveedoresTabComponent } from './tabs/panel-proveedores-tab/panel-proveedores-tab';
import { PanelReportesTabComponent } from './tabs/panel-reportes-tab/panel-reportes-tab';
import { PanelHistorialTabComponent } from './tabs/panel-historial-tab/panel-historial-tab';
import { PanelCatalogoTabComponent } from './tabs/panel-catalogo-tab/panel-catalogo-tab';
import { PanelDestacadosTabComponent } from './tabs/panel-destacados-tab/panel-destacados-tab';
import { PanelAnalisisTabComponent } from './tabs/panel-analisis-tab/panel-analisis-tab';
import { PanelFacturasTabComponent } from './tabs/panel-facturas-tab/panel-facturas-tab';

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
    PanelMermasTabComponent,
    PanelSugerenciasCompraTabComponent,
    PanelOrdenesPedidoTabComponent,
    PanelProveedoresTabComponent,
    PanelReportesTabComponent,
    PanelHistorialTabComponent,
    PanelCatalogoTabComponent,
    PanelDestacadosTabComponent,
    PanelAnalisisTabComponent,
    PanelFacturasTabComponent
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
  filtroSugerenciaReactivoId = signal<number | null>(null);
  gruposExpandidos = signal<Record<string, boolean>>({
    ordenes: true,
    inventario: true,
    compras: true,
    reportes: true,
    config: true
  });

  ordenesTab = viewChild(PanelOrdenesTabComponent);
  inventarioTab = viewChild(PanelInventarioTabComponent);
  mermasTab = viewChild(PanelMermasTabComponent);
  sugerenciasTab = viewChild(PanelSugerenciasCompraTabComponent);
  ordenesPedidoTab = viewChild(PanelOrdenesPedidoTabComponent);
  proveedoresTab = viewChild(PanelProveedoresTabComponent);
  catalogoTab = viewChild(PanelCatalogoTabComponent);
  destacadosTab = viewChild(PanelDestacadosTabComponent);
  analisisTab = viewChild(PanelAnalisisTabComponent);
  facturasTab = viewChild(PanelFacturasTabComponent);

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
      'ordenes-facturas': 'Facturas y comprobantes',
      'inventario-insumos': 'Control de insumos',
      'inventario-mermas': 'Historial de mermas',
      'compras-sugerencias': 'Sugerencias de compra',
      'compras-proveedores': 'Catálogo de proveedores',
      'compras-ordenes-pedido': 'Órdenes de pedido',
      'reportes-stats': 'Reportes y estadísticas',
      'reportes-paciente': 'Historial por paciente',
      'config-catalogo': 'Catálogo de pruebas',
      'config-catalogo-nuevo': 'Nueva prueba',
      'config-destacados': 'Destacados del inicio'
    };
    return map[this.navActivo()] ?? 'Panel';
  });

  breadcrumbs = computed<BreadcrumbItem[]>(() => {
    const nav = this.navActivo();
    const base: BreadcrumbItem[] = [{ label: 'Panel' }];

    if (nav.startsWith('ordenes')) {
      return [...base, { label: 'Órdenes' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('inventario')) {
      return [...base, { label: 'Inventario' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('compras')) {
      return [...base, { label: 'Compras' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('reportes')) {
      return [...base, { label: 'Reportes' }, { label: this.tituloPagina() }];
    }
    if (nav.startsWith('config-catalogo') || nav === 'config-destacados') {
      return [...base, { label: 'Examen' }, { label: this.tituloPagina() }];
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
    if (nav.startsWith('inventario')) {
      this.gruposExpandidos.update(g => ({ ...g, inventario: true }));
    }
    if (nav.startsWith('compras')) {
      this.gruposExpandidos.update(g => ({ ...g, compras: true }));
    }
    if (nav.startsWith('reportes')) {
      this.gruposExpandidos.update(g => ({ ...g, reportes: true }));
    }
    if (nav.startsWith('config-catalogo') || nav === 'config-destacados') {
      this.gruposExpandidos.update(g => ({ ...g, config: true }));
    }

    setTimeout(() => this.aplicarVistaNav(nav), 0);
  }

  navegarSugerenciaCompra(reactivoId: number) {
    this.filtroSugerenciaReactivoId.set(reactivoId);
    this.navegar('compras-sugerencias');
  }

  limpiarFiltroSugerencia() {
    this.filtroSugerenciaReactivoId.set(null);
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
    if (grupo === 'inventario') return nav.startsWith('inventario');
    if (grupo === 'compras') return nav.startsWith('compras');
    if (grupo === 'reportes') return nav.startsWith('reportes');
    if (grupo === 'config') return nav.startsWith('config-catalogo') || nav === 'config-destacados';
    return false;
  }

  onInventarioChanged() {
    this.inventarioTab()?.cargarDatosInventario();
    this.sugerenciasTab()?.cargarSugerencias();
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/']);
  }

  private tabDesdeNav(nav: PanelNavId): PanelTabId {
    if (nav === 'ordenes-facturas') return 'ordenes-facturas';
    if (nav.startsWith('ordenes')) return 'ordenes';
    if (nav === 'inventario-insumos') return 'inventario-insumos';
    if (nav === 'inventario-mermas') return 'inventario-mermas';
    if (nav === 'compras-sugerencias') return 'compras-sugerencias';
    if (nav === 'compras-proveedores') return 'compras-proveedores';
    if (nav === 'compras-ordenes-pedido') return 'compras-ordenes-pedido';
    if (nav === 'reportes-stats') return 'reportes';
    if (nav === 'reportes-paciente') return 'historial';
    if (nav === 'config-catalogo') return 'config-catalogo';
    if (nav === 'config-catalogo-nuevo') return 'config-analisis';
    if (nav === 'config-destacados') return 'config-destacados';
    return 'inventario-insumos';
  }

  private aplicarVistaNav(nav: PanelNavId) {
    if (nav === 'ordenes-facturas') {
      this.facturasTab()?.cargarComprobantes();
      return;
    }
    if (nav.startsWith('ordenes')) {
      const vista =
        nav === 'ordenes-nueva' ? 'nueva' : nav === 'ordenes-cobros' ? 'cobros_pendiente' : 'lista';
      this.ordenesTab()?.aplicarVista(vista);
      this.ordenesTab()?.refresh();
      return;
    }
    if (nav === 'inventario-insumos') {
      this.inventarioTab()?.cargarDatosInventario();
    }
    if (nav === 'inventario-mermas') {
      this.mermasTab()?.cargarMermas();
    }
    if (nav === 'compras-sugerencias') {
      this.sugerenciasTab()?.cargarSugerencias();
    }
    if (nav === 'compras-proveedores') {
      this.proveedoresTab()?.cargarProveedores();
    }
    if (nav === 'compras-ordenes-pedido') {
      this.ordenesPedidoTab()?.cargarDatos();
    }
    if (nav === 'config-catalogo') {
      this.catalogoTab()?.cargarExamenesCatalogo();
    }
    if (nav === 'config-destacados') {
      this.destacadosTab()?.cargarExamenes();
      this.destacadosTab()?.cargarMasBuscados();
    }
    if (nav === 'config-catalogo-nuevo') {
      this.analisisTab()?.refresh();
    }
  }
}
