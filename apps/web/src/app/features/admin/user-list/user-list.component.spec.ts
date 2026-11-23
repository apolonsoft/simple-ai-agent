import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter } from '@angular/router';
import { of, Subject, throwError, finalize } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserListComponent } from './user-list.component';
import { AdminService } from '../../../core/services/admin.service';
import { AuthService } from '../../../core/services/auth.service';
import { AdminUser, AdminUserListResponse, AdminActionResponse } from '../../../core/models/admin.model';
import { User } from '../../../core/models/user.model';

describe('UserListComponent', () => {
  let component: UserListComponent;
  let fixture: ComponentFixture<UserListComponent>;

  let mockAdminService: {
    users: ReturnType<typeof signal<AdminUser[]>>;
    total: ReturnType<typeof signal<number>>;
    page: ReturnType<typeof signal<number>>;
    limit: ReturnType<typeof signal<number>>;
    totalPages: ReturnType<typeof signal<number>>;
    isLoading: ReturnType<typeof signal<boolean>>;
    isLoadingList: ReturnType<typeof signal<boolean>>;
    isLoadingDetail: ReturnType<typeof signal<boolean>>;
    mutatingUserId: ReturnType<typeof signal<string | null>>;
    error: ReturnType<typeof signal<string | null>>;
    loadUsers: ReturnType<typeof vi.fn>;
    banUser: ReturnType<typeof vi.fn>;
    unbanUser: ReturnType<typeof vi.fn>;
    updateRole: ReturnType<typeof vi.fn>;
  };

  let mockAuthService: {
    currentUser: ReturnType<typeof signal<User | null>>;
  };

  const sampleUsers: AdminUser[] = [
    {
      id: 'admin-id-1',
      email: 'admin@platform.com',
      full_name: 'Super Admin User',
      role: 'super_admin',
      is_active: true,
      is_banned: false,
      banned_at: null,
      ban_reason: null,
      created_at: '2026-01-01T00:00:00Z',
    },
    {
      id: 'user-id-2',
      email: 'bob@example.com',
      full_name: 'Bob Regular',
      role: 'user',
      is_active: true,
      is_banned: false,
      banned_at: null,
      ban_reason: null,
      created_at: '2026-01-05T00:00:00Z',
    },
    {
      id: 'banned-id-3',
      email: 'spammer@example.com',
      full_name: 'Spam Bot',
      role: 'user',
      is_active: true,
      is_banned: true,
      banned_at: '2026-02-01T10:00:00Z',
      ban_reason: 'Abusive spamming',
      created_at: '2026-01-10T00:00:00Z',
    },
  ];

  beforeEach(async () => {
    mockAdminService = {
      users: signal<AdminUser[]>(sampleUsers),
      total: signal<number>(3),
      page: signal<number>(1),
      limit: signal<number>(20),
      totalPages: signal<number>(1),
      isLoading: signal<boolean>(false),
      isLoadingList: signal<boolean>(false),
      isLoadingDetail: signal<boolean>(false),
      mutatingUserId: signal<string | null>(null),
      error: signal<string | null>(null),
      loadUsers: vi.fn().mockReturnValue(
        of({
          items: sampleUsers,
          total: 3,
          page: 1,
          limit: 20,
          total_pages: 1,
        } as AdminUserListResponse)
      ),
      banUser: vi.fn(),
      unbanUser: vi.fn(),
      updateRole: vi.fn(),
    };

    mockAuthService = {
      currentUser: signal<User | null>({
        id: 'admin-id-1',
        email: 'admin@platform.com',
        role: 'super_admin',
        is_active: true,
      }),
    };

    await TestBed.configureTestingModule({
      imports: [UserListComponent],
      providers: [
        provideRouter([]),
        { provide: AdminService, useValue: mockAdminService },
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize and call loadUsers', () => {
    expect(mockAdminService.loadUsers).toHaveBeenCalled();
    expect(component.adminService.users().length).toBe(3);
  });

  it('should debounce rapid onSearch calls and dispatch only the latest query after 250ms', () => {
    vi.useFakeTimers();
    mockAdminService.loadUsers.mockClear();

    component.onSearch('a');
    component.onSearch('al');
    component.onSearch('ali');

    expect(component.searchQuery()).toBe('ali');
    expect(component.currentPage()).toBe(1);
    expect(mockAdminService.loadUsers).not.toHaveBeenCalled();

    vi.advanceTimersByTime(250);

    expect(mockAdminService.loadUsers).toHaveBeenCalledTimes(1);
    expect(mockAdminService.loadUsers).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'ali', page: 1 })
    );
    vi.useRealTimers();
  });

  it('should cancel prior in-flight loadUsers request via switchMap when filter changes', () => {
    const first$ = new Subject<AdminUserListResponse>();
    const second$ = new Subject<AdminUserListResponse>();
    let firstUnsubscribed = false;

    mockAdminService.loadUsers.mockReset();
    mockAdminService.loadUsers
      .mockReturnValueOnce(first$.pipe(finalize(() => (firstUnsubscribed = true))))
      .mockReturnValueOnce(second$);

    component.onRoleFilterChange('admin');
    expect(firstUnsubscribed).toBe(false);

    component.onRoleFilterChange('user');
    expect(firstUnsubscribed).toBe(true);
    expect(mockAdminService.loadUsers).toHaveBeenCalledTimes(2);
  });

  it('should reset search query on clearSearch', () => {
    component.searchQuery.set('bob');
    component.clearSearch();
    expect(component.searchQuery()).toBe('');
    expect(component.currentPage()).toBe(1);
  });

  it('should filter by role and reload', () => {
    component.onRoleFilterChange('admin');
    expect(component.roleFilter()).toBe('admin');
    expect(component.currentPage()).toBe(1);
    expect(mockAdminService.loadUsers).toHaveBeenCalled();
  });

  it('should filter by status and reload', () => {
    component.onStatusFilterChange('banned');
    expect(component.statusFilter()).toBe('banned');
    expect(component.currentPage()).toBe(1);
    expect(mockAdminService.loadUsers).toHaveBeenCalled();
  });

  it('should navigate to page on goToPage', () => {
    mockAdminService.totalPages.set(3);
    component.goToPage(2);
    expect(component.currentPage()).toBe(2);
    expect(mockAdminService.loadUsers).toHaveBeenCalled();
  });

  it('should open ban modal and confirm ban with custom reason', () => {
    const targetUser = sampleUsers[1];
    const bannedUser: AdminUser = {
      ...targetUser,
      is_banned: true,
      ban_reason: 'Violated Terms',
    };
    mockAdminService.banUser.mockReturnValue(
      of({
        success: true,
        message: 'User banned',
        user: bannedUser,
      } as AdminActionResponse)
    );

    component.openBanModal(targetUser);
    expect(component.isBanModalOpen()).toBe(true);
    expect(component.targetUser()).toEqual(targetUser);

    component.banReason.set('Violated Terms');
    component.confirmBan();

    expect(mockAdminService.banUser).toHaveBeenCalledWith('user-id-2', 'Violated Terms');
    expect(component.isBanModalOpen()).toBe(false);
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should handle ban error gracefully', () => {
    const targetUser = sampleUsers[1];
    mockAdminService.banUser.mockReturnValue(throwError(() => ({ error: { detail: 'Permission Denied' } })));

    component.openBanModal(targetUser);
    component.confirmBan();

    expect(component.actionMessage()?.type).toBe('error');
    expect(component.actionMessage()?.text).toBe('Permission Denied');
    expect(component.isSubmitting()).toBe(false);
  });

  it('should unban user successfully', () => {
    const bannedUser = sampleUsers[2];
    mockAdminService.unbanUser.mockReturnValue(
      of({
        success: true,
        message: 'User unbanned',
        user: { ...bannedUser, is_banned: false },
      } as AdminActionResponse)
    );

    component.unbanUser(bannedUser);

    expect(mockAdminService.unbanUser).toHaveBeenCalledWith('banned-id-3');
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should allow super_admin to change user role and update', () => {
    const targetUser = sampleUsers[1];
    mockAdminService.updateRole.mockReturnValue(
      of({
        success: true,
        message: 'Role updated',
        user: { ...targetUser, role: 'admin' },
      } as AdminActionResponse)
    );

    const event = { target: { value: 'admin' } } as unknown as Event;
    component.onRoleChange(targetUser, event);

    expect(mockAdminService.updateRole).toHaveBeenCalledWith('user-id-2', 'admin');
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should enforce guardrails: cannot ban self or super_admin', () => {
    // Current user is admin-id-1 (Super Admin User)
    expect(component.canBan(sampleUsers[0])).toBe(false); // Self & Super Admin
    expect(component.canBan(sampleUsers[1])).toBe(true); // Regular user
  });

  it('should enforce guardrails: cannot change own role', () => {
    expect(component.canChangeRole(sampleUsers[0])).toBe(false); // Self
    expect(component.canChangeRole(sampleUsers[1])).toBe(true); // Other user
  });

  it('should hide Unban button when regular admin views a banned admin or super_admin', () => {
    mockAuthService.currentUser.set({
      id: 'regular-admin-1',
      email: 'admin@platform.com',
      role: 'admin',
      is_active: true,
    });
    mockAdminService.users.set([
      {
        ...sampleUsers[0],
        id: 'banned-admin-2',
        role: 'admin',
        is_banned: true,
      },
      {
        ...sampleUsers[2],
        id: 'banned-user-3',
        role: 'user',
        is_banned: true,
      },
    ]);
    fixture.detectChanges();

    const unbanButtons = (fixture.nativeElement as HTMLElement).querySelectorAll('.btn-unban');
    expect(unbanButtons.length).toBe(1);
  });
});
