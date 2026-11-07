import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <div class="auth-container">
      <div class="auth-card">
        <div class="header">
          <div class="logo-badge">🤖</div>
          <h1>Welcome Back</h1>
          <p class="subtitle">Sign in to your AI Agent account</p>
        </div>

        @if (errorMessage()) {
          <div class="error-alert">
            <span>⚠️</span>
            <p>{{ errorMessage() }}</p>
          </div>
        }

        <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
          <div class="form-group">
            <label for="email">Email Address</label>
            <input
              id="email"
              type="email"
              formControlName="email"
              placeholder="you@example.com"
              [class.input-error]="isFieldInvalid('email')"
            />
            @if (isFieldInvalid('email')) {
              <span class="field-error">Please enter a valid email address.</span>
            }
          </div>

          <div class="form-group">
            <label for="password">Password</label>
            <input
              id="password"
              type="password"
              formControlName="password"
              placeholder="••••••••"
              [class.input-error]="isFieldInvalid('password')"
            />
            @if (isFieldInvalid('password')) {
              <span class="field-error">Password is required.</span>
            }
          </div>

          <button
            type="submit"
            class="submit-btn"
            [disabled]="loginForm.invalid || isSubmitting()"
          >
            @if (isSubmitting()) {
              <span class="spinner"></span> Signing in...
            } @else {
              Sign In
            }
          </button>
        </form>

        <div class="footer">
          <p>Don't have an account? <a routerLink="/register">Create one</a></p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .auth-container {
      display: flex;
      min-height: 100vh;
      align-items: center;
      justify-content: center;
      background: #090d16;
      padding: 1.5rem;
      font-family: inherit;
    }
    .auth-card {
      width: 100%;
      max-width: 420px;
      background: #111827;
      border: 1px solid #1f2937;
      border-radius: 1rem;
      padding: 2.5rem;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    .header {
      text-align: center;
      margin-bottom: 2rem;
    }
    .logo-badge {
      font-size: 2.5rem;
      margin-bottom: 0.5rem;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #f9fafb;
      margin: 0;
    }
    .subtitle {
      color: #9ca3af;
      font-size: 0.875rem;
      margin-top: 0.25rem;
    }
    .error-alert {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #f87171;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
    }
    .form-group {
      margin-bottom: 1.25rem;
    }
    label {
      display: block;
      color: #d1d5db;
      font-size: 0.875rem;
      font-weight: 500;
      margin-bottom: 0.5rem;
    }
    input {
      width: 100%;
      padding: 0.75rem 1rem;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 0.5rem;
      color: #f9fafb;
      font-size: 0.95rem;
      outline: none;
      box-sizing: border-box;
      transition: border-color 0.15s;
    }
    input:focus {
      border-color: #6366f1;
    }
    input.input-error {
      border-color: #ef4444;
    }
    .field-error {
      color: #f87171;
      font-size: 0.75rem;
      margin-top: 0.25rem;
      display: block;
    }
    .submit-btn {
      width: 100%;
      padding: 0.75rem 1.5rem;
      background: #4f46e5;
      color: #ffffff;
      border: none;
      border-radius: 0.5rem;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: background-color 0.15s;
      margin-top: 1rem;
    }
    .submit-btn:hover:not(:disabled) {
      background: #4338ca;
    }
    .submit-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .spinner {
      width: 1rem;
      height: 1rem;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .footer {
      text-align: center;
      margin-top: 1.75rem;
      color: #9ca3af;
      font-size: 0.875rem;
    }
    .footer a {
      color: #818cf8;
      text-decoration: none;
      font-weight: 500;
    }
    .footer a:hover {
      text-decoration: underline;
    }
  `]
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly isSubmitting = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);

  readonly loginForm: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(4)]],
  });

  isFieldInvalid(fieldName: string): boolean {
    const field = this.loginForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  onSubmit(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set(null);

    const { email, password } = this.loginForm.value;
    this.authService.login(email, password).subscribe({
      next: () => {
        this.isSubmitting.set(false);
        this.router.navigate(['/chat']);
      },
      error: (err) => {
        this.isSubmitting.set(false);
        const detail = err.error?.detail || 'Incorrect email or password. Please try again.';
        this.errorMessage.set(detail);
      }
    });
  }
}
