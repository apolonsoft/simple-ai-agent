import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  AdminUser,
  AdminUserDetail,
  AdminUserListResponse,
  AdminActionResponse,
  AdminUserFilter,
  BanUserRequest,
  UpdateUserRoleRequest,
  UserRole,
} from '../models/admin.model';

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/users';

  // State signals
  readonly users = signal<AdminUser[]>([]);
  readonly total = signal<number>(0);
  readonly page = signal<number>(1);
  readonly limit = signal<number>(20);
  readonly totalPages = signal<number>(1);
  readonly isLoading = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly selectedUser = signal<AdminUserDetail | null>(null);

  // Active filter signals
  readonly searchQuery = signal<string>('');
  readonly roleFilter = signal<string>('');
  readonly statusFilter = signal<string>('');

  loadUsers(filter?: AdminUserFilter): Observable<AdminUserListResponse> {
    this.isLoading.set(true);
    this.error.set(null);

    let params = new HttpParams();

    const page = filter?.page ?? this.page();
    const limit = filter?.limit ?? this.limit();
    params = params.set('page', page.toString());
    params = params.set('limit', limit.toString());

    const search = filter?.search !== undefined ? filter.search : this.searchQuery();
    if (search && search.trim()) {
      params = params.set('search', search.trim());
    }

    const role = filter?.role !== undefined ? filter.role : this.roleFilter();
    if (role && role !== 'all') {
      params = params.set('role', role);
    }

    const status = filter?.status !== undefined ? filter.status : this.statusFilter();
    if (status && status !== 'all') {
      params = params.set('status', status);
    }

    return this.http.get<AdminUserListResponse>(this.baseUrl, { params }).pipe(
      tap((res) => {
        this.users.set(res.items);
        this.total.set(res.total);
        this.page.set(res.page);
        this.limit.set(res.limit);
        this.totalPages.set(res.total_pages);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to load users';
        this.error.set(errMsg);
        return throwError(() => err);
      })
    );
  }

  getUserDetail(userId: string): Observable<AdminUserDetail> {
    this.isLoading.set(true);
    this.error.set(null);

    return this.http.get<AdminUserDetail>(`${this.baseUrl}/${userId}`).pipe(
      tap((user) => {
        this.selectedUser.set(user);
        this.isLoading.set(false);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to load user details';
        this.error.set(errMsg);
        return throwError(() => err);
      })
    );
  }

  banUser(userId: string, reason?: string): Observable<AdminActionResponse> {
    this.isLoading.set(true);
    this.error.set(null);

    const body: BanUserRequest = { reason: reason || null };

    return this.http.post<AdminActionResponse>(`${this.baseUrl}/${userId}/ban`, body).pipe(
      tap((res) => {
        this.isLoading.set(false);
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to ban user';
        this.error.set(errMsg);
        return throwError(() => err);
      })
    );
  }

  unbanUser(userId: string): Observable<AdminActionResponse> {
    this.isLoading.set(true);
    this.error.set(null);

    return this.http.post<AdminActionResponse>(`${this.baseUrl}/${userId}/unban`, {}).pipe(
      tap((res) => {
        this.isLoading.set(false);
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to unban user';
        this.error.set(errMsg);
        return throwError(() => err);
      })
    );
  }

  updateRole(userId: string, role: UserRole): Observable<AdminActionResponse> {
    this.isLoading.set(true);
    this.error.set(null);

    const body: UpdateUserRoleRequest = { role };

    return this.http.patch<AdminActionResponse>(`${this.baseUrl}/${userId}/role`, body).pipe(
      tap((res) => {
        this.isLoading.set(false);
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        this.isLoading.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to update user role';
        this.error.set(errMsg);
        return throwError(() => err);
      })
    );
  }

  private updateUserInState(updatedUser: AdminUser): void {
    this.users.update((current) =>
      current.map((u) => (u.id === updatedUser.id ? { ...u, ...updatedUser } : u))
    );

    const sel = this.selectedUser();
    if (sel && sel.id === updatedUser.id) {
      this.selectedUser.set({ ...sel, ...updatedUser });
    }
  }
}
