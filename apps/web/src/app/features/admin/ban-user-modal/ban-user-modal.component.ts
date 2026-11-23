import { ChangeDetectionStrategy, Component, HostListener, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminUser } from '../../../core/models/admin.model';

@Component({
  selector: 'app-ban-user-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './ban-user-modal.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BanUserModalComponent {
  readonly targetUser = input.required<AdminUser>();
  readonly isSubmitting = input<boolean>(false);

  readonly cancel = output<void>();
  readonly confirm = output<string>();

  readonly banReason = signal<string>('');

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (!this.isSubmitting()) {
      this.onCancel();
    }
  }

  onCancel(): void {
    if (!this.isSubmitting()) {
      this.banReason.set('');
      this.cancel.emit();
    }
  }

  onConfirm(): void {
    if (!this.isSubmitting()) {
      this.confirm.emit(this.banReason().trim());
    }
  }
}
