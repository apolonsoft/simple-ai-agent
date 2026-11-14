import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { UserService } from './user.service';
import { AuthService } from './auth.service';
import { User, UserProfileUpdate } from '../models/user.model';

describe('UserService', () => {
  let service: UserService;
  let authService: AuthService;
  let httpTestingController: HttpTestingController;

  const mockUser: User = {
    id: 'user-uuid-1',
    email: 'test@example.com',
    role: 'user',
    is_active: true,
    full_name: 'Original Name',
    avatar_url: null,
    bio: 'Original bio',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        AuthService,
        UserService,
        { provide: Router, useValue: { navigate: vi.fn() } },
      ],
    });

    service = TestBed.inject(UserService);
    authService = TestBed.inject(AuthService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should fetch profile via GET /api/v1/users/me and update authService.currentUser', () => {
    service.getProfile().subscribe((user) => {
      expect(user).toEqual(mockUser);
      expect(authService.currentUser()).toEqual(mockUser);
    });

    const req = httpTestingController.expectOne('/api/v1/users/me');
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });

  it('should update profile via PATCH /api/v1/users/me and update authService.currentUser', () => {
    const updatePayload: UserProfileUpdate = {
      full_name: 'Updated Name',
      bio: 'Updated Bio',
    };
    const updatedUser: User = {
      ...mockUser,
      full_name: 'Updated Name',
      bio: 'Updated Bio',
    };

    service.updateProfile(updatePayload).subscribe((user) => {
      expect(user).toEqual(updatedUser);
      expect(authService.currentUser()).toEqual(updatedUser);
    });

    const req = httpTestingController.expectOne('/api/v1/users/me');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(updatePayload);
    req.flush(updatedUser);
  });

  it('should upload avatar via POST /api/v1/users/me/avatar and update authService.currentUser', () => {
    const fakeFile = new File(['fake-png-content'], 'avatar.png', { type: 'image/png' });
    const updatedUser: User = {
      ...mockUser,
      avatar_url: 'http://localhost:8333/avatars/new-avatar.png',
    };

    service.uploadAvatar(fakeFile).subscribe((user) => {
      expect(user).toEqual(updatedUser);
      expect(authService.currentUser()).toEqual(updatedUser);
    });

    const req = httpTestingController.expectOne('/api/v1/users/me/avatar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body instanceof FormData).toBe(true);
    req.flush(updatedUser);
  });

  it('should reject avatar with unsupported MIME type without making HTTP request', () => {
    const textFile = new File(['text content'], 'file.txt', { type: 'text/plain' });

    let errorReceived: Error | null = null;
    service.uploadAvatar(textFile).subscribe({
      next: () => { throw new Error('Should not succeed'); },
      error: (err) => { errorReceived = err; },
    });

    expect(errorReceived).not.toBeNull();
    expect((errorReceived as any)?.message).toContain('Invalid image format');
    httpTestingController.expectNone('/api/v1/users/me/avatar');
  });

  it('should reject avatar larger than 5MB without making HTTP request', () => {
    const largeBlob = new Uint8Array(6 * 1024 * 1024);
    const largeFile = new File([largeBlob], 'huge.png', { type: 'image/png' });

    let errorReceived: any = null;
    service.uploadAvatar(largeFile).subscribe({
      next: () => { throw new Error('Should not succeed'); },
      error: (err) => { errorReceived = err; },
    });

    expect(errorReceived).not.toBeNull();
    expect((errorReceived as any)?.message).toContain('exceeds maximum allowed size');
    httpTestingController.expectNone('/api/v1/users/me/avatar');
  });
});
