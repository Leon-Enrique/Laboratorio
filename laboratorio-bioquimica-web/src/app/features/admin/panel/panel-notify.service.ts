import { Injectable, signal } from '@angular/core';

export type ToastType = 'success' | 'error' | 'info';

@Injectable()
export class PanelNotifyService {
  toast = signal<{ visible: boolean; message: string; type: ToastType }>({
    visible: false,
    message: '',
    type: 'info'
  });
  confirmVisible = signal(false);
  confirmTitle = signal('Confirmar');
  confirmMessage = signal('');

  private confirmAction: (() => void) | null = null;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  mostrarToast(message: string, type: ToastType = 'info') {
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toast.set({ visible: true, message, type });
    this.toastTimer = setTimeout(() => {
      this.toast.update(t => ({ ...t, visible: false }));
    }, 4500);
  }

  mostrarError(err: unknown, fallback: string) {
    const detail = (err as { error?: { detail?: string }; message?: string })?.error?.detail
      || (err as { message?: string })?.message
      || fallback;
    this.mostrarToast(String(detail), 'error');
  }

  pedirConfirmacion(title: string, message: string, onConfirm: () => void) {
    this.confirmTitle.set(title);
    this.confirmMessage.set(message);
    this.confirmAction = onConfirm;
    this.confirmVisible.set(true);
  }

  ejecutarConfirmacion() {
    this.confirmVisible.set(false);
    const action = this.confirmAction;
    this.confirmAction = null;
    action?.();
  }

  cancelarConfirmacion() {
    this.confirmVisible.set(false);
    this.confirmAction = null;
  }
}
