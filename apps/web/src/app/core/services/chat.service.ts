import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { ChatSession, ChatMessage, CreateSessionRequest, ToolCall } from '../models/chat.model';

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
  readonly isExecutingTool = signal<boolean>(false);
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
        const blocks = buffer.split(/(?:\r\n\r\n|\r\r|\n\n)/);
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (block.trim()) {
            this.processSseBlock(block);
          }
        }
      }

      if (buffer.trim()) {
        const remainingBlocks = buffer.split(/(?:\r\n\r\n|\r\r|\n\n)/);
        for (const block of remainingBlocks) {
          if (block.trim()) {
            this.processSseBlock(block);
          }
        }
        buffer = '';
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

  async approveToolCall(
    sessionId: string,
    messageId: string | undefined,
    toolCallId: string,
    approved: boolean
  ): Promise<void> {
    if (this.isExecutingTool()) return;

    this.isExecutingTool.set(true);
    this.streamError.set(null);

    // Optimistically update status
    this.updateToolCallStatus(toolCallId, approved ? 'approved' : 'rejected');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const token = localStorage.getItem('token');
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
      });

      if (!response.ok) {
        let errorDetail = `Server returned HTTP ${response.status}`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch {
          // ignore
        }
        this.handleStreamError(errorDetail);
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

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split(/(?:\r\n\r\n|\r\r|\n\n)/);
        buffer = blocks.pop() || '';

        for (const block of blocks) {
          if (block.trim()) {
            this.processSseBlock(block);
          }
        }
      }

      if (buffer.trim()) {
        const remainingBlocks = buffer.split(/(?:\r\n\r\n|\r\r|\n\n)/);
        for (const block of remainingBlocks) {
          if (block.trim()) {
            this.processSseBlock(block);
          }
        }
        buffer = '';
      }
    } catch (error: any) {
      this.handleStreamError(error?.message || 'Failed to process tool approval.');
    } finally {
      this.isExecutingTool.set(false);
      this.finalizeAssistantMessage();
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

    const lines = block.split(/\r?\n/);
    for (const rawLine of lines) {
      const line = rawLine.trimEnd();
      if (line.startsWith('event:')) {
        eventType = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        const rawData = line.slice(5);
        dataStr = rawData.startsWith(' ') ? rawData.slice(1) : rawData;
      }
    }

    if (!dataStr) return;

    try {
      const parsed = JSON.parse(dataStr);
      if (eventType === 'error' || parsed.error) {
        this.handleStreamError(parsed.error || 'Generation error');
      } else if (eventType === 'tool_call') {
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
        this.updateToolCallResult(parsed.tool_call_id, parsed.status, parsed.result);
      } else if (eventType === 'done' || parsed.status === 'completed' || parsed.status === 'awaiting_approval') {
        if (parsed.message_id) {
          this.updateAssistantMessageId(parsed.message_id);
        }
        if (parsed.tool_calls && Array.isArray(parsed.tool_calls)) {
          for (const tc of parsed.tool_calls) {
            this.addToolCallToAssistant(tc);
          }
        }
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
