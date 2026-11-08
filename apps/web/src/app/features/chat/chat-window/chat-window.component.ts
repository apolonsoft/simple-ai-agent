import { Component, inject, input, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatService } from '../../../core/services/chat.service';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="chat-window-container">
      @if (sessionId()) {
        <div class="chat-header">
          <h2>{{ currentSession()?.title || 'Conversation' }}</h2>
          <span class="session-id-tag">ID: {{ sessionId() }}</span>
        </div>
        <div class="messages-viewport">
          <div class="welcome-box">
            <h3>Connected to Session</h3>
            <p>Start exchanging messages with the model.</p>
          </div>
        </div>
      } @else {
        <div class="no-session-selected">
          <div class="empty-hero">
            <span class="hero-icon">✨</span>
            <h2>Select or create a conversation</h2>
            <p>Choose a chat from the sidebar or click "+ New Chat" to start.</p>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .chat-window-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100%;
      background: #0b1120;
      color: #f1f5f9;
      position: relative;
    }
    .chat-header {
      height: 3.5rem;
      border-bottom: 1px solid #1e293b;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.5rem;
      background: #0f172a;
      flex-shrink: 0;
    }
    .chat-header h2 {
      font-size: 1rem;
      font-weight: 600;
      margin: 0;
      color: #f8fafc;
    }
    .session-id-tag {
      font-size: 0.75rem;
      color: #64748b;
      font-family: monospace;
    }
    .messages-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .welcome-box {
      text-align: center;
      color: #94a3b8;
    }
    .no-session-selected {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .empty-hero {
      text-align: center;
      max-width: 360px;
    }
    .hero-icon {
      font-size: 3rem;
      display: block;
      margin-bottom: 1rem;
    }
    .empty-hero h2 {
      font-size: 1.25rem;
      font-weight: 700;
      color: #f8fafc;
      margin: 0 0 0.5rem 0;
    }
    .empty-hero p {
      font-size: 0.875rem;
      color: #64748b;
      margin: 0;
    }
  `]
})
export class ChatWindowComponent {
  private readonly chatService = inject(ChatService);

  // Bound from route parameter :sessionId
  readonly sessionId = input<string | null>(null);
  readonly currentSession = this.chatService.activeSession;

  constructor() {
    effect(() => {
      const id = this.sessionId();
      this.chatService.selectSession(id);
    });
  }
}
