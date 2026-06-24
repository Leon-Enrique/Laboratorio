import { Injectable, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';

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
    let detail = fallback;
    if (err instanceof HttpErrorResponse) {
      if (err.status === 0) {
        detail =
          'Sin respuesta del servidor. Si el API está en Render (plan gratis), espere ~30 s tras abrir la página y vuelva a intentar.';
      } else if (err.error && typeof err.error === 'object' && 'detail' in err.error) {
        detail = String((err.error as { detail: unknown }).detail);
      } else if (err.message) {
        detail = err.message;
      }
    } else if (err && typeof err === 'object' && 'message' in err) {
      detail = String((err as { message: string }).message);
    }
    this.mostrarToast(detail, 'error');
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
