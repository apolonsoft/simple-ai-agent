import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError, finalize } from 'rxjs';
import { AuthService } from './auth.service';
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
  private readonly authService = inject(AuthService);
  private readonly baseUrl = '/api/v1/admin/users';

  constructor() {
    this.authService.registerLogoutCleanup(() => this.resetState());
  }

  resetState(): void {
    this.users.set([]);
    this.total.set(0);
    this.page.set(1);
    this.totalPages.set(1);
    this.selectedUser.set(null);
    this.searchQuery.set('');
    this.roleFilter.set('');
    this.statusFilter.set('');
    this.isLoadingList.set(false);
    this.isLoadingDetail.set(false);
    this.mutatingUserId.set(null);
    this.error.set(null);
  }

  // State signals
  readonly users = signal<AdminUser[]>([]);
  readonly total = signal<number>(0);
  readonly page = signal<number>(1);
  readonly limit = signal<number>(20);
  readonly totalPages = signal<number>(1);
  readonly isLoadingList = signal<boolean>(false);
  readonly isLoadingDetail = signal<boolean>(false);
  readonly mutatingUserId = signal<string | null>(null);
  readonly isLoading = computed(() => this.isLoadingList() || this.isLoadingDetail());
  readonly error = signal<string | null>(null);
  readonly selectedUser = signal<AdminUserDetail | null>(null);

  // Active filter signals
  readonly searchQuery = signal<string>('');
  readonly roleFilter = signal<string>('');
  readonly statusFilter = signal<string>('');

  loadUsers(filter?: AdminUserFilter): Observable<AdminUserListResponse> {
    this.isLoadingList.set(true);
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
        this.isLoadingList.set(false);
      }),
      catchError((err) => {
        this.isLoadingList.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to load users';
        this.error.set(errMsg);
        return throwError(() => err);
      }),
      finalize(() => {
        this.isLoadingList.set(false);
      })
    );
  }

  getUserDetail(userId: string): Observable<AdminUserDetail> {
    this.selectedUser.set(null);
    this.isLoadingDetail.set(true);
    this.error.set(null);

    return this.http.get<AdminUserDetail>(`${this.baseUrl}/${userId}`).pipe(
      tap((user) => {
        this.selectedUser.set(user);
        this.isLoadingDetail.set(false);
      }),
      catchError((err) => {
        this.isLoadingDetail.set(false);
        const errMsg = err?.error?.detail || err?.message || 'Failed to load user details';
        this.error.set(errMsg);
        return throwError(() => err);
      }),
      finalize(() => {
        this.isLoadingDetail.set(false);
      })
    );
  }

  banUser(userId: string, reason?: string): Observable<AdminActionResponse> {
    this.mutatingUserId.set(userId);
    this.error.set(null);

    const body: BanUserRequest = { reason: reason || null };

    return this.http.post<AdminActionResponse>(`${this.baseUrl}/${userId}/ban`, body).pipe(
      tap((res) => {
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        const errMsg = err?.error?.detail || err?.message || 'Failed to ban user';
        this.error.set(errMsg);
        return throwError(() => err);
      }),
      finalize(() => {
        if (this.mutatingUserId() === userId) {
          this.mutatingUserId.set(null);
        }
      })
    );
  }

  unbanUser(userId: string): Observable<AdminActionResponse> {
    this.mutatingUserId.set(userId);
    this.error.set(null);

    return this.http.post<AdminActionResponse>(`${this.baseUrl}/${userId}/unban`, {}).pipe(
      tap((res) => {
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        const errMsg = err?.error?.detail || err?.message || 'Failed to unban user';
        this.error.set(errMsg);
        return throwError(() => err);
      }),
      finalize(() => {
        if (this.mutatingUserId() === userId) {
          this.mutatingUserId.set(null);
        }
      })
    );
  }

  updateRole(userId: string, role: UserRole): Observable<AdminActionResponse> {
    this.mutatingUserId.set(userId);
    this.error.set(null);

    const body: UpdateUserRoleRequest = { role };

    return this.http.patch<AdminActionResponse>(`${this.baseUrl}/${userId}/role`, body).pipe(
      tap((res) => {
        this.updateUserInState(res.user);
      }),
      catchError((err) => {
        const errMsg = err?.error?.detail || err?.message || 'Failed to update user role';
        this.error.set(errMsg);
        return throwError(() => err);
      }),
      finalize(() => {
        if (this.mutatingUserId() === userId) {
          this.mutatingUserId.set(null);
        }
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
