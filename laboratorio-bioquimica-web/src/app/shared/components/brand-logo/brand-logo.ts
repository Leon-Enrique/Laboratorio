import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-brand-logo',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './brand-logo.html',
  styleUrl: './brand-logo.scss'
})
export class BrandLogoComponent {
  /** Tamaño del logo: compacto para navbar, completo para login/footer */
  size = input<'compact' | 'full'>('compact');
  /** dark = fondos oscuros; light = fondos claros (tickets, PDF) */
  theme = input<'dark' | 'light'>('dark');
  /** Texto opcional junto al logo (ej. "Admin Panel") */
  suffix = input<string>('');
}
