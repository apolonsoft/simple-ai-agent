import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { AdminService } from './admin.service';
import {
  AdminUser,
  AdminUserDetail,
  AdminUserListResponse,
  AdminActionResponse,
} from '../models/admin.model';

describe('AdminService', () => {
  let service: AdminService;
  let httpTestingController: HttpTestingController;

  const mockUsers: AdminUser[] = [
    {
      id: 'user-1',
      email: 'user1@example.com',
      full_name: 'User One',
      role: 'user',
      is_active: true,
      is_banned: false,
      banned_at: null,
      ban_reason: null,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'admin-1',
      email: 'admin1@example.com',
      full_name: 'Admin One',
      role: 'admin',
      is_active: true,
      is_banned: false,
      banned_at: null,
      ban_reason: null,
      created_at: '2026-01-01T00:00:00Z',
    },
  ];

  const mockListResponse: AdminUserListResponse = {
    items: mockUsers,
    total: 2,
    page: 1,
    limit: 20,
    total_pages: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), AdminService],
    });

    service = TestBed.inject(AdminService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should initialize with default empty signals', () => {
    expect(service.users()).toEqual([]);
    expect(service.total()).toBe(0);
    expect(service.page()).toBe(1);
    expect(service.limit()).toBe(20);
    expect(service.isLoading()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.selectedUser()).toBeNull();
  });

  it('should load users and populate signals on success', () => {
    service.loadUsers({ page: 1, limit: 10, search: 'test', role: 'user', status: 'active' }).subscribe((res) => {
      expect(res).toEqual(mockListResponse);
      expect(service.users()).toEqual(mockUsers);
      expect(service.total()).toBe(2);
      expect(service.page()).toBe(1);
      expect(service.limit()).toBe(20);
      expect(service.totalPages()).toBe(1);
      expect(service.isLoading()).toBe(false);
    });

    const req = httpTestingController.expectOne(
      (r) =>
        r.url === '/api/v1/admin/users' &&
        r.params.get('page') === '1' &&
        r.params.get('limit') === '10' &&
        r.params.get('search') === 'test' &&
        r.params.get('role') === 'user' &&
        r.params.get('status') === 'active'
    );
    expect(req.request.method).toBe('GET');

    req.flush(mockListResponse);
  });

  it('should set error signal if loadUsers fails', () => {
    service.loadUsers().subscribe({
      next: () => expect.unreachable('Should have failed'),
      error: () => {
        expect(service.error()).toBe('Forbidden');
        expect(service.isLoading()).toBe(false);
      },
    });

    const req = httpTestingController.expectOne((r) => r.url === '/api/v1/admin/users');
    req.flush({ detail: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });
  });

  it('should fetch user detail and populate selectedUser signal', () => {
    const mockDetail: AdminUserDetail = {
      ...mockUsers[0],
      avatar_url: 'https://example.com/avatar.png',
      bio: 'Hello bio',
      chat_sessions_count: 5,
      updated_at: '2026-01-02T00:00:00Z',
    };

    service.getUserDetail('user-1').subscribe((detail) => {
      expect(detail).toEqual(mockDetail);
      expect(service.selectedUser()).toEqual(mockDetail);
      expect(service.isLoading()).toBe(false);
    });

    const req = httpTestingController.expectOne('/api/v1/admin/users/user-1');
    expect(req.request.method).toBe('GET');
    req.flush(mockDetail);
  });

  it('should ban user and update item in users signal and selectedUser signal', () => {
    service.users.set(mockUsers);
    const mockDetail: AdminUserDetail = {
      ...mockUsers[0],
      chat_sessions_count: 2,
    };
    service.selectedUser.set(mockDetail);

    const bannedUser: AdminUser = {
      ...mockUsers[0],
      is_banned: true,
      ban_reason: 'Spamming',
      banned_at: '2026-02-01T12:00:00Z',
    };

    const actionResponse: AdminActionResponse = {
      success: true,
      message: 'User banned',
      user: bannedUser,
    };

    service.banUser('user-1', 'Spamming').subscribe((res) => {
      expect(res.user.is_banned).toBe(true);
      expect(res.user.ban_reason).toBe('Spamming');

      // Check users signal update
      const updatedInList = service.users().find((u) => u.id === 'user-1');
      expect(updatedInList?.is_banned).toBe(true);
      expect(updatedInList?.ban_reason).toBe('Spamming');

      // Check selectedUser signal update
      expect(service.selectedUser()?.is_banned).toBe(true);
      expect(service.selectedUser()?.ban_reason).toBe('Spamming');
    });

    const req = httpTestingController.expectOne('/api/v1/admin/users/user-1/ban');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ reason: 'Spamming' });
    req.flush(actionResponse);
  });

  it('should unban user and update state', () => {
    const initiallyBanned: AdminUser = {
      ...mockUsers[0],
      is_banned: true,
      ban_reason: 'Spam',
    };
    service.users.set([initiallyBanned]);

    const unbannedUser: AdminUser = {
      ...mockUsers[0],
      is_banned: false,
      ban_reason: null,
      banned_at: null,
    };

    const actionResponse: AdminActionResponse = {
      success: true,
      message: 'User unbanned',
      user: unbannedUser,
    };

    service.unbanUser('user-1').subscribe((res) => {
      expect(res.user.is_banned).toBe(false);
      expect(service.users()[0].is_banned).toBe(false);
    });

    const req = httpTestingController.expectOne('/api/v1/admin/users/user-1/unban');
    expect(req.request.method).toBe('POST');
    req.flush(actionResponse);
  });

  it('should update role and update state', () => {
    service.users.set(mockUsers);

    const promotedUser: AdminUser = {
      ...mockUsers[0],
      role: 'admin',
    };

    const actionResponse: AdminActionResponse = {
      success: true,
      message: 'Role updated',
      user: promotedUser,
    };

    service.updateRole('user-1', 'admin').subscribe((res) => {
      expect(res.user.role).toBe('admin');
      expect(service.users()[0].role).toBe('admin');
    });

    const req = httpTestingController.expectOne('/api/v1/admin/users/user-1/role');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ role: 'admin' });
    req.flush(actionResponse);
  });
});
