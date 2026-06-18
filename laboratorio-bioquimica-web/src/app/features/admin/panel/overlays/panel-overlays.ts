import { Component, ViewEncapsulation, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PanelNotifyService } from '../panel-notify.service';

@Component({
  selector: 'app-panel-overlays',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './panel-overlays.html',
  styleUrl: '../panel.scss',
  encapsulation: ViewEncapsulation.None
})
export class PanelOverlaysComponent {
  notify = inject(PanelNotifyService);
}
