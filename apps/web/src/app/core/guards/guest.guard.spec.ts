import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { guestGuard } from './guest.guard';
import { AuthService } from '../services/auth.service';

describe('guestGuard', () => {
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

  it('should allow navigation to login/register when user has no token', () => {
    mockAuthService.getToken.mockReturnValue(null);

    const result = TestBed.runInInjectionContext(() => guestGuard({} as any, {} as any));

    expect(result).toBe(true);
  });

  it('should redirect authenticated user to /chat', () => {
    mockAuthService.getToken.mockReturnValue('already-logged-in-token');

    const result = TestBed.runInInjectionContext(() => guestGuard({} as any, {} as any));

    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/chat');
  });
});
