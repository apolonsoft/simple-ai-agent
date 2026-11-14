import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { UserService } from '../../core/services/user.service';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss',
})
export class ProfileComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly userService = inject(UserService);
  readonly authService = inject(AuthService);

  readonly user = computed(() => this.authService.currentUser());
  readonly isLoading = signal<boolean>(false);
  readonly isSaving = signal<boolean>(false);
  readonly isUploadingAvatar = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly profileForm: FormGroup = this.fb.group({
    full_name: ['', [Validators.maxLength(100)]],
    bio: ['', [Validators.maxLength(500)]],
  });

  ngOnInit(): void {
    this.loadProfile();
  }

  loadProfile(): void {
    this.isLoading.set(true);
    this.userService.getProfile().subscribe({
      next: (user) => {
        this.isLoading.set(false);
        this.profileForm.patchValue({
          full_name: user.full_name || '',
          bio: user.bio || '',
        });
      },
      error: (err) => {
        this.isLoading.set(false);
        const detail = err.error?.detail || err.message || 'Failed to load user profile.';
        this.errorMessage.set(detail);
      },
    });
  }

  onSubmit(): void {
    if (this.profileForm.invalid) {
      this.profileForm.markAllAsTouched();
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const { full_name, bio } = this.profileForm.value;
    this.userService.updateProfile({ full_name: full_name?.trim() || null, bio: bio?.trim() || null }).subscribe({
      next: () => {
        this.isSaving.set(false);
        this.successMessage.set('Profile updated successfully.');
      },
      error: (err) => {
        this.isSaving.set(false);
        const detail = err.error?.detail || err.message || 'Failed to update profile.';
        this.errorMessage.set(detail);
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) {
      return;
    }

    const file = input.files[0];
    this.isUploadingAvatar.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    this.userService.uploadAvatar(file).subscribe({
      next: () => {
        this.isUploadingAvatar.set(false);
        this.successMessage.set('Avatar image updated successfully.');
        input.value = '';
      },
      error: (err) => {
        this.isUploadingAvatar.set(false);
        const detail = err.error?.detail || err.message || 'Failed to upload avatar image.';
        this.errorMessage.set(detail);
        input.value = '';
      },
    });
  }

  dismissAlerts(): void {
    this.errorMessage.set(null);
    this.successMessage.set(null);
  }
}
