import {
  Component,
  inject,
  input,
  effect,
  ViewChild,
  ElementRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../../core/services/chat.service';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  template: `
    <div class="chat-window-container">
      @if (sessionId(); as sid) {
        <!-- Top Session Context Bar -->
        <header class="chat-header">
          <div class="session-info">
            <h2>{{ currentSession()?.title || 'Active Conversation' }}</h2>
            <span class="session-id-tag">Thread: {{ sid }}</span>
          </div>

          <div class="header-status">
            <span class="status-indicator"></span>
            <span class="status-text">LLM Streaming Active</span>
          </div>
        </header>

        <!-- Message History Viewport -->
        <div class="messages-viewport" #messagesContainer>
          @if (isLoadingMessages()) {
            <div class="loading-state">
              <div class="spinner"></div>
              <span>Retrieving thread memory...</span>
            </div>
          } @else if (messages().length === 0) {
            <div class="empty-conversation">
              <div class="empty-badge">🚀 Enterprise Pluggable Agent</div>
              <h3>How can I assist you today?</h3>
              <p>Ask anything about architecture, code reviews, debugging, or system design.</p>
              
              <div class="quick-prompts">
                <button class="quick-chip" (click)="setQuickPrompt('Explain how PostgreSQL connection pooling prevents LLM starvation.')">
                  💡 Connection Pooling Architecture
                </button>
                <button class="quick-chip" (click)="setQuickPrompt('Review the async sliding-window rate limiter in Redis.')">
                  ⚡ Redis Rate Limiter Deep Dive
                </button>
                <button class="quick-chip" (click)="setQuickPrompt('Help me write an automated integration test in Vitest.')">
                  🧪 Test Automation Guidance
                </button>
              </div>
            </div>
          } @else {
            <div class="message-feed">
              @for (msg of messages(); track $index) {
                <div class="message-row" [class.user-row]="msg.role === 'user'" [class.assistant-row]="msg.role === 'assistant'">
                  <div class="avatar" [class.user-avatar]="msg.role === 'user'" [class.assistant-avatar]="msg.role === 'assistant'">
                    @if (msg.role === 'user') {
                      <span>👤</span>
                    } @else {
                      <span>⚡</span>
                    }
                  </div>

                  <div class="bubble" [class.user-bubble]="msg.role === 'user'" [class.assistant-bubble]="msg.role === 'assistant'">
                    <div class="bubble-header">
                      <span class="author-label">{{ msg.role === 'user' ? 'You' : 'AI Assistant' }}</span>
                      @if (msg.created_at) {
                        <span class="timestamp">{{ msg.created_at | date:'shortTime' }}</span>
                      }
                    </div>

                    <div class="bubble-content">
                      @if (msg.role === 'assistant') {
                        <div class="markdown-body" [innerHTML]="msg.content | markdown"></div>
                        @if (msg.isStreaming) {
                          <span class="streaming-cursor" title="Streaming token generation..."></span>
                        }
                      } @else {
                        <p class="user-text">{{ msg.content }}</p>
                      }
                    </div>
                  </div>
                </div>
              }
            </div>
          }

          @if (streamError(); as err) {
            <div class="error-banner">
              <span class="error-icon">⚠️</span>
              <span class="error-text">{{ err }}</span>
            </div>
          }
        </div>

        <!-- Sticky Chat Input Bar -->
        <footer class="input-dock">
          <form class="input-form" (submit)="onSubmit($event)">
            <textarea
              #inputArea
              class="chat-input"
              rows="1"
              placeholder="Type your prompt... (Press Enter to send, Shift+Enter for new line)"
              [(ngModel)]="promptText"
              name="promptText"
              (keydown)="onKeyDown($event)"
              [disabled]="isStreaming()"
            ></textarea>

            <div class="input-actions">
              @if (isStreaming()) {
                <button type="button" class="stop-btn" (click)="onAbort()" title="Stop Generation">
                  <span class="stop-icon">■</span>
                  <span>Stop</span>
                </button>
              } @else {
                <button
                  type="submit"
                  class="send-btn"
                  [disabled]="!promptText.trim()"
                  title="Send message (Enter)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"></line>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                  </svg>
                </button>
              }
            </div>
          </form>
          <div class="input-footnote">
            <span>Enterprise Multi-Tenant AI Agent • High-Throughput Streaming Engine</span>
          </div>
        </footer>
      } @else {
        <!-- No Session Selected Placeholder -->
        <div class="no-session-selected">
          <div class="empty-hero">
            <span class="hero-icon">✨</span>
            <h2>Select or create a conversation</h2>
            <p>Choose an existing thread from the sidebar or click "+ New Chat" to start fresh.</p>
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
      background: #090e17;
      color: #f1f5f9;
      position: relative;
      overflow: hidden;
    }

    .chat-header {
      height: 3.5rem;
      border-bottom: 1px solid #1e293b;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.5rem;
      background: #0b1220;
      flex-shrink: 0;
    }

    .session-info {
      display: flex;
      align-items: baseline;
      gap: 0.75rem;
      overflow: hidden;
    }

    .session-info h2 {
      font-size: 1rem;
      font-weight: 600;
      margin: 0;
      color: #f8fafc;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .session-id-tag {
      font-size: 0.75rem;
      color: #64748b;
      font-family: monospace;
    }

    .header-status {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.75rem;
      color: #94a3b8;
    }

    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
    }

    .messages-viewport {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem 2rem;
      display: flex;
      flex-direction: column;
      scroll-behavior: smooth;
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      margin: auto;
      color: #94a3b8;
      font-size: 0.875rem;
    }

    .spinner {
      width: 2rem;
      height: 2rem;
      border: 3px solid #1e293b;
      border-top-color: #6366f1;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .empty-conversation {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      margin: auto;
      text-align: center;
      max-width: 580px;
      padding: 2rem 1rem;
    }

    .empty-badge {
      display: inline-block;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border: 1px solid rgba(99, 102, 241, 0.3);
      margin-bottom: 1rem;
    }

    .empty-conversation h3 {
      font-size: 1.5rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 0.5rem 0;
      letter-spacing: -0.02em;
    }

    .empty-conversation p {
      font-size: 0.9375rem;
      color: #94a3b8;
      margin: 0 0 1.75rem 0;
      line-height: 1.5;
    }

    .quick-prompts {
      display: flex;
      flex-direction: column;
      gap: 0.625rem;
      width: 100%;
    }

    .quick-chip {
      background: #111827;
      border: 1px solid #1f2937;
      color: #e5e7eb;
      padding: 0.75rem 1rem;
      border-radius: 0.625rem;
      font-size: 0.875rem;
      text-align: left;
      cursor: pointer;
      transition: all 0.15s ease-in-out;
    }

    .quick-chip:hover {
      background: #1f2937;
      border-color: #6366f1;
      color: #ffffff;
      transform: translateY(-1px);
    }

    .message-feed {
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
      width: 100%;
      max-width: 860px;
      margin: 0 auto;
    }

    .message-row {
      display: flex;
      gap: 0.875rem;
      width: 100%;
    }

    .user-row {
      flex-direction: row-reverse;
    }

    .avatar {
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .user-avatar {
      background: #4f46e5;
      color: #ffffff;
    }

    .assistant-avatar {
      background: #1e293b;
      border: 1px solid #334155;
      color: #f59e0b;
    }

    .bubble {
      max-width: 82%;
      border-radius: 0.875rem;
      padding: 0.875rem 1.125rem;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }

    .user-bubble {
      background: #4338ca;
      color: #f8fafc;
      border-bottom-right-radius: 0.25rem;
    }

    .assistant-bubble {
      background: #131d2e;
      border: 1px solid #1e293b;
      color: #f1f5f9;
      border-bottom-left-radius: 0.25rem;
    }

    .bubble-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.375rem;
    }

    .author-label {
      font-size: 0.75rem;
      font-weight: 700;
      opacity: 0.8;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }

    .timestamp {
      font-size: 0.6875rem;
      opacity: 0.6;
    }

    .user-text {
      margin: 0;
      white-space: pre-wrap;
      line-height: 1.5;
      font-size: 0.9375rem;
    }

    .streaming-cursor {
      display: inline-block;
      width: 7px;
      height: 14px;
      background: #818cf8;
      margin-left: 4px;
      vertical-align: middle;
      animation: blink 0.8s infinite;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0; }
    }

    .error-banner {
      max-width: 860px;
      margin: 1rem auto 0 auto;
      width: 100%;
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #fca5a5;
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.875rem;
    }

    .input-dock {
      background: #0b1220;
      border-top: 1px solid #1e293b;
      padding: 1rem 1.5rem;
      flex-shrink: 0;
    }

    .input-form {
      max-width: 860px;
      margin: 0 auto;
      display: flex;
      align-items: flex-end;
      gap: 0.75rem;
      background: #070c14;
      border: 1px solid #1e293b;
      border-radius: 0.75rem;
      padding: 0.5rem 0.75rem;
      transition: border-color 0.15s;
    }

    .input-form:focus-within {
      border-color: #6366f1;
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
    }

    .chat-input {
      flex: 1;
      background: transparent;
      border: none;
      color: #f8fafc;
      font-size: 0.9375rem;
      font-family: inherit;
      resize: none;
      outline: none;
      max-height: 140px;
      min-height: 24px;
      line-height: 1.5;
    }

    .chat-input::placeholder {
      color: #64748b;
    }

    .input-actions {
      display: flex;
      align-items: center;
      flex-shrink: 0;
    }

    .send-btn {
      background: #4f46e5;
      color: #ffffff;
      border: none;
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
    }

    .send-btn:hover:not(:disabled) {
      background: #4338ca;
      transform: scale(1.05);
    }

    .send-btn:disabled {
      background: #1e293b;
      color: #475569;
      cursor: not-allowed;
      transform: none;
    }

    .stop-btn {
      background: #dc2626;
      color: #ffffff;
      border: none;
      padding: 0.375rem 0.75rem;
      border-radius: 0.5rem;
      font-size: 0.75rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.375rem;
      cursor: pointer;
      transition: background 0.15s;
    }

    .stop-btn:hover {
      background: #b91c1c;
    }

    .stop-icon {
      font-size: 0.625rem;
    }

    .input-footnote {
      max-width: 860px;
      margin: 0.5rem auto 0 auto;
      text-align: center;
      font-size: 0.6875rem;
      color: #475569;
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
      max-width: 380px;
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
      line-height: 1.5;
    }
  `]
})
export class ChatWindowComponent {
  private readonly chatService = inject(ChatService);

  @ViewChild('messagesContainer') private messagesContainer?: ElementRef<HTMLDivElement>;

  // Bound from route parameter :sessionId
  readonly sessionId = input<string | null>(null);

  readonly currentSession = this.chatService.activeSession;
  readonly messages = this.chatService.messages;
  readonly isLoadingMessages = this.chatService.isLoadingMessages;
  readonly isStreaming = this.chatService.isStreaming;
  readonly streamError = this.chatService.streamError;

  promptText: string = '';

  constructor() {
    effect(() => {
      const id = this.sessionId();
      this.chatService.selectSession(id);
    });

    effect(() => {
      // Re-trigger scroll whenever messages array updates
      this.messages();
      setTimeout(() => this.scrollToBottom(), 50);
    });
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    this.sendMessage();
  }

  sendMessage(): void {
    const text = this.promptText.trim();
    const sid = this.sessionId();
    if (!text || !sid || this.isStreaming()) return;

    this.promptText = '';
    this.chatService.sendMessageStream(sid, text);
  }

  setQuickPrompt(prompt: string): void {
    this.promptText = prompt;
  }

  onAbort(): void {
    this.chatService.abortStream();
  }

  private scrollToBottom(): void {
    if (this.messagesContainer?.nativeElement) {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }
}
