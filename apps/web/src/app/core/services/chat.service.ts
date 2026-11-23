import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, Subscription, tap } from 'rxjs';
import { ChatSession, ChatMessage, CreateSessionRequest, ToolCall } from '../models/chat.model';
import { parseSseBlock, splitSseBuffer } from '../utils/sse-parser';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  // Active SSE stream abort controller & session/load guards
  private abortController: AbortController | null = null;
  private loadMessagesSub?: Subscription;
  private streamingSessionId: string | null = null;
  private pendingTokenBuffer = '';
  private flushRafId: number | null = null;

  constructor() {
    this.authService.registerLogoutCleanup(() => this.resetState());
  }

  resetState(): void {
    this.abortStream();
    this.loadMessagesSub?.unsubscribe();
    this.loadMessagesSub = undefined;
    this.sessions.set([]);
    this.messages.set([]);
    this.activeSessionId.set(null);
    this.isLoadingSessions.set(false);
    this.isCreatingSession.set(false);
    this.sidebarError.set(null);
    this.isLoadingMessages.set(false);
    this.isExecutingTool.set(false);
    this.streamError.set(null);
  }

  // Reactive state using Angular Signals
  readonly sessions = signal<ChatSession[]>([]);
  readonly activeSessionId = signal<string | null>(null);
  readonly isLoadingSessions = signal<boolean>(false);
  readonly isCreatingSession = signal<boolean>(false);
  readonly sidebarError = signal<string | null>(null);

  // Messages and streaming state
  readonly messages = signal<ChatMessage[]>([]);
  readonly isLoadingMessages = signal<boolean>(false);
  readonly isStreaming = signal<boolean>(false);
  readonly isExecutingTool = signal<boolean>(false);
  readonly streamError = signal<string | null>(null);

  readonly activeSession = computed(() => {
    const currentId = this.activeSessionId();
    if (!currentId) return null;
    return this.sessions().find((s) => s.id === currentId) || null;
  });

  loadSessions(): Observable<ChatSession[]> {
    this.isLoadingSessions.set(true);
    this.sidebarError.set(null);
    return this.http.get<ChatSession[]>('/api/v1/chats').pipe(
      tap({
        next: (items) => {
          this.sessions.set(items);
          this.isLoadingSessions.set(false);
        },
        error: () => {
          this.isLoadingSessions.set(false);
          this.sidebarError.set('Failed to load conversations.');
        },
      })
    );
  }

  createSession(title: string = 'New Chat'): Observable<ChatSession> {
    this.isCreatingSession.set(true);
    this.sidebarError.set(null);
    const payload: CreateSessionRequest = { title };
    return this.http.post<ChatSession>('/api/v1/chats', payload).pipe(
      tap({
        next: (newSession) => {
          this.sessions.update((prev) => [newSession, ...prev]);
          this.activeSessionId.set(newSession.id);
          this.isCreatingSession.set(false);
          this.router.navigate(['/chat', newSession.id]);
        },
        error: () => {
          this.isCreatingSession.set(false);
          this.sidebarError.set('Failed to create conversation.');
        },
      })
    );
  }

  deleteSession(sessionId: string): Observable<void> {
    this.sidebarError.set(null);
    return this.http.delete<void>(`/api/v1/chats/${sessionId}`).pipe(
      tap({
        next: () => {
          this.sessions.update((prev) => prev.filter((s) => s.id !== sessionId));
          if (this.activeSessionId() === sessionId) {
            const remaining = this.sessions();
            if (remaining.length > 0) {
              this.activeSessionId.set(remaining[0].id);
              this.router.navigate(['/chat', remaining[0].id]);
            } else {
              this.activeSessionId.set(null);
              this.router.navigate(['/chat']);
            }
          }
        },
        error: () => {
          this.sidebarError.set('Failed to delete conversation.');
        },
      })
    );
  }

  selectSession(sessionId: string | null): void {
    if (
      sessionId !== null &&
      sessionId === this.activeSessionId() &&
      (this.isLoadingMessages() || this.messages().some((m) => m.session_id === sessionId))
    ) {
      return;
    }

    this.abortStream();
    this.loadMessagesSub?.unsubscribe();
    this.loadMessagesSub = undefined;
    this.activeSessionId.set(sessionId);

    if (sessionId) {
      this.loadMessagesSub = this.loadMessages(sessionId).subscribe();
    } else {
      this.isLoadingMessages.set(false);
      this.messages.set([]);
      this.streamError.set(null);
    }
  }

  loadMessages(sessionId: string): Observable<ChatMessage[]> {
    this.isLoadingMessages.set(true);
    this.streamError.set(null);
    return this.http.get<ChatMessage[]>(`/api/v1/chats/${sessionId}/messages`).pipe(
      tap({
        next: (msgs) => {
          if (this.activeSessionId() === null || this.activeSessionId() === sessionId) {
            this.messages.set(msgs);
          }
          this.isLoadingMessages.set(false);
        },
        error: () => {
          this.isLoadingMessages.set(false);
          this.streamError.set('Failed to load conversation messages.');
        },
      })
    );
  }

  getPdfBlob(filename: string): Observable<Blob> {
    return this.http.get(`/api/v1/chats/files/pdf/${filename}`, {
      responseType: 'blob',
    });
  }

  async sendMessageStream(sessionId: string, prompt: string): Promise<void> {
    const trimmed = prompt.trim();
    if (!trimmed || this.isStreaming()) return;

    this.abortStream();

    const userMsg: ChatMessage = {
      clientId: this.createClientId(),
      session_id: sessionId,
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    const assistantMsg: ChatMessage = {
      clientId: this.createClientId(),
      session_id: sessionId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toISOString(),
    };

    this.messages.update((prev) => [...prev, userMsg, assistantMsg]);
    this.isStreaming.set(true);
    this.streamError.set(null);
    this.streamingSessionId = sessionId;

    this.abortController = new AbortController();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = this.authService.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`/api/v1/chats/${sessionId}/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ content: trimmed }),
        signal: this.abortController.signal,
      });

      if (response.status === 401) {
        this.authService.logout();
        return;
      }

      if (!response.ok) {
        let errorDetail = `Server returned HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore json parse error
        }
        this.handleStreamError(errorDetail, sessionId);
        return;
      }

      if (!response.body) {
        this.handleStreamError('Streaming response body is undefined.', sessionId);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!this.isStreamActiveFor(sessionId)) break;

        buffer += decoder.decode(value, { stream: true });
        const { blocks, remainder } = splitSseBuffer(buffer);
        buffer = remainder;

        for (const block of blocks) {
          if (block.trim()) {
            this.processSseBlock(block, sessionId);
          }
        }
      }

      if (buffer.trim() && this.isStreamActiveFor(sessionId)) {
        const { blocks, remainder } = splitSseBuffer(buffer);
        for (const block of [...blocks, remainder]) {
          if (block.trim()) {
            this.processSseBlock(block, sessionId);
          }
        }
        buffer = '';
      }
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        // Stream aborted on request
      } else {
        this.handleStreamError(error?.message || 'Failed to stream response.', sessionId);
      }
    } finally {
      this.flushPendingTokens(sessionId);
      this.finalizeAssistantMessage(sessionId);
      this.isStreaming.set(false);
      this.abortController = null;
      if (this.streamingSessionId === sessionId) {
        this.streamingSessionId = null;
      }
    }
  }

  async approveToolCall(
    sessionId: string,
    messageId: string | undefined,
    toolCallId: string,
    approved: boolean
  ): Promise<void> {
    if (this.isExecutingTool()) return;

    this.abortStream();
    this.isExecutingTool.set(true);
    this.streamError.set(null);
    this.streamingSessionId = sessionId;
    this.abortController = new AbortController();

    // Optimistically update status
    this.updateToolCallStatus(toolCallId, approved ? 'approved' : 'rejected');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = this.authService.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`/api/v1/chats/${sessionId}/tool-calls/approval`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          tool_call_id: toolCallId,
          approved,
          message_id: messageId,
        }),
        signal: this.abortController.signal,
      });

      if (response.status === 401) {
        this.updateToolCallStatus(toolCallId, 'pending');
        this.authService.logout();
        return;
      }

      if (!response.ok) {
        this.updateToolCallStatus(toolCallId, 'pending');
        let errorDetail = `Server returned HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore
        }
        this.handleStreamError(errorDetail, sessionId);
        return;
      }

      if (!response.body) {
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!this.isStreamActiveFor(sessionId)) break;

        buffer += decoder.decode(value, { stream: true });
        const { blocks, remainder } = splitSseBuffer(buffer);
        buffer = remainder;

        for (const block of blocks) {
          if (block.trim()) {
            this.processSseBlock(block, sessionId);
          }
        }
      }

      if (buffer.trim() && this.isStreamActiveFor(sessionId)) {
        const { blocks, remainder } = splitSseBuffer(buffer);
        for (const block of [...blocks, remainder]) {
          if (block.trim()) {
            this.processSseBlock(block, sessionId);
          }
        }
        buffer = '';
      }
    } catch (error: any) {
      this.updateToolCallStatus(toolCallId, 'pending');
      if (error?.name !== 'AbortError') {
        this.handleStreamError(error?.message || 'Failed to process tool approval.', sessionId);
      }
    } finally {
      this.flushPendingTokens(sessionId);
      this.isExecutingTool.set(false);
      this.finalizeAssistantMessage(sessionId);
      this.abortController = null;
      if (this.streamingSessionId === sessionId) {
        this.streamingSessionId = null;
      }
    }
  }

  abortStream(): void {
    const previousSessionId = this.streamingSessionId;
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.flushPendingTokens(previousSessionId);
    this.cancelPendingTokenFlush();
    this.finalizeAssistantMessage(previousSessionId);
    this.streamingSessionId = null;
    this.isStreaming.set(false);
    this.isExecutingTool.set(false);
  }

  private isStreamActiveFor(sessionId: string): boolean {
    if (this.streamingSessionId !== sessionId) return false;
    const active = this.activeSessionId();
    return active === null || active === sessionId;
  }

  private createClientId(): string {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID();
    }
    return `client-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }

  private processSseBlock(block: string, sessionId: string): void {
    if (!this.isStreamActiveFor(sessionId)) return;

    const parsedBlock = parseSseBlock(block);
    if (!parsedBlock) return;
    const { eventType, dataStr } = parsedBlock;

    try {
      const parsed = JSON.parse(dataStr);
      if (eventType === 'error' || parsed.error) {
        this.flushPendingTokens(sessionId);
        this.handleStreamError(parsed.error || 'Generation error', sessionId);
      } else if (eventType === 'tool_call') {
        this.flushPendingTokens(sessionId);
        const toolName = parsed.tool || parsed.name;
        if (!toolName) return;
        const tc: ToolCall = {
          id: parsed.id,
          tool: toolName,
          arguments: parsed.arguments || {},
          status: (parsed.status as any) || 'pending',
          result: parsed.result,
        };
        this.addToolCallToAssistant(tc);
      } else if (eventType === 'tool_result') {
        this.flushPendingTokens(sessionId);
        this.updateToolCallResult(parsed.tool_call_id, parsed.status, parsed.result);
      } else if (eventType === 'done' || parsed.status === 'completed' || parsed.status === 'awaiting_approval') {
        this.flushPendingTokens(sessionId);
        if (parsed.message_id) {
          this.updateAssistantMessageId(parsed.message_id);
        }
        if (parsed.tool_calls && Array.isArray(parsed.tool_calls)) {
          for (const tc of parsed.tool_calls) {
            this.addToolCallToAssistant(tc);
          }
        }
        this.finalizeAssistantMessage(sessionId);
      } else if (eventType === 'chunk' || parsed.content !== undefined) {
        if (parsed.content) {
          this.appendAssistantToken(parsed.content, sessionId);
        }
      }
    } catch {
      if (dataStr) {
        this.appendAssistantToken(dataStr, sessionId);
      }
    }
  }

  private addToolCallToAssistant(tc: ToolCall): void {
    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant') {
        const existingCalls = last.tool_calls || [];
        const alreadyExists = existingCalls.some((c) => c.id === tc.id);
        const updatedCalls = alreadyExists
          ? existingCalls.map((c) => (c.id === tc.id ? { ...c, ...tc } : c))
          : [...existingCalls, tc];

        const updated: ChatMessage = {
          ...last,
          tool_calls: updatedCalls,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }

  private updateToolCallStatus(
    toolCallId: string,
    status: 'pending' | 'approved' | 'rejected' | 'executed'
  ): void {
    this.messages.update((list) =>
      list.map((msg) => {
        if (!msg.tool_calls) return msg;
        const updated = msg.tool_calls.map((c) =>
          c.id === toolCallId ? { ...c, status } : c
        );
        return { ...msg, tool_calls: updated };
      })
    );
  }

  private updateToolCallResult(
    toolCallId: string,
    status: 'executed' | 'rejected',
    result?: any
  ): void {
    this.messages.update((list) =>
      list.map((msg) => {
        if (!msg.tool_calls) return msg;
        const updated = msg.tool_calls.map((c) =>
          c.id === toolCallId ? { ...c, status, result } : c
        );
        return { ...msg, tool_calls: updated };
      })
    );
  }

  private updateAssistantMessageId(messageId: string): void {
    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant') {
        const updated: ChatMessage = {
          ...last,
          id: messageId,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }

  private appendAssistantToken(token: string, sessionId?: string | null): void {
    if (sessionId && !this.isStreamActiveFor(sessionId)) return;

    this.pendingTokenBuffer += token;
    if (typeof requestAnimationFrame !== 'function') {
      this.flushPendingTokens(sessionId);
      return;
    }

    if (this.flushRafId === null) {
      const targetSessionId = sessionId ?? this.streamingSessionId;
      this.flushRafId = requestAnimationFrame(() => {
        this.flushRafId = null;
        this.flushPendingTokens(targetSessionId);
      });
    }
  }

  private flushPendingTokens(sessionId?: string | null): void {
    if (this.flushRafId !== null && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.flushRafId);
    }
    this.flushRafId = null;

    if (!this.pendingTokenBuffer) return;
    const buffered = this.pendingTokenBuffer;
    this.pendingTokenBuffer = '';

    if (sessionId && !this.isStreamActiveFor(sessionId)) return;

    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant') {
        const updated: ChatMessage = {
          ...last,
          content: last.content + buffered,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }

  private cancelPendingTokenFlush(): void {
    if (this.flushRafId !== null && typeof cancelAnimationFrame === 'function') {
      cancelAnimationFrame(this.flushRafId);
    }
    this.flushRafId = null;
    this.pendingTokenBuffer = '';
  }

  private finalizeAssistantMessage(sessionId?: string | null): void {
    if (sessionId && !this.isStreamActiveFor(sessionId)) return;

    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant' && last.isStreaming) {
        const updated: ChatMessage = {
          ...last,
          isStreaming: false,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }

  private handleStreamError(errorMessage: string, sessionId?: string | null): void {
    if (sessionId && !this.isStreamActiveFor(sessionId)) return;

    this.streamError.set(errorMessage);
    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant' && !last.content) {
        const updated: ChatMessage = {
          ...last,
          content: `⚠️ Error: ${errorMessage}`,
          isStreaming: false,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }
}
