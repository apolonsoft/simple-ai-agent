import {
  Component,
  inject,
  input,
  effect,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnDestroy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../../core/services/chat.service';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './chat-window.component.html',
  styleUrl: './chat-window.component.scss',
})
export class ChatWindowComponent implements AfterViewInit, OnDestroy {
  private readonly chatService = inject(ChatService);

  @ViewChild('messagesContainer') private messagesContainer?: ElementRef<HTMLDivElement>;
  @ViewChild('scrollAnchor') private scrollAnchor?: ElementRef<HTMLDivElement>;

  // Bound from route parameter :sessionId
  readonly sessionId = input<string | null>(null);

  readonly currentSession = this.chatService.activeSession;
  readonly messages = this.chatService.messages;
  readonly isLoadingMessages = this.chatService.isLoadingMessages;
  readonly isStreaming = this.chatService.isStreaming;
  readonly streamError = this.chatService.streamError;

  promptText: string = '';
  private observer?: MutationObserver;

  constructor() {
    effect(() => {
      const id = this.sessionId();
      this.chatService.selectSession(id);
    });

    effect(() => {
      // Re-trigger scroll whenever messages array updates
      this.messages();
      this.scheduleScrollToBottom();
    });
  }

  ngAfterViewInit(): void {
    this.scheduleScrollToBottom();
    this.setupScrollObserver();
  }

  ngOnDestroy(): void {
    this.observer?.disconnect();
  }

  private setupScrollObserver(): void {
    if (typeof MutationObserver !== 'undefined' && this.messagesContainer?.nativeElement) {
      this.observer = new MutationObserver(() => {
        this.scrollToBottom();
      });
      this.observer.observe(this.messagesContainer.nativeElement, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    }
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
    this.scheduleScrollToBottom();
  }

  setQuickPrompt(prompt: string): void {
    this.promptText = prompt;
  }

  onAbort(): void {
    this.chatService.abortStream();
  }

  onMessagesClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const copyBtn = target.closest('.copy-code-btn') as HTMLButtonElement | null;
    if (!copyBtn) return;

    const container = copyBtn.closest('.code-container');
    const codeEl = container?.querySelector('code');
    if (!codeEl) return;

    const textToCopy = codeEl.innerText || codeEl.textContent || '';
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        const textSpan = copyBtn.querySelector('.copy-text');
        if (textSpan) textSpan.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        setTimeout(() => {
          if (textSpan) textSpan.textContent = 'Copy';
          copyBtn.classList.remove('copied');
        }, 2000);
      }).catch(() => {
        // clipboard access restricted
      });
    }
  }

  private scheduleScrollToBottom(): void {
    this.scrollToBottom();
    if (typeof requestAnimationFrame !== 'undefined') {
      requestAnimationFrame(() => this.scrollToBottom());
    }
    setTimeout(() => this.scrollToBottom(), 20);
    setTimeout(() => this.scrollToBottom(), 80);
  }

  private scrollToBottom(): void {
    if (this.messagesContainer?.nativeElement) {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
    if (typeof this.scrollAnchor?.nativeElement?.scrollIntoView === 'function') {
      this.scrollAnchor.nativeElement.scrollIntoView({ block: 'end' });
    }
  }
}
