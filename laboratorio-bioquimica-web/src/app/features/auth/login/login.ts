import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, BrandLogoComponent],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent {
  private auth = inject(AuthService);
  private router = inject(Router);

  email = signal<string>('');
  password = signal<string>('');
  cargando = signal<boolean>(false);
  error = signal<string | null>(null);

  realizarLogin() {
    const mail = this.email().trim();
    const pass = this.password().trim();

    if (!mail || !pass) return;

    this.cargando.set(true);
    this.error.set(null);

    this.auth.login(mail, pass).subscribe({
      next: () => {
        this.cargando.set(false);
        this.router.navigate(['/admin']);
      },
      error: (err) => {
        console.error('Error de login:', err);
        this.error.set('Credenciales incorrectas o usuario inactivo. Por favor verifique.');
        this.cargando.set(false);
      }
    });
  }
}
