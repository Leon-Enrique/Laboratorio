import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { obtenerArticuloPorSlug, BlogArticulo } from './blog-articles.data';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';

@Component({
  selector: 'app-blog-articulo',
  standalone: true,
  imports: [CommonModule, RouterLink, BrandLogoComponent],
  templateUrl: './blog-articulo.html',
  styleUrl: './blog-articulo.scss',
})
export class BlogArticuloComponent {
  private route = inject(ActivatedRoute);

  readonly articulo: BlogArticulo | undefined = obtenerArticuloPorSlug(
    this.route.snapshot.paramMap.get('slug') ?? ''
  );
}
