import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { RegisterComponent } from './register.component';
import { AuthService } from '../../../core/services/auth.service';

describe('RegisterComponent', () => {
  let component: RegisterComponent;
  let fixture: ComponentFixture<RegisterComponent>;
  let mockAuthService: { register: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(async () => {
    mockAuthService = {
      register: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize with invalid empty form', () => {
    expect(component.registerForm.valid).toBe(false);
  });

  it('should fail validation when passwords do not match', () => {
    component.registerForm.patchValue({
      email: 'newuser@example.com',
      password: 'password123',
      confirmPassword: 'differentpassword',
    });

    expect(component.registerForm.hasError('passwordMismatch')).toBe(true);
    expect(component.registerForm.valid).toBe(false);
  });

  it('should call authService.register on valid submission', () => {
    mockAuthService.register.mockReturnValue(of({ id: 'new-id', email: 'newuser@example.com' }));

    component.registerForm.setValue({
      email: 'newuser@example.com',
      password: 'password123',
      confirmPassword: 'password123',
    });

    component.onSubmit();

    expect(mockAuthService.register).toHaveBeenCalledWith({
      email: 'newuser@example.com',
      password: 'password123',
    });
    expect(component.successMessage()).toContain('Account created successfully');
  });
});
