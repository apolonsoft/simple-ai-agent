import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

export type ResetStatus = 'loading' | 'valid' | 'invalid' | 'success';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './reset-password.component.html',
})
export class ResetPasswordComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  readonly status = signal<ResetStatus>('loading');
  readonly isSubmitting = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  token = '';

  readonly resetForm: FormGroup = this.fb.group({
    newPassword: ['', [Validators.required, Validators.minLength(8)]],
  });

  ngOnInit(): void {
    this.token = this.route.snapshot.queryParamMap.get('token') || '';

    if (!this.token) {
      this.status.set('invalid');
      return;
    }

    this.authService.verifyResetToken(this.token).subscribe({
      next: (res) => {
        if (res.valid) {
          this.status.set('valid');
        } else {
          this.status.set('invalid');
        }
      },
      error: () => {
        this.status.set('invalid');
      },
    });
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.resetForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  onSubmit(): void {
    if (this.resetForm.invalid) {
      this.resetForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    const { newPassword } = this.resetForm.value;
    this.authService.resetPassword(this.token, newPassword).subscribe({
      next: () => {
        this.isSubmitting.set(false);
        this.status.set('success');
      },
      error: (err) => {
        this.isSubmitting.set(false);
        const detail = err.error?.detail || 'Failed to reset password. Please try again or request a new link.';
        this.errorMessage.set(detail);
      },
    });
  }
}
