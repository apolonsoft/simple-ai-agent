import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, switchMap, of, catchError } from 'rxjs';
import { User, TokenResponse, RegisterRequest } from '../models/user.model';

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

  constructor() {
    this.checkInitialAuth();
  }

  getToken(): string | null {
    if (typeof localStorage !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
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

  checkInitialAuth(): void {
    const token = this.getToken();
    if (token) {
      this.getMe().subscribe({
        next: (user) => this.currentUser.set(user),
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

  logout(): void {
    this.removeToken();
    this.currentUser.set(null);
    this.router.navigate(['/login']);
  }
}
