import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { ChatSidebarComponent } from '../chat-sidebar/chat-sidebar.component';

@Component({
  selector: 'app-chat-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ChatSidebarComponent],
  template: `
    <div class="layout-wrapper">
      <!-- Top Navigation Bar -->
      <header class="top-nav">
        <div class="brand">
          <span class="brand-icon">⚡</span>
          <span class="brand-title">Enterprise AI Agent</span>
          <span class="status-badge">Online</span>
        </div>

        <div class="user-actions">
          @if (currentUser(); as user) {
            <div class="user-chip">
              <span class="user-avatar">{{ user.email[0].toUpperCase() }}</span>
              <span class="user-email">{{ user.email }}</span>
            </div>
          }

          <button class="logout-btn" (click)="onLogout()" title="Sign out">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            <span>Sign Out</span>
          </button>
        </div>
      </header>

      <!-- Main Layout Body: Sidebar + Dynamic Chat Viewport -->
      <div class="layout-body">
        <app-chat-sidebar></app-chat-sidebar>
        <div class="chat-viewport">
          <router-outlet></router-outlet>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
      width: 100vw;
      overflow: hidden;
    }
    .layout-wrapper {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100vw;
      background: #090d16;
      color: #f3f4f6;
      overflow: hidden;
      position: fixed;
      inset: 0;
      font-family: inherit;
    }
    .top-nav {
      height: 3.5rem;
      min-height: 3.5rem;
      background: #0f172a;
      border-bottom: 1px solid #1e293b;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.25rem;
      flex-shrink: 0;
      z-index: 20;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.625rem;
    }
    .brand-icon {
      font-size: 1.25rem;
    }
    .brand-title {
      font-weight: 700;
      font-size: 1rem;
      letter-spacing: -0.01em;
      color: #f8fafc;
    }
    .status-badge {
      font-size: 0.6875rem;
      font-weight: 600;
      background: rgba(34, 197, 94, 0.15);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.3);
      padding: 0.125rem 0.5rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .user-actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .user-chip {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: #1e293b;
      padding: 0.25rem 0.75rem 0.25rem 0.375rem;
      border-radius: 9999px;
      border: 1px solid #334155;
    }
    .user-avatar {
      width: 1.5rem;
      height: 1.5rem;
      border-radius: 9999px;
      background: #4f46e5;
      color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .user-email {
      font-size: 0.8125rem;
      color: #cbd5e1;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .logout-btn {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      background: transparent;
      border: 1px solid #334155;
      color: #94a3b8;
      padding: 0.375rem 0.75rem;
      border-radius: 0.375rem;
      font-size: 0.8125rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.15s;
    }
    .logout-btn:hover {
      background: rgba(239, 68, 68, 0.1);
      border-color: rgba(239, 68, 68, 0.3);
      color: #f87171;
    }
    .layout-body {
      flex: 1 1 0%;
      height: calc(100vh - 3.5rem);
      width: 100vw;
      display: flex;
      overflow: hidden;
      position: relative;
    }
    app-chat-sidebar {
      width: 280px;
      min-width: 280px;
      max-width: 280px;
      height: 100%;
      flex-shrink: 0;
      z-index: 15;
    }
    .chat-viewport {
      flex: 1 1 0%;
      min-width: 0;
      min-height: 0;
      height: 100%;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }
  `]
})
export class ChatLayoutComponent {
  private readonly authService = inject(AuthService);

  readonly currentUser = this.authService.currentUser;

  onLogout(): void {
    this.authService.logout();
  }
}
