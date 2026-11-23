import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, signal, computed } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { EMPTY, Subject, catchError, debounceTime, distinctUntilChanged, merge, switchMap } from 'rxjs';
import { AdminService } from '../../../core/services/admin.service';
import { AuthService } from '../../../core/services/auth.service';
import { AdminUser, UserRole } from '../../../core/models/admin.model';
import { canModerateUser, canChangeUserRole } from '../../../core/utils/admin-permissions';
import { BanUserModalComponent } from '../ban-user-modal/ban-user-modal.component';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [NgClass, DatePipe, FormsModule, RouterLink, BanUserModalComponent],
  templateUrl: './user-list.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserListComponent implements OnInit {
  readonly adminService = inject(AdminService);
  private readonly authService = inject(AuthService);
  private readonly destroyRef = inject(DestroyRef);

  private readonly searchInput$ = new Subject<string>();
  private readonly reload$ = new Subject<void>();

  // Filter & pagination state
  readonly searchQuery = signal<string>('');
  readonly roleFilter = signal<string>('all');
  readonly statusFilter = signal<string>('all');
  readonly currentPage = signal<number>(1);
  readonly pageSize = signal<number>(20);

  // Toast / feedback message
  readonly actionMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Ban confirmation modal state
  readonly isBanModalOpen = signal<boolean>(false);
  readonly targetUser = signal<AdminUser | null>(null);
  readonly banReason = signal<string>('');
  readonly isSubmitting = signal<boolean>(false);

  // Auth computed helpers
  readonly currentUser = this.authService.currentUser;
  readonly isSuperAdmin = computed(() => this.currentUser()?.role === 'super_admin');
  readonly currentUserId = computed(() => this.currentUser()?.id);

  ngOnInit(): void {
    merge(
      this.searchInput$.pipe(debounceTime(250), distinctUntilChanged()),
      this.reload$
    )
      .pipe(
        switchMap(() =>
          this.adminService
            .loadUsers({
              page: this.currentPage(),
              limit: this.pageSize(),
              search: this.searchQuery(),
              role: this.roleFilter() === 'all' ? undefined : this.roleFilter(),
              status: this.statusFilter() === 'all' ? undefined : this.statusFilter(),
            })
            .pipe(
              catchError((err) => {
                this.showToast('error', err?.error?.detail || 'Failed to load users');
                return EMPTY;
              })
            )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe();

    this.loadUsers();
  }

  loadUsers(): void {
    this.reload$.next();
  }

  onSearch(query: string): void {
    this.searchQuery.set(query);
    this.currentPage.set(1);
    this.searchInput$.next(query);
  }

  clearSearch(): void {
    this.searchQuery.set('');
    this.currentPage.set(1);
    this.loadUsers();
  }

  onRoleFilterChange(role: string): void {
    this.roleFilter.set(role);
    this.currentPage.set(1);
    this.loadUsers();
  }

  onStatusFilterChange(status: string): void {
    this.statusFilter.set(status);
    this.currentPage.set(1);
    this.loadUsers();
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.adminService.totalPages()) {
      this.currentPage.set(page);
      this.loadUsers();
    }
  }

  canBan(user: AdminUser): boolean {
    return canModerateUser(this.currentUser(), user);
  }

  canChangeRole(user: AdminUser): boolean {
    return canChangeUserRole(this.currentUser(), user);
  }

  openBanModal(user: AdminUser): void {
    this.targetUser.set(user);
    this.banReason.set('');
    this.isBanModalOpen.set(true);
  }

  closeBanModal(): void {
    this.isBanModalOpen.set(false);
    this.targetUser.set(null);
    this.banReason.set('');
    this.isSubmitting.set(false);
  }

  confirmBan(reason: string = this.banReason()): void {
    const target = this.targetUser();
    if (!target) return;

    this.isSubmitting.set(true);
    this.adminService.banUser(target.id, reason.trim()).subscribe({
      next: () => {
        this.showToast('success', `User ${target.email} has been banned.`);
        this.closeBanModal();
      },
      error: (err) => {
        this.isSubmitting.set(false);
        this.showToast('error', err?.error?.detail || 'Failed to ban user');
      },
    });
  }

  unbanUser(user: AdminUser): void {
    this.adminService.unbanUser(user.id).subscribe({
      next: () => {
        this.showToast('success', `Access restored for ${user.email}.`);
      },
      error: (err) => {
        this.showToast('error', err?.error?.detail || 'Failed to unban user');
      },
    });
  }

  onRoleChange(user: AdminUser, event: Event): void {
    const target = event.target as HTMLSelectElement;
    const newRole = target.value as UserRole;
    if (newRole === user.role) return;

    this.adminService.updateRole(user.id, newRole).subscribe({
      next: () => {
        this.showToast('success', `Role for ${user.email} updated to ${newRole}.`);
      },
      error: (err) => {
        target.value = user.role; // Revert select on error
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
