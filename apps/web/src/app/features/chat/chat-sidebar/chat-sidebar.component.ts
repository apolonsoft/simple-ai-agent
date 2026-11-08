import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession } from '../../../core/models/chat.model';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <aside class="sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" (click)="onNewChat()">
          <span class="btn-icon">+</span>
          <span>New Chat</span>
        </button>
      </div>

      <div class="session-list-container">
        @if (isLoading()) {
          <div class="loading-state">
            <span class="spinner"></span>
            <span>Loading history...</span>
          </div>
        } @else if (sessions().length === 0) {
          <div class="empty-state">
            <span class="empty-icon">💬</span>
            <p>No conversations yet.</p>
            <span class="empty-sub">Start a new chat to begin.</span>
          </div>
        } @else {
          <div class="session-list">
            @for (session of sessions(); track session.id) {
              <div
                class="session-item"
                [class.active]="activeSessionId() === session.id"
                [routerLink]="['/chat', session.id]"
                (click)="onSelect(session.id)"
              >
                <div class="item-content">
                  <span class="chat-icon">💭</span>
                  <span class="session-title" [title]="session.title">{{ session.title }}</span>
                </div>

                <button
                  class="delete-btn"
                  title="Delete chat"
                  (click)="onDelete(session.id, $event)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                  </svg>
                </button>
              </div>
            }
          </div>
        }
      </div>
    </aside>
  `,
  styles: [`
    :host {
      display: block;
      width: 280px;
      min-width: 280px;
      max-width: 280px;
      height: 100%;
      flex-shrink: 0;
      position: relative;
    }
    .sidebar {
      width: 280px;
      min-width: 280px;
      max-width: 280px;
      height: 100%;
      background: #0f172a;
      border-right: 1px solid #1e293b;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      user-select: none;
      overflow: hidden;
    }
    .sidebar-header {
      padding: 1rem;
      border-bottom: 1px solid #1e293b;
      flex-shrink: 0;
    }
    .new-chat-btn {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      background: #1e293b;
      color: #f8fafc;
      border: 1px solid #334155;
      padding: 0.625rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .new-chat-btn:hover {
      background: #334155;
      border-color: #6366f1;
      color: #ffffff;
    }
    .btn-icon {
      font-size: 1.125rem;
      line-height: 1;
    }
    .session-list-container {
      flex: 1 1 0%;
      min-height: 0;
      overflow-y: auto;
      padding: 0.75rem;
      scrollbar-width: thin;
      scrollbar-color: #334155 #0f172a;
    }
    .loading-state, .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1rem;
      color: #64748b;
      text-align: center;
      font-size: 0.875rem;
    }
    .empty-icon {
      font-size: 2rem;
      margin-bottom: 0.5rem;
      opacity: 0.6;
    }
    .empty-sub {
      font-size: 0.75rem;
      color: #475569;
      margin-top: 0.25rem;
    }
    .spinner {
      width: 1.25rem;
      height: 1.25rem;
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-top-color: #6366f1;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-bottom: 0.5rem;
    }
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    .session-list {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    .session-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.625rem 0.75rem;
      border-radius: 0.5rem;
      color: #cbd5e1;
      text-decoration: none;
      font-size: 0.875rem;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }
    .session-item:hover {
      background: #1e293b;
      color: #f8fafc;
    }
    .session-item.active {
      background: #1e1b4b;
      border-left: 3px solid #6366f1;
      color: #ffffff;
      font-weight: 500;
    }
    .item-content {
      display: flex;
      align-items: center;
      gap: 0.625rem;
      min-width: 0;
      flex: 1;
    }
    .chat-icon {
      font-size: 0.875rem;
      flex-shrink: 0;
    }
    .session-title {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .delete-btn {
      opacity: 0;
      background: transparent;
      border: none;
      color: #64748b;
      cursor: pointer;
      padding: 0.25rem;
      border-radius: 0.25rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: opacity 0.15s, color 0.15s;
    }
    .session-item:hover .delete-btn {
      opacity: 1;
    }
    .delete-btn:hover {
      color: #ef4444;
      background: rgba(239, 68, 68, 0.1);
    }
  `]
})
export class ChatSidebarComponent implements OnInit {
  private readonly chatService = inject(ChatService);

  readonly sessions = this.chatService.sessions;
  readonly activeSessionId = this.chatService.activeSessionId;
  readonly isLoading = this.chatService.isLoadingSessions;

  ngOnInit(): void {
    this.chatService.loadSessions().subscribe();
  }

  onNewChat(): void {
    this.chatService.createSession().subscribe();
  }

  onSelect(id: string): void {
    this.chatService.selectSession(id);
  }

  onDelete(id: string, event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    this.chatService.deleteSession(id).subscribe();
  }
}
