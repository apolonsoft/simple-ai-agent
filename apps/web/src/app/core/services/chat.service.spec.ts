import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { ChatService } from './chat.service';
import { ChatSession, ChatMessage } from '../models/chat.model';

describe('ChatService', () => {
  let service: ChatService;
  let httpTestingController: HttpTestingController;
  let mockRouter: { navigate: ReturnType<typeof vi.fn> };

  const mockSessions: ChatSession[] = [
    {
      id: 'session-1',
      user_id: 'user-1',
      title: 'First Chat',
      created_at: '2026-11-08T10:00:00Z',
      updated_at: '2026-11-08T10:00:00Z',
    },
    {
      id: 'session-2',
      user_id: 'user-1',
      title: 'Second Chat',
      created_at: '2026-11-08T11:00:00Z',
      updated_at: '2026-11-08T11:00:00Z',
    },
  ];

  beforeEach(() => {
    mockRouter = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        ChatService,
        { provide: Router, useValue: mockRouter },
      ],
    });

    service = TestBed.inject(ChatService);
    httpTestingController = TestBed.inject(HttpTestingController);
    localStorage.clear();
  });

  afterEach(() => {
    httpTestingController.verify();
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('should load sessions and update reactive state', () => {
    expect(service.sessions()).toEqual([]);
    expect(service.isLoadingSessions()).toBe(false);

    service.loadSessions().subscribe((sessions) => {
      expect(sessions.length).toBe(2);
    });

    expect(service.isLoadingSessions()).toBe(true);

    const req = httpTestingController.expectOne('/api/v1/chats');
    expect(req.request.method).toBe('GET');
    req.flush(mockSessions);

    expect(service.sessions()).toEqual(mockSessions);
    expect(service.isLoadingSessions()).toBe(false);
  });

  it('should create a new session, prepend it to state, and navigate', () => {
    service.sessions.set([...mockSessions]);

    const newSession: ChatSession = {
      id: 'session-3',
      user_id: 'user-1',
      title: 'New Chat',
      created_at: '2026-11-08T12:00:00Z',
      updated_at: '2026-11-08T12:00:00Z',
    };

    service.createSession('New Chat').subscribe((session) => {
      expect(session.id).toBe('session-3');
    });

    const req = httpTestingController.expectOne('/api/v1/chats');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ title: 'New Chat' });
    req.flush(newSession);

    expect(service.sessions().length).toBe(3);
    expect(service.sessions()[0]).toEqual(newSession);
    expect(service.activeSessionId()).toBe('session-3');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/chat', 'session-3']);
  });

  it('should delete a non-active session without changing activeSessionId', () => {
    service.sessions.set([...mockSessions]);
    service.activeSessionId.set('session-1');

    service.deleteSession('session-2').subscribe();

    const req = httpTestingController.expectOne('/api/v1/chats/session-2');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);

    expect(service.sessions().length).toBe(1);
    expect(service.sessions()[0].id).toBe('session-1');
    expect(service.activeSessionId()).toBe('session-1');
  });

  it('should delete active session and navigate to first remaining session', () => {
    service.sessions.set([...mockSessions]);
    service.activeSessionId.set('session-1');

    service.deleteSession('session-1').subscribe();

    const req = httpTestingController.expectOne('/api/v1/chats/session-1');
    req.flush(null);

    expect(service.sessions().length).toBe(1);
    expect(service.sessions()[0].id).toBe('session-2');
    expect(service.activeSessionId()).toBe('session-2');
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/chat', 'session-2']);
  });

  it('should delete active session when it is the only session and navigate to root chat', () => {
    service.sessions.set([mockSessions[0]]);
    service.activeSessionId.set('session-1');

    service.deleteSession('session-1').subscribe();

    const req = httpTestingController.expectOne('/api/v1/chats/session-1');
    req.flush(null);

    expect(service.sessions().length).toBe(0);
    expect(service.activeSessionId()).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/chat']);
  });

  it('should compute activeSession correctly when activeSessionId changes', () => {
    service.sessions.set([...mockSessions]);
    expect(service.activeSession()).toBeNull();

    service.selectSession('session-2');
    const req = httpTestingController.expectOne('/api/v1/chats/session-2/messages');
    req.flush([]);

    expect(service.activeSession()).toEqual(mockSessions[1]);

    service.selectSession(null);
    expect(service.activeSession()).toBeNull();
    expect(service.messages()).toEqual([]);
  });

  it('should load session messages via loadMessages', () => {
    const mockMessages: ChatMessage[] = [
      { id: 'm-1', session_id: 'session-1', role: 'user', content: 'Hello' },
      { id: 'm-2', session_id: 'session-1', role: 'assistant', content: 'Hi there!' },
    ];

    service.loadMessages('session-1').subscribe((msgs) => {
      expect(msgs).toEqual(mockMessages);
    });

    expect(service.isLoadingMessages()).toBe(true);

    const req = httpTestingController.expectOne('/api/v1/chats/session-1/messages');
    expect(req.request.method).toBe('GET');
    req.flush(mockMessages);

    expect(service.messages()).toEqual(mockMessages);
    expect(service.isLoadingMessages()).toBe(false);
  });

  it('should consume real-time SSE stream chunks and update assistant message', async () => {
    localStorage.setItem('token', 'jwt-test-token');

    const stream = new ReadableStream({
      start(controller) {
        const encoder = new TextEncoder();
        controller.enqueue(encoder.encode('event: chunk\ndata: {"content": "Deep"}\n\n'));
        controller.enqueue(encoder.encode('event: chunk\ndata: {"content": " learning"}\n\n'));
        controller.enqueue(encoder.encode('event: done\ndata: {"status": "completed"}\n\n'));
        controller.close();
      },
    });

    const mockResponse = new Response(stream, {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    });

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(mockResponse);

    await service.sendMessageStream('session-1', 'Explain AI');

    expect(fetchSpy).toHaveBeenCalledWith(
      '/api/v1/chats/session-1/stream',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          Authorization: 'Bearer jwt-test-token',
        }),
        body: JSON.stringify({ content: 'Explain AI' }),
      })
    );

    const msgs = service.messages();
    expect(msgs.length).toBe(2);
    expect(msgs[0]).toMatchObject({ role: 'user', content: 'Explain AI' });
    expect(msgs[1]).toMatchObject({ role: 'assistant', content: 'Deep learning', isStreaming: false });
    expect(service.isStreaming()).toBe(false);
  });

  it('should handle SSE server error gracefully', async () => {
    const mockResponse = new Response(JSON.stringify({ detail: 'Provider API key is invalid' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });

    vi.spyOn(globalThis, 'fetch').mockResolvedValue(mockResponse);

    await service.sendMessageStream('session-1', 'Test prompt');

    expect(service.streamError()).toContain('Provider API key is invalid');
    const msgs = service.messages();
    expect(msgs.length).toBe(2);
    expect(msgs[1].content).toContain('Provider API key is invalid');
    expect(service.isStreaming()).toBe(false);
  });
});
