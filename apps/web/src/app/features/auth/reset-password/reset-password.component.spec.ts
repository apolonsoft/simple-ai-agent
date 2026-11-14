import { TestBed, ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { ResetPasswordComponent } from './reset-password.component';
import { AuthService } from '../../../core/services/auth.service';

describe('ResetPasswordComponent', () => {
  let component: ResetPasswordComponent;
  let fixture: ComponentFixture<ResetPasswordComponent>;
  let mockAuthService: {
    verifyResetToken: ReturnType<typeof vi.fn>;
    resetPassword: ReturnType<typeof vi.fn>;
  };
  let queryParamToken = 'valid-sample-token';

  const createComponent = async (tokenValue: string | null = 'valid-sample-token') => {
    mockAuthService = {
      verifyResetToken: vi.fn(),
      resetPassword: vi.fn(),
    };

    if (tokenValue) {
      mockAuthService.verifyResetToken.mockReturnValue(of({ valid: true, email: 'test@example.com' }));
    }

    await TestBed.configureTestingModule({
      imports: [ResetPasswordComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: {
                get: (key: string) => (key === 'token' ? tokenValue : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ResetPasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  };

  it('should set status to invalid if token query param is missing', async () => {
    await createComponent(null);
    expect(component.status()).toBe('invalid');
  });

  it('should set status to invalid if verifyResetToken returns false', async () => {
    mockAuthService = {
      verifyResetToken: vi.fn().mockReturnValue(of({ valid: false })),
      resetPassword: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ResetPasswordComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              queryParamMap: {
                get: (key: string) => (key === 'token' ? 'expired-token' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ResetPasswordComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.status()).toBe('invalid');
  });

  it('should set status to valid if verifyResetToken succeeds', async () => {
    await createComponent('valid-token-123');
    expect(component.status()).toBe('valid');
    expect(mockAuthService.verifyResetToken).toHaveBeenCalledWith('valid-token-123');
  });

  it('should validate password length', async () => {
    await createComponent('valid-token-123');
    const passwordField = component.resetForm.get('newPassword');

    passwordField?.setValue('123');
    expect(passwordField?.hasError('minlength')).toBe(true);

    passwordField?.setValue('validPassword123');
    expect(passwordField?.hasError('minlength')).toBe(false);
  });

  it('should call resetPassword and transition to success status upon submission', async () => {
    await createComponent('valid-token-123');
    mockAuthService.resetPassword.mockReturnValue(of({ message: 'Password has been successfully reset.' }));

    component.resetForm.setValue({ newPassword: 'BrandNewPassword123!' });
    component.onSubmit();

    expect(mockAuthService.resetPassword).toHaveBeenCalledWith('valid-token-123', 'BrandNewPassword123!');
    expect(component.status()).toBe('success');
    expect(component.isSubmitting()).toBe(false);
  });

  it('should display error message on reset failure', async () => {
    await createComponent('valid-token-123');
    mockAuthService.resetPassword.mockReturnValue(
      throwError(() => ({ error: { detail: 'Token has already been used.' } }))
    );

    component.resetForm.setValue({ newPassword: 'BrandNewPassword123!' });
    component.onSubmit();

    expect(component.errorMessage()).toBe('Token has already been used.');
    expect(component.isSubmitting()).toBe(false);
    expect(component.status()).toBe('valid');
  });
});
