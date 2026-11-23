import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { AdminService } from '../../../core/services/admin.service';
import { AuthService } from '../../../core/services/auth.service';
import { UserRole } from '../../../core/models/admin.model';
import { canBanUser, canChangeUserRole } from '../../../core/utils/admin-permissions';

@Component({
  selector: 'app-user-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './user-detail.component.html',
})
export class UserDetailComponent implements OnInit {
  readonly adminService = inject(AdminService);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  readonly userId = signal<string | null>(null);
  readonly actionMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Ban confirmation modal state
  readonly isBanModalOpen = signal<boolean>(false);
  readonly banReason = signal<string>('');
  readonly isSubmitting = signal<boolean>(false);

  // User and auth signals
  readonly user = this.adminService.selectedUser;
  readonly currentUser = this.authService.currentUser;
  readonly isSuperAdmin = computed(() => this.currentUser()?.role === 'super_admin');
  readonly currentUserId = computed(() => this.currentUser()?.id);

  readonly canBan = computed(() => canBanUser(this.currentUser(), this.user()));

  readonly canChangeRole = computed(() => canChangeUserRole(this.currentUser(), this.user()));

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.userId.set(id);
      this.loadUser(id);
    }
  }

  loadUser(id: string): void {
    this.adminService.getUserDetail(id).subscribe({
      error: (err) => {
        this.showToast('error', err?.error?.detail || 'Failed to load user details');
      },
    });
  }

  openBanModal(): void {
    this.banReason.set('');
    this.isBanModalOpen.set(true);
  }

  closeBanModal(): void {
    this.isBanModalOpen.set(false);
    this.banReason.set('');
    this.isSubmitting.set(false);
  }

  confirmBan(): void {
    const u = this.user();
    if (!u) return;

    this.isSubmitting.set(true);
    this.adminService.banUser(u.id, this.banReason().trim()).subscribe({
      next: () => {
        this.showToast('success', `User ${u.email} has been banned.`);
        this.closeBanModal();
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.showToast('error', err?.error?.detail || 'Failed to ban user');
      },
    });
  }

  unbanUser(): void {
    const u = this.user();
    if (!u) return;

    this.adminService.unbanUser(u.id).subscribe({
      next: () => {
        this.showToast('success', `Access restored for ${u.email}.`);
      },
      error: (err) => {
        this.showToast('error', err?.error?.detail || 'Failed to unban user');
      },
    });
  }

  onRoleChange(event: Event): void {
    const u = this.user();
    if (!u || !this.canChangeRole()) return;

    const target = event.target as HTMLSelectElement;
    const newRole = target.value as UserRole;
    if (newRole === u.role) return;

    this.adminService.updateRole(u.id, newRole).subscribe({
      next: () => {
        this.showToast('success', `Role for ${u.email} updated to ${newRole}.`);
      },
      error: (err) => {
        target.value = u.role;
        this.showToast('error', err?.error?.detail || 'Failed to update user role');
      },
    });
  }

  showToast(type: 'success' | 'error', text: string): void {
    this.actionMessage.set({ type, text });
  }

  dismissToast(): void {
    this.actionMessage.set(null);
  }
}
