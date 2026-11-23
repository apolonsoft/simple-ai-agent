import { ChangeDetectionStrategy, Component, DestroyRef, OnInit, inject, input, signal, computed } from '@angular/core';
import { DatePipe, NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { EMPTY, catchError, distinctUntilChanged, filter, map, merge, of, switchMap, tap } from 'rxjs';
import { AdminService } from '../../../core/services/admin.service';
import { AuthService } from '../../../core/services/auth.service';
import { UserRole } from '../../../core/models/admin.model';
import { canModerateUser, canChangeUserRole } from '../../../core/utils/admin-permissions';
import { BanUserModalComponent } from '../ban-user-modal/ban-user-modal.component';

@Component({
  selector: 'app-user-detail',
  standalone: true,
  imports: [NgClass, DatePipe, FormsModule, RouterLink, BanUserModalComponent],
  templateUrl: './user-detail.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserDetailComponent implements OnInit {
  readonly adminService = inject(AdminService);
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  readonly id = input<string | null>(null);
  private readonly id$ = toObservable(this.id);

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

  readonly canBan = computed(() => canModerateUser(this.currentUser(), this.user()));

  readonly canChangeRole = computed(() => canChangeUserRole(this.currentUser(), this.user()));

  ngOnInit(): void {
    const routeParam$ = this.route.paramMap
      ? this.route.paramMap.pipe(map((params) => params.get('id')))
      : of(this.route.snapshot?.paramMap?.get('id') ?? null);

    merge(this.id$, routeParam$)
      .pipe(
        filter((id): id is string => Boolean(id)),
        distinctUntilChanged(),
        tap((id) => this.userId.set(id)),
        switchMap((id) =>
          this.adminService.getUserDetail(id).pipe(
            catchError((err) => {
              this.showToast('error', err?.error?.detail || 'Failed to load user details');
              return EMPTY;
            })
          )
        ),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe();
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

  confirmBan(reason: string = this.banReason()): void {
    const u = this.user();
    if (!u) return;

    this.isSubmitting.set(true);
    this.adminService.banUser(u.id, reason.trim()).subscribe({
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
