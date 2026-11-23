import { ChangeDetectionStrategy, Component, inject, computed } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ChatSidebarComponent } from '../chat-sidebar/chat-sidebar.component';

@Component({
  selector: 'app-chat-layout',
  standalone: true,
  imports: [RouterOutlet, RouterLink, ChatSidebarComponent],
  templateUrl: './chat-layout.component.html',
  styleUrl: './chat-layout.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatLayoutComponent {
  private readonly authService = inject(AuthService);

  readonly currentUser = this.authService.currentUser;
  readonly isAdminOrSuperAdmin = computed(() => {
    const role = this.currentUser()?.role;
    return role === 'admin' || role === 'super_admin';
  });

  onLogout(): void {
    this.authService.logout();
  }
}
