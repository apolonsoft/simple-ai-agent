import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { ChatSession, ChatMessage, CreateSessionRequest } from '../models/chat.model';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  // Active SSE stream abort controller
  private abortController: AbortController | null = null;

  // Reactive state using Angular Signals
  readonly sessions = signal<ChatSession[]>([]);
  readonly activeSessionId = signal<string | null>(null);
  readonly isLoadingSessions = signal<boolean>(false);

  // Messages and streaming state
  readonly messages = signal<ChatMessage[]>([]);
  readonly isLoadingMessages = signal<boolean>(false);
  readonly isStreaming = signal<boolean>(false);
  readonly streamError = signal<string | null>(null);

  readonly activeSession = computed(() => {
    const currentId = this.activeSessionId();
    if (!currentId) return null;
    return this.sessions().find((s) => s.id === currentId) || null;
  });

  loadSessions(): Observable<ChatSession[]> {
    this.isLoadingSessions.set(true);
    return this.http.get<ChatSession[]>('/api/v1/chats').pipe(
      tap({
        next: (items) => {
          this.sessions.set(items);
          this.isLoadingSessions.set(false);
        },
        error: () => {
          this.isLoadingSessions.set(false);
        },
      })
    );
  }

  createSession(title: string = 'New Chat'): Observable<ChatSession> {
    const payload: CreateSessionRequest = { title };
    return this.http.post<ChatSession>('/api/v1/chats', payload).pipe(
      tap((newSession) => {
        this.sessions.update((prev) => [newSession, ...prev]);
        this.activeSessionId.set(newSession.id);
        this.router.navigate(['/chat', newSession.id]);
      })
    );
  }

  deleteSession(sessionId: string): Observable<void> {
    return this.http.delete<void>(`/api/v1/chats/${sessionId}`).pipe(
      tap(() => {
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
      })
    );
  }

  selectSession(sessionId: string | null): void {
    this.activeSessionId.set(sessionId);
    if (sessionId) {
      this.loadMessages(sessionId).subscribe();
    } else {
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
          this.messages.set(msgs);
          this.isLoadingMessages.set(false);
        },
        error: () => {
          this.isLoadingMessages.set(false);
        },
      })
    );
  }

  async sendMessageStream(sessionId: string, prompt: string): Promise<void> {
    const trimmed = prompt.trim();
    if (!trimmed || this.isStreaming()) return;

    this.abortStream();

    const userMsg: ChatMessage = {
      session_id: sessionId,
      role: 'user',
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    const assistantMsg: ChatMessage = {
      session_id: sessionId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      created_at: new Date().toISOString(),
    };

    this.messages.update((prev) => [...prev, userMsg, assistantMsg]);
    this.isStreaming.set(true);
    this.streamError.set(null);

    this.abortController = new AbortController();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('token');
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

      if (!response.ok) {
        let errorDetail = `Server returned HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore json parse error
        }
        this.handleStreamError(errorDetail);
        return;
      }

      if (!response.body) {
        this.handleStreamError('Streaming response body is undefined.');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (block.trim()) {
            this.processSseBlock(block);
          }
        }
      }

      if (buffer.trim()) {
        this.processSseBlock(buffer);
      }
    } catch (error: any) {
      if (error?.name === 'AbortError') {
        // Stream aborted on request
      } else {
        this.handleStreamError(error?.message || 'Failed to stream response.');
      }
    } finally {
      this.finalizeAssistantMessage();
      this.isStreaming.set(false);
      this.abortController = null;
    }
  }

  abortStream(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.finalizeAssistantMessage();
    this.isStreaming.set(false);
  }

  private processSseBlock(block: string): void {
    let eventType = 'chunk';
    let dataStr = '';

    const lines = block.split('\n');
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine.startsWith('event:')) {
        eventType = trimmedLine.replace('event:', '').trim();
      } else if (trimmedLine.startsWith('data:')) {
        dataStr = trimmedLine.replace('data:', '').trim();
      }
    }

    if (!dataStr) return;

    try {
      const parsed = JSON.parse(dataStr);
      if (eventType === 'error' || parsed.error) {
        this.handleStreamError(parsed.error || 'Generation error');
      } else if (eventType === 'done' || parsed.status === 'completed') {
        this.finalizeAssistantMessage();
      } else if (eventType === 'chunk' || parsed.content !== undefined) {
        if (parsed.content) {
          this.appendAssistantToken(parsed.content);
        }
      }
    } catch {
      if (dataStr) {
        this.appendAssistantToken(dataStr);
      }
    }
  }

  private appendAssistantToken(token: string): void {
    this.messages.update((list) => {
      if (list.length === 0) return list;
      const lastIdx = list.length - 1;
      const last = list[lastIdx];
      if (last.role === 'assistant') {
        const updated: ChatMessage = {
          ...last,
          content: last.content + token,
        };
        return [...list.slice(0, lastIdx), updated];
      }
      return list;
    });
  }

  private finalizeAssistantMessage(): void {
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

  private handleStreamError(errorMessage: string): void {
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
