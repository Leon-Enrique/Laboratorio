import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BLOG_ARTICULOS } from './blog-articles.data';
import { BrandLogoComponent } from '../../../shared/components/brand-logo/brand-logo';

@Component({
  selector: 'app-blog-list',
  standalone: true,
  imports: [CommonModule, RouterLink, BrandLogoComponent],
  templateUrl: './blog-list.html',
  styleUrl: './blog-list.scss',
})
export class BlogListComponent {
  readonly articulos = BLOG_ARTICULOS;
}
