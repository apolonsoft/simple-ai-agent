import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { of, throwError } from 'rxjs';
import { adminGuard } from './admin.guard';
import { AuthService } from '../services/auth.service';
import { User } from '../models/user.model';

describe('adminGuard', () => {
  let mockAuthService: {
    getToken: ReturnType<typeof vi.fn>;
    currentUser: ReturnType<typeof signal<User | null>>;
    getMe: ReturnType<typeof vi.fn>;
    logout: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  beforeEach(() => {
    mockAuthService = {
      getToken: vi.fn(),
      currentUser: signal<User | null>(null),
      getMe: vi.fn(),
      logout: vi.fn(),
    };

    TestBed.configureTestingModule({
      providers: [{ provide: AuthService, useValue: mockAuthService }],
    });

    router = TestBed.inject(Router);
  });

  it('should redirect to /login when user has no token', () => {
    mockAuthService.getToken.mockReturnValue(null);

    const result = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any));

    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/login');
  });

  it('should allow navigation when currentUser has admin role', () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set({
      id: '1',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
    });

    const result = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any));

    expect(result).toBe(true);
  });

  it('should allow navigation when currentUser has super_admin role', () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set({
      id: '2',
      email: 'super@example.com',
      role: 'super_admin',
      is_active: true,
    });

    const result = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any));

    expect(result).toBe(true);
  });

  it('should redirect to /chat when currentUser has regular user role', () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set({
      id: '3',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
    });

    const result = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any));

    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/chat');
  });

  it('should fetch profile with getMe when signal is null and allow if role is admin', async () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set(null);
    mockAuthService.getMe.mockReturnValue(
      of({
        id: '1',
        email: 'admin@example.com',
        role: 'admin',
        is_active: true,
      })
    );

    const guardObs = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any)) as any;

    guardObs.subscribe((res: any) => {
      expect(res).toBe(true);
      expect(mockAuthService.currentUser()?.role).toBe('admin');
    });
  });

  it('should fetch profile with getMe when signal is null and redirect to /chat if role is user', async () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set(null);
    mockAuthService.getMe.mockReturnValue(
      of({
        id: '4',
        email: 'regular@example.com',
        role: 'user',
        is_active: true,
      })
    );

    const guardObs = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any)) as any;

    guardObs.subscribe((res: any) => {
      expect(res instanceof UrlTree).toBe(true);
      expect((res as UrlTree).toString()).toBe('/chat');
    });
  });

  it('should call logout and redirect to /login if getMe fails', async () => {
    mockAuthService.getToken.mockReturnValue('valid-token');
    mockAuthService.currentUser.set(null);
    mockAuthService.getMe.mockReturnValue(throwError(() => new Error('Unauthorized')));

    const guardObs = TestBed.runInInjectionContext(() => adminGuard({} as any, {} as any)) as any;

    guardObs.subscribe((res: any) => {
      expect(mockAuthService.logout).toHaveBeenCalled();
      expect(res instanceof UrlTree).toBe(true);
      expect((res as UrlTree).toString()).toBe('/login');
    });
  });
});
