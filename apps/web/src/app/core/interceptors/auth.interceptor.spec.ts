import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTestingController: HttpTestingController;
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    mockRouter = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: Router, useValue: mockRouter },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTestingController = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpTestingController.verify();
    localStorage.clear();
  });

  it('should add Authorization Bearer header when token exists in localStorage', () => {
    localStorage.setItem('token', 'fake-jwt-token-xyz');

    httpClient.get('/api/v1/chats').subscribe();

    const req = httpTestingController.expectOne('/api/v1/chats');
    expect(req.request.headers.has('Authorization')).toBe(true);
    expect(req.request.headers.get('Authorization')).toBe('Bearer fake-jwt-token-xyz');
    req.flush([]);
  });

  it('should not add Authorization header when token is not present', () => {
    httpClient.get('/api/v1/public-endpoint').subscribe();

    const req = httpTestingController.expectOne('/api/v1/public-endpoint');
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush({});
  });

  it('should delegate 401 Unauthorized to AuthService.logout() clearing currentUser, token, and navigating to /login', () => {
    const authService = TestBed.inject(AuthService);
    authService.currentUser.set({
      id: 'user-1',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
    });
    localStorage.setItem('token', 'expired-token');

    httpClient.get('/api/v1/chats').subscribe({
      next: () => {},
      error: () => {},
    });

    const req = httpTestingController.expectOne('/api/v1/chats');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem('token')).toBeNull();
    expect(authService.currentUser()).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });
});
