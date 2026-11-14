import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ProfileComponent } from './profile.component';
import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';
import { User } from '../../core/models/user.model';

describe('ProfileComponent', () => {
  let component: ProfileComponent;
  let fixture: ComponentFixture<ProfileComponent>;
  let mockUserService: {
    getProfile: ReturnType<typeof vi.fn>;
    updateProfile: ReturnType<typeof vi.fn>;
    uploadAvatar: ReturnType<typeof vi.fn>;
  };
  let authService: AuthService;

  const mockUser: User = {
    id: 'user-uuid-1',
    email: 'profile_tester@example.com',
    role: 'user',
    is_active: true,
    full_name: 'Test Tester',
    avatar_url: 'http://localhost:8333/avatars/test.png',
    bio: 'Test bio description',
  };

  beforeEach(async () => {
    mockUserService = {
      getProfile: vi.fn().mockReturnValue(of(mockUser)),
      updateProfile: vi.fn().mockReturnValue(of({ ...mockUser, full_name: 'New Name' })),
      uploadAvatar: vi.fn().mockReturnValue(of({ ...mockUser, avatar_url: 'http://localhost:8333/avatars/new.png' })),
    };

    await TestBed.configureTestingModule({
      imports: [ProfileComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: 'login', component: class {} },
          { path: 'chat', component: class {} },
        ]),
        { provide: UserService, useValue: mockUserService },
        AuthService,
      ],
    }).compileComponents();

    authService = TestBed.inject(AuthService);
    authService.currentUser.set(mockUser);

    fixture = TestBed.createComponent(ProfileComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component and populate form on init', () => {
    expect(component).toBeTruthy();
    expect(mockUserService.getProfile).toHaveBeenCalled();
    expect(component.profileForm.value.full_name).toBe('Test Tester');
    expect(component.profileForm.value.bio).toBe('Test bio description');
  });

  it('should successfully submit form and display success message', () => {
    component.profileForm.patchValue({
      full_name: 'New Name',
      bio: 'New Bio',
    });

    component.onSubmit();

    expect(mockUserService.updateProfile).toHaveBeenCalledWith({
      full_name: 'New Name',
      bio: 'New Bio',
    });
    expect(component.isSaving()).toBe(false);
    expect(component.successMessage()).toBe('Profile updated successfully.');
  });

  it('should not submit if form is invalid', () => {
    component.profileForm.patchValue({
      full_name: 'A'.repeat(105), // Exceeds 100 chars
    });

    component.onSubmit();

    expect(mockUserService.updateProfile).not.toHaveBeenCalled();
    expect(component.profileForm.invalid).toBe(true);
  });

  it('should handle avatar file upload successfully', () => {
    const fakeFile = new File(['content'], 'avatar.png', { type: 'image/png' });
    const event = {
      target: {
        files: [fakeFile],
        value: 'fake-path',
      },
    } as unknown as Event;

    component.onFileSelected(event);

    expect(mockUserService.uploadAvatar).toHaveBeenCalledWith(fakeFile);
    expect(component.isUploadingAvatar()).toBe(false);
    expect(component.successMessage()).toBe('Avatar image updated successfully.');
  });

  it('should handle avatar file upload error', () => {
    mockUserService.uploadAvatar.mockReturnValue(throwError(() => new Error('Image too large')));

    const fakeFile = new File(['content'], 'avatar.png', { type: 'image/png' });
    const event = {
      target: {
        files: [fakeFile],
        value: 'fake-path',
      },
    } as unknown as Event;

    component.onFileSelected(event);

    expect(component.isUploadingAvatar()).toBe(false);
    expect(component.errorMessage()).toBe('Image too large');
  });

  it('should calculate password strength score dynamically', () => {
    // Empty
    component.passwordForm.patchValue({ new_password: '' });
    expect(component.passwordStrength.score).toBe(0);

    // Too short (< 6 chars)
    component.passwordForm.patchValue({ new_password: 'abc' });
    expect(component.passwordStrength.score).toBe(1);
    expect(component.passwordStrength.label).toBe('Too short');

    // 6 chars simple
    component.passwordForm.patchValue({ new_password: 'simple' });
    expect(component.passwordStrength.score).toBe(1);
    expect(component.passwordStrength.label).toBe('Weak');

    // Length >= 8
    component.passwordForm.patchValue({ new_password: 'simplelong' });
    expect(component.passwordStrength.score).toBe(2);
    expect(component.passwordStrength.label).toBe('Fair');

    // Length >= 8 with uppercase + lowercase
    component.passwordForm.patchValue({ new_password: 'SimpleLong' });
    expect(component.passwordStrength.score).toBe(3);
    expect(component.passwordStrength.label).toBe('Good');

    // Length >= 8, mixed case, number and symbol
    component.passwordForm.patchValue({ new_password: 'SimpleLong123!' });
    expect(component.passwordStrength.score).toBe(4);
    expect(component.passwordStrength.label).toBe('Strong');
  });

  it('should invalidate passwordForm when passwords do not match', () => {
    component.passwordForm.patchValue({
      current_password: 'CurrentPassword123',
      new_password: 'NewPassword123!',
      confirm_password: 'DifferentPassword456!',
    });

    expect(component.passwordForm.hasError('passwordMismatch')).toBe(true);
    expect(component.passwordForm.invalid).toBe(true);

    const changePasswordSpy = vi.spyOn(authService, 'changePassword');
    component.onChangePassword();
    expect(changePasswordSpy).not.toHaveBeenCalled();
  });

  it('should submit password change and schedule logout after delay', () => {
    vi.useFakeTimers();
    const changePasswordSpy = vi.spyOn(authService, 'changePassword').mockReturnValue(
      of({ message: 'Password changed successfully.' })
    );
    const logoutSpy = vi.spyOn(authService, 'logout');

    component.passwordForm.patchValue({
      current_password: 'CurrentPassword123',
      new_password: 'NewPassword123!',
      confirm_password: 'NewPassword123!',
    });

    component.onChangePassword();

    expect(changePasswordSpy).toHaveBeenCalledWith({
      current_password: 'CurrentPassword123',
      new_password: 'NewPassword123!',
    });
    expect(component.passwordSuccessMessage()).toContain('Password changed successfully');

    // Fast-forward timers by 2 seconds
    vi.advanceTimersByTime(2000);
    expect(logoutSpy).toHaveBeenCalled();

    vi.useRealTimers();
  });

  it('should display error message when change password fails', () => {
    vi.spyOn(authService, 'changePassword').mockReturnValue(
      throwError(() => ({ error: { detail: 'Current password is incorrect.' } }))
    );

    component.passwordForm.patchValue({
      current_password: 'WrongCurrentPassword',
      new_password: 'NewPassword123!',
      confirm_password: 'NewPassword123!',
    });

    component.onChangePassword();

    expect(component.isChangingPassword()).toBe(false);
    expect(component.passwordErrorMessage()).toBe('Current password is incorrect.');
  });
});
