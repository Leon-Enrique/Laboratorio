import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BLOG_ARTICULOS } from './blog-articles.data';
import { PublicNavbarComponent } from '../../../shared/components/public-navbar/public-navbar';

@Component({
  selector: 'app-blog-list',
  standalone: true,
  imports: [CommonModule, RouterLink, PublicNavbarComponent],
  templateUrl: './blog-list.html',
  styleUrl: './blog-list.scss',
})
export class BlogListComponent {
  readonly articulos = BLOG_ARTICULOS;
}
