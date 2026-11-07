import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginComponent } from './login.component';
import { AuthService } from '../../../core/services/auth.service';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let mockAuthService: { login: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(async () => {
    mockAuthService = {
      login: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize with invalid empty form', () => {
    expect(component.loginForm.valid).toBe(false);
  });

  it('should validate email format', () => {
    const emailField = component.loginForm.get('email');
    emailField?.setValue('not-an-email');
    expect(emailField?.hasError('email')).toBe(true);

    emailField?.setValue('user@example.com');
    expect(emailField?.hasError('email')).toBe(false);
  });

  it('should call authService.login and navigate to /chat on valid submission', () => {
    mockAuthService.login.mockReturnValue(of({ id: '123', email: 'user@example.com' }));

    component.loginForm.setValue({
      email: 'user@example.com',
      password: 'password123',
    });

    component.onSubmit();

    expect(mockAuthService.login).toHaveBeenCalledWith('user@example.com', 'password123');
    expect(router.navigate).toHaveBeenCalledWith(['/chat']);
  });

  it('should display error message on failed login', () => {
    mockAuthService.login.mockReturnValue(
      throwError(() => ({ error: { detail: 'Incorrect email or password' } }))
    );

    component.loginForm.setValue({
      email: 'user@example.com',
      password: 'wrongpassword',
    });

    component.onSubmit();

    expect(component.errorMessage()).toBe('Incorrect email or password');
    expect(component.isSubmitting()).toBe(false);
  });
});
