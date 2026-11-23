import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, switchMap, of, catchError, finalize, shareReplay } from 'rxjs';
import { User, TokenResponse, RegisterRequest, ResetPasswordRequest, ChangePasswordRequest, VerifyResetTokenResponse, MessageResponse } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  // Reactive state using Angular Signals
  readonly currentUser = signal<User | null>(null);
  readonly isLoading = signal<boolean>(false);
  readonly isAuthenticated = computed(() => !!this.currentUser());

  private meRequest$: Observable<User> | null = null;
  private readonly logoutCleanups = new Set<() => void>();

  constructor() {
    this.checkInitialAuth();
  }

  registerLogoutCleanup(fn: () => void): void {
    this.logoutCleanups.add(fn);
  }

  getToken(): string | null {
    if (typeof localStorage === 'undefined') {
      return null;
    }
    const token = localStorage.getItem('token');
    if (!token) {
      return null;
    }
    if (this.isTokenExpired(token)) {
      this.removeToken();
      return null;
    }
    return token;
  }

  private isTokenExpired(token: string): boolean {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return false;
    }
    try {
      const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=');
      const payload = JSON.parse(atob(padded)) as { exp?: unknown };
      if (typeof payload.exp === 'number') {
        return payload.exp * 1000 <= Date.now();
      }
      return false;
    } catch {
      return true;
    }
  }

  private setToken(token: string): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  private removeToken(): void {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('token');
    }
  }

  ensureCurrentUser(): Observable<User> {
    const existing = this.currentUser();
    if (existing) {
      return of(existing);
    }
    if (!this.meRequest$) {
      this.meRequest$ = this.getMe().pipe(
        tap((user) => {
          this.currentUser.set(user);
        }),
        finalize(() => {
          this.meRequest$ = null;
        }),
        shareReplay({ bufferSize: 1, refCount: false })
      );
    }
    return this.meRequest$;
  }

  checkInitialAuth(): void {
    const token = this.getToken();
    if (token) {
      this.ensureCurrentUser().subscribe({
        error: () => this.logout(),
      });
    }
  }

  login(email: string, password: string): Observable<User> {
    this.isLoading.set(true);

    const body = new URLSearchParams();
    body.set('username', email);
    body.set('password', password);

    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded'
    });

    return this.http.post<TokenResponse>('/api/v1/auth/login', body.toString(), { headers }).pipe(
      tap((res) => this.setToken(res.access_token)),
      switchMap(() => this.getMe()),
      tap((user) => {
        this.currentUser.set(user);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        throw err;
      })
    );
  }

  register(req: RegisterRequest): Observable<User> {
    this.isLoading.set(true);
    return this.http.post<User>('/api/v1/auth/register', req).pipe(
      tap(() => this.isLoading.set(false)),
      catchError((err) => {
        this.isLoading.set(false);
        throw err;
      })
    );
  }

  getMe(): Observable<User> {
    return this.http.get<User>('/api/v1/auth/me');
  }

  forgotPassword(email: string): Observable<MessageResponse> {
    return this.http.post<MessageResponse>('/api/v1/auth/forgot-password', { email });
  }

  verifyResetToken(token: string): Observable<VerifyResetTokenResponse> {
    return this.http.get<VerifyResetTokenResponse>(`/api/v1/auth/verify-reset-token?token=${encodeURIComponent(token)}`);
  }

  resetPassword(token: string, newPassword: string): Observable<MessageResponse> {
    const payload: ResetPasswordRequest = { token, new_password: newPassword };
    return this.http.post<MessageResponse>('/api/v1/auth/reset-password', payload);
  }

  changePassword(req: ChangePasswordRequest): Observable<MessageResponse> {
    return this.http.post<MessageResponse>('/api/v1/auth/change-password', req);
  }

  logout(): void {
    this.meRequest$ = null;
    this.removeToken();
    this.currentUser.set(null);
    for (const cleanup of this.logoutCleanups) {
      cleanup();
    }
    this.router.navigate(['/login']);
  }
}
