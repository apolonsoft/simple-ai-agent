import {
  ChangeDetectionStrategy,
  Component,
  inject,
  input,
  signal,
  effect,
  ViewChild,
  ElementRef,
  AfterViewInit,
  OnDestroy,
  HostListener,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatMessage, ToolCall } from '../../../core/models/chat.model';
import { ChatService } from '../../../core/services/chat.service';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { PdfViewerModalComponent } from '../pdf-viewer-modal/pdf-viewer-modal.component';
import { ToolParamsPipe } from '../pipes/tool-params.pipe';
import { PdfFilenamePipe } from '../pipes/pdf-filename.pipe';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [DatePipe, FormsModule, MarkdownPipe, PdfViewerModalComponent, ToolParamsPipe, PdfFilenamePipe],
  templateUrl: './chat-window.component.html',
  styleUrl: './chat-window.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
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
  readonly isExecutingTool = this.chatService.isExecutingTool;
  readonly streamError = this.chatService.streamError;

  readonly activePdfBlob = signal<Blob | null>(null);
  readonly previewFilename = signal<string | null>(null);
  readonly isToolsMenuOpen = signal<boolean>(false);

  readonly promptText = signal<string>('');
  private stickToBottom = true;
  private scrollRafId: number | null = null;

  constructor() {
    effect(() => {
      const id = this.sessionId();
      this.stickToBottom = true;
      this.chatService.selectSession(id);
    });

    effect(() => {
      // Re-trigger scroll whenever messages array updates
      this.messages();
      this.scheduleScrollToBottom();
    });
  }

  ngAfterViewInit(): void {
    this.scheduleScrollToBottom(true);
  }

  ngOnDestroy(): void {
    if (this.scrollRafId !== null && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.scrollRafId);
      this.scrollRafId = null;
    }
    this.closePdfViewer();
  }

  onViewportScroll(): void {
    const el = this.messagesContainer?.nativeElement;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    this.stickToBottom = distanceFromBottom <= 80;
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
    const text = this.promptText().trim();
    const sid = this.sessionId();
    if (!text || !sid || this.isStreaming()) return;

    this.promptText.set('');
    this.stickToBottom = true;
    this.chatService.sendMessageStream(sid, text);
    this.scheduleScrollToBottom(true);
  }

  setQuickPrompt(prompt: string): void {
    this.promptText.set(prompt);
  }

  onAbort(): void {
    this.chatService.abortStream();
  }

  onApproveTool(msg: ChatMessage, tc: ToolCall): void {
    const sid = this.sessionId();
    if (!sid || this.isExecutingTool()) return;
    this.chatService.approveToolCall(sid, msg.id, tc.id, true);
  }

  onRejectTool(msg: ChatMessage, tc: ToolCall): void {
    const sid = this.sessionId();
    if (!sid || this.isExecutingTool()) return;
    this.chatService.approveToolCall(sid, msg.id, tc.id, false);
  }

  getToolParams(args: Record<string, any> | undefined): { key: string; value: string }[] {
    if (!args) return [];
    return Object.entries(args).map(([key, val]) => ({
      key,
      value: typeof val === 'object' ? JSON.stringify(val) : String(val),
    }));
  }

  isPdfTool(toolName: string): boolean {
    return ['create_pdf', 'merge_pdfs', 'inspect_pdf'].includes(toolName);
  }

  extractPdfFilename(result: any): string | null {
    if (!result) return null;
    let data: any = result;
    if (typeof result === 'string') {
      try {
        data = JSON.parse(result);
      } catch {
        const match = result.match(/[\w\-.]+\.pdf/i);
        return match ? match[0] : null;
      }
    }
    if (typeof data === 'object' && data !== null) {
      if (typeof data.filename === 'string' && data.filename.toLowerCase().endsWith('.pdf')) {
        return data.filename;
      }
      if (typeof data.file_path === 'string' && data.file_path.toLowerCase().endsWith('.pdf')) {
        const parts = data.file_path.split(/[/\\]/);
        return parts[parts.length - 1];
      }
      if (typeof data.merged_file_path === 'string' && data.merged_file_path.toLowerCase().endsWith('.pdf')) {
        const parts = data.merged_file_path.split(/[/\\]/);
        return parts[parts.length - 1];
      }
    }
    return null;
  }

  openPdfViewer(filename: string): void {
    this.chatService.getPdfBlob(filename).subscribe({
      next: (blob) => {
        this.activePdfBlob.set(blob);
        this.previewFilename.set(filename);
      },
      error: (err) => {
        console.error('Failed to load PDF for preview', err);
      },
    });
  }

  closePdfViewer(): void {
    this.activePdfBlob.set(null);
    this.previewFilename.set(null);
  }

  downloadPdf(filename: string): void {
    this.chatService.getPdfBlob(filename).subscribe({
      next: (blob) => {
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
      },
      error: (err) => {
        console.error('Failed to download PDF', err);
      },
    });
  }

  toggleToolsMenu(): void {
    this.isToolsMenuOpen.update((open) => !open);
  }

  closeToolsMenu(): void {
    this.isToolsMenuOpen.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.isToolsMenuOpen()) return;
    const target = event.target as HTMLElement;
    if (!target.closest('.tools-trigger-container')) {
      this.closeToolsMenu();
    }
  }

  onMessagesClick(event: MouseEvent): void {
    const target = event.target as HTMLElement;
    const copyBtn = target.closest('.copy-code-btn') as HTMLElement | null;
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

  private scheduleScrollToBottom(force = false): void {
    if (!force && !this.stickToBottom) return;

    if (typeof requestAnimationFrame === 'function') {
      if (this.scrollRafId !== null) return;
      this.scrollRafId = requestAnimationFrame(() => {
        this.scrollRafId = null;
        if (force || this.stickToBottom) {
          this.scrollToBottom();
        }
      });
    } else {
      this.scrollToBottom();
    }
  }

  private scrollToBottom(): void {
    if (this.messagesContainer?.nativeElement) {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }
}
