import { Component, HostListener, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { BrandLogoComponent } from '../brand-logo/brand-logo';

@Component({
  selector: 'app-public-navbar',
  standalone: true,
  imports: [RouterLink, BrandLogoComponent],
  templateUrl: './public-navbar.html',
  styleUrl: './public-navbar.scss',
})
export class PublicNavbarComponent {
  /** En la landing usa anchors (#); en otras páginas usa routerLink con fragment */
  anchorMode = input(false);

  menuAbierto = signal(false);
  readonly whatsappUrl = 'https://wa.me/59175548529';

  toggleMenu(): void {
    this.menuAbierto.update(v => !v);
    this.syncBodyScroll();
  }

  cerrarMenu(): void {
    if (!this.menuAbierto()) return;
    this.menuAbierto.set(false);
    this.syncBodyScroll();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.cerrarMenu();
  }

  private syncBodyScroll(): void {
    document.body.style.overflow = this.menuAbierto() ? 'hidden' : '';
  }
}
