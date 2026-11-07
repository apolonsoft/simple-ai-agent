import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  let mockAuthService: { getToken: ReturnType<typeof vi.fn> };
  let router: Router;

  beforeEach(() => {
    mockAuthService = {
      getToken: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: mockAuthService },
      ],
    });

    router = TestBed.inject(Router);
  });

  it('should allow navigation when user has a valid token', () => {
    mockAuthService.getToken.mockReturnValue('valid-token-abc');

    const result = TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));

    expect(result).toBe(true);
  });

  it('should redirect to /login when user has no token', () => {
    mockAuthService.getToken.mockReturnValue(null);

    const result = TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));

    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/login');
  });
});
