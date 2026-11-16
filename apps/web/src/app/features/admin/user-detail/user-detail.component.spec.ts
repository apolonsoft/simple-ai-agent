import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserDetailComponent } from './user-detail.component';
import { AdminService } from '../../../core/services/admin.service';
import { AuthService } from '../../../core/services/auth.service';
import { AdminUserDetail, AdminActionResponse } from '../../../core/models/admin.model';
import { User } from '../../../core/models/user.model';

describe('UserDetailComponent', () => {
  let component: UserDetailComponent;
  let fixture: ComponentFixture<UserDetailComponent>;

  let mockAdminService: {
    selectedUser: ReturnType<typeof signal<AdminUserDetail | null>>;
    isLoading: ReturnType<typeof signal<boolean>>;
    error: ReturnType<typeof signal<string | null>>;
    getUserDetail: ReturnType<typeof vi.fn>;
    banUser: ReturnType<typeof vi.fn>;
    unbanUser: ReturnType<typeof vi.fn>;
    updateRole: ReturnType<typeof vi.fn>;
  };

  let mockAuthService: {
    currentUser: ReturnType<typeof signal<User | null>>;
  };

  const sampleUserDetail: AdminUserDetail = {
    id: 'user-uuid-123',
    email: 'charlie@example.com',
    full_name: 'Charlie Brown',
    avatar_url: null,
    bio: 'Software engineer and enthusiast.',
    role: 'user',
    is_active: true,
    is_banned: false,
    banned_at: null,
    ban_reason: null,
    chat_sessions_count: 14,
    created_at: '2026-01-15T08:00:00Z',
    updated_at: '2026-02-01T09:30:00Z',
  };

  beforeEach(async () => {
    mockAdminService = {
      selectedUser: signal<AdminUserDetail | null>(sampleUserDetail),
      isLoading: signal<boolean>(false),
      error: signal<string | null>(null),
      getUserDetail: vi.fn().mockReturnValue(of(sampleUserDetail)),
      banUser: vi.fn(),
      unbanUser: vi.fn(),
      updateRole: vi.fn(),
    };

    mockAuthService = {
      currentUser: signal<User | null>({
        id: 'admin-uuid-999',
        email: 'superadmin@example.com',
        role: 'super_admin',
        is_active: true,
      }),
    };

    await TestBed.configureTestingModule({
      imports: [UserDetailComponent],
      providers: [
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? 'user-uuid-123' : null),
              },
            },
          },
        },
        { provide: AdminService, useValue: mockAdminService },
        { provide: AuthService, useValue: mockAuthService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize and load user detail by route id', () => {
    expect(component.userId()).toBe('user-uuid-123');
    expect(mockAdminService.getUserDetail).toHaveBeenCalledWith('user-uuid-123');
    expect(component.user()?.email).toBe('charlie@example.com');
    expect(component.user()?.chat_sessions_count).toBe(14);
  });

  it('should open ban modal and confirm ban', () => {
    const bannedUser: AdminUserDetail = {
      ...sampleUserDetail,
      is_banned: true,
      ban_reason: 'Abuse of platform',
      banned_at: '2026-02-05T10:00:00Z',
    };

    mockAdminService.banUser.mockReturnValue(
      of({
        success: true,
        message: 'Banned',
        user: bannedUser,
      } as AdminActionResponse)
    );

    component.openBanModal();
    expect(component.isBanModalOpen()).toBe(true);

    component.banReason.set('Abuse of platform');
    component.confirmBan();

    expect(mockAdminService.banUser).toHaveBeenCalledWith('user-uuid-123', 'Abuse of platform');
    expect(component.isBanModalOpen()).toBe(false);
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should unban user successfully', () => {
    const bannedState: AdminUserDetail = {
      ...sampleUserDetail,
      is_banned: true,
      ban_reason: 'Abuse',
    };
    mockAdminService.selectedUser.set(bannedState);

    const unbannedUser: AdminUserDetail = {
      ...sampleUserDetail,
      is_banned: false,
      ban_reason: null,
      banned_at: null,
    };
    mockAdminService.unbanUser.mockReturnValue(
      of({
        success: true,
        message: 'Unbanned',
        user: unbannedUser,
      } as AdminActionResponse)
    );

    component.unbanUser();

    expect(mockAdminService.unbanUser).toHaveBeenCalledWith('user-uuid-123');
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should change user role when super_admin', () => {
    const updatedUser: AdminUserDetail = {
      ...sampleUserDetail,
      role: 'admin',
    };
    mockAdminService.updateRole.mockReturnValue(
      of({
        success: true,
        message: 'Role updated',
        user: updatedUser,
      } as AdminActionResponse)
    );

    const event = { target: { value: 'admin' } } as unknown as Event;
    component.onRoleChange(event);

    expect(mockAdminService.updateRole).toHaveBeenCalledWith('user-uuid-123', 'admin');
    expect(component.actionMessage()?.type).toBe('success');
  });

  it('should enforce guardrails: cannot ban or change role for self', () => {
    // Set selected user to current user
    mockAdminService.selectedUser.set({
      ...sampleUserDetail,
      id: 'admin-uuid-999',
      role: 'super_admin',
    });

    expect(component.canBan()).toBe(false);
    expect(component.canChangeRole()).toBe(false);
  });

  it('should handle ban error', () => {
    mockAdminService.banUser.mockReturnValue(
      throwError(() => ({ error: { detail: 'Cannot ban user' } }))
    );

    component.openBanModal();
    component.confirmBan();

    expect(component.actionMessage()?.type).toBe('error');
    expect(component.actionMessage()?.text).toBe('Cannot ban user');
    expect(component.isSubmitting()).toBe(false);
  });
});
