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
        provideRouter([]),
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
});
