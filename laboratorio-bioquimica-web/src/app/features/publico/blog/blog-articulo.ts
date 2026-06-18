import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { obtenerArticuloPorSlug, BlogArticulo } from './blog-articles.data';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';

@Component({
  selector: 'app-blog-articulo',
  standalone: true,
  imports: [CommonModule, RouterLink, PublicNavbarComponent],
  templateUrl: './blog-articulo.html',
  styleUrl: './blog-articulo.scss',
})
export class BlogArticuloComponent {
  private route = inject(ActivatedRoute);

  readonly articulo: BlogArticulo | undefined = obtenerArticuloPorSlug(
    this.route.snapshot.paramMap.get('slug') ?? ''
  );
}
