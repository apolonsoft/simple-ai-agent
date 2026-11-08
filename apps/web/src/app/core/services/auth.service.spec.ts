import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';
import { User, TokenResponse } from '../models/user.model';

describe('AuthService', () => {
  let service: AuthService;
  let httpTestingController: HttpTestingController;
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  const mockUser: User = {
    id: 'user-uuid-1',
    email: 'architect@example.com',
    role: 'user',
    is_active: true,
  };

  const mockToken: TokenResponse = {
    access_token: 'fake-jwt-token-123',
    token_type: 'bearer',
  };

  beforeEach(() => {
    localStorage.clear();
    mockRouter = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthService,
        { provide: Router, useValue: mockRouter },
      ],
    });

    service = TestBed.inject(AuthService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
    localStorage.clear();
  });

  it('should initialize with null currentUser and unauthenticated status when no token', () => {
    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(service.getToken()).toBeNull();
  });

  it('should restore authenticated session if token exists in localStorage', () => {
    localStorage.setItem('token', 'existing-jwt-token');

    service.checkInitialAuth();

    const req = httpTestingController.expectOne('/api/v1/auth/me');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);

    expect(service.currentUser()).toEqual(mockUser);
    expect(service.isAuthenticated()).toBe(true);
  });

  it('should logout and clear state if initial token verification fails', () => {
    localStorage.setItem('token', 'expired-jwt-token');

    service.checkInitialAuth();

    const req = httpTestingController.expectOne('/api/v1/auth/me');
    req.flush({ detail: 'Token expired' }, { status: 401, statusText: 'Unauthorized' });

    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(service.getToken()).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should login with urlencoded credentials, store token, and fetch user', () => {
    expect(service.isLoading()).toBe(false);

    service.login('architect@example.com', 'SecurePass123!').subscribe((user) => {
      expect(user).toEqual(mockUser);
    });

    expect(service.isLoading()).toBe(true);

    // 1. First expects login request
    const loginReq = httpTestingController.expectOne('/api/v1/auth/login');
    expect(loginReq.request.method).toBe('POST');
    expect(loginReq.request.headers.get('Content-Type')).toContain('application/x-www-form-urlencoded');
    expect(loginReq.request.body).toContain('username=architect%40example.com');
    expect(loginReq.request.body).toContain('password=SecurePass123%21');
    loginReq.flush(mockToken);

    expect(service.getToken()).toBe('fake-jwt-token-123');

    // 2. Then expects getMe request
    const meReq = httpTestingController.expectOne('/api/v1/auth/me');
    expect(meReq.request.method).toBe('GET');
    meReq.flush(mockUser);

    expect(service.currentUser()).toEqual(mockUser);
    expect(service.isAuthenticated()).toBe(true);
    expect(service.isLoading()).toBe(false);
  });

  it('should register a new user successfully', () => {
    const registerPayload = {
      email: 'newuser@example.com',
      password: 'StrongPassword123!',
    };

    service.register(registerPayload).subscribe((user) => {
      expect(user.email).toBe('newuser@example.com');
    });

    expect(service.isLoading()).toBe(true);

    const req = httpTestingController.expectOne('/api/v1/auth/register');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(registerPayload);
    req.flush({ ...mockUser, email: 'newuser@example.com' });

    expect(service.isLoading()).toBe(false);
  });

  it('should logout cleanly, remove token, reset signal, and navigate to /login', () => {
    localStorage.setItem('token', 'active-token');
    service.currentUser.set(mockUser);

    service.logout();

    expect(service.getToken()).toBeNull();
    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });
});
