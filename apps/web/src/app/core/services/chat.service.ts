import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { ChatSession, CreateSessionRequest } from '../models/chat.model';

@Injectable({
  providedIn: 'root',
})
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  // Reactive state using Angular Signals
  readonly sessions = signal<ChatSession[]>([]);
  readonly activeSessionId = signal<string | null>(null);
  readonly isLoadingSessions = signal<boolean>(false);

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
  }
}
