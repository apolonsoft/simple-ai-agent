import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap, throwError } from 'rxjs';
import { User, UserProfileUpdate } from '../models/user.model';
import { AuthService } from './auth.service';

export const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
export const ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  getProfile(): Observable<User> {
    return this.http.get<User>('/api/v1/users/me').pipe(
      tap((user) => this.authService.currentUser.set(user))
    );
  }

  updateProfile(data: UserProfileUpdate): Observable<User> {
    return this.http.patch<User>('/api/v1/users/me', data).pipe(
      tap((user) => this.authService.currentUser.set(user))
    );
  }

  uploadAvatar(file: File): Observable<User> {
    if (!file) {
      return throwError(() => new Error('No file selected'));
    }

    if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
      return throwError(
        () => new Error('Invalid image format. Supported formats: JPEG, PNG, WebP')
      );
    }

    if (file.size > MAX_AVATAR_SIZE_BYTES) {
      return throwError(
        () => new Error('Image exceeds maximum allowed size of 5MB')
      );
    }

    const formData = new FormData();
    formData.append('file', file, file.name);

    return this.http.post<User>('/api/v1/users/me/avatar', formData).pipe(
      tap((user) => this.authService.currentUser.set(user))
    );
  }
}
