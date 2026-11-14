import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ForgotPasswordComponent } from './forgot-password.component';
import { AuthService } from '../../../core/services/auth.service';

describe('ForgotPasswordComponent', () => {
  let component: ForgotPasswordComponent;
  let fixture: ComponentFixture<ForgotPasswordComponent>;
  let mockAuthService: { forgotPassword: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    mockAuthService = {
      forgotPassword: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ForgotPasswordComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ForgotPasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize with invalid empty email form', () => {
    expect(component.forgotForm.valid).toBe(false);
    expect(component.isSent()).toBe(false);
  });

  it('should validate email format', () => {
    const emailField = component.forgotForm.get('email');
    emailField?.setValue('invalid-email');
    expect(emailField?.hasError('email')).toBe(true);

    emailField?.setValue('valid@example.com');
    expect(emailField?.hasError('email')).toBe(false);
  });

  it('should call authService.forgotPassword and set isSent on success', () => {
    mockAuthService.forgotPassword.mockReturnValue(
      of({ message: 'If an account with that email exists, a password reset link has been sent.' })
    );

    component.forgotForm.setValue({ email: 'user@example.com' });
    component.onSubmit();

    expect(mockAuthService.forgotPassword).toHaveBeenCalledWith('user@example.com');
    expect(component.isSent()).toBe(true);
    expect(component.isSubmitting()).toBe(false);
  });

  it('should set errorMessage on failed request', () => {
    mockAuthService.forgotPassword.mockReturnValue(
      throwError(() => ({ error: { detail: 'Too many requests' } }))
    );

    component.forgotForm.setValue({ email: 'user@example.com' });
    component.onSubmit();

    expect(component.isSent()).toBe(false);
    expect(component.errorMessage()).toBe('Too many requests');
    expect(component.isSubmitting()).toBe(false);
  });
});
