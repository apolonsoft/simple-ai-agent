import { TestBed, ComponentFixture } from '@angular/core/testing';
import { signal } from '@angular/core';
import { ChatWindowComponent } from './chat-window.component';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession, ChatMessage } from '../../../core/models/chat.model';

describe('ChatWindowComponent', () => {
  let component: ChatWindowComponent;
  let fixture: ComponentFixture<ChatWindowComponent>;

  const activeSessionSignal = signal<ChatSession | null>(null);
  const messagesSignal = signal<ChatMessage[]>([]);
  const isLoadingMessagesSignal = signal<boolean>(false);
  const isStreamingSignal = signal<boolean>(false);
  const streamErrorSignal = signal<string | null>(null);

  let mockChatService: {
    activeSession: typeof activeSessionSignal;
    messages: typeof messagesSignal;
    isLoadingMessages: typeof isLoadingMessagesSignal;
    isStreaming: typeof isStreamingSignal;
    streamError: typeof streamErrorSignal;
    selectSession: ReturnType<typeof vi.fn>;
    sendMessageStream: ReturnType<typeof vi.fn>;
    abortStream: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    activeSessionSignal.set(null);
    messagesSignal.set([]);
    isLoadingMessagesSignal.set(false);
    isStreamingSignal.set(false);
    streamErrorSignal.set(null);

    mockChatService = {
      activeSession: activeSessionSignal,
      messages: messagesSignal,
      isLoadingMessages: isLoadingMessagesSignal,
      isStreaming: isStreamingSignal,
      streamError: streamErrorSignal,
      selectSession: vi.fn(),
      sendMessageStream: vi.fn().mockResolvedValue(undefined),
      abortStream: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ChatWindowComponent],
      providers: [
        { provide: ChatService, useValue: mockChatService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatWindowComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render empty hero when no sessionId is active', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.no-session-selected')).toBeTruthy();
    expect(compiled.textContent).toContain('Select or create a conversation');
  });

  it('should render session header and call selectSession when sessionId input is set', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    activeSessionSignal.set({
      id: 'session-42',
      user_id: 'user-1',
      title: 'Deep Learning Discussion',
      created_at: '2026-11-08T10:00:00Z',
      updated_at: '2026-11-08T10:00:00Z',
    });
    fixture.detectChanges();

    expect(mockChatService.selectSession).toHaveBeenCalledWith('session-42');
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.chat-header h2')?.textContent).toContain('Deep Learning Discussion');
    expect(compiled.querySelector('.session-id-tag')?.textContent).toContain('session-42');
  });

  it('should render user and assistant message bubbles with markdown', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        role: 'user',
        content: 'Explain Docker',
      },
      {
        role: 'assistant',
        content: '**Docker** provides `containerization`.',
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const messageRows = compiled.querySelectorAll('.message-row');
    expect(messageRows.length).toBe(2);

    expect(messageRows[0].classList.contains('user-row')).toBe(true);
    expect(messageRows[0].textContent).toContain('Explain Docker');

    expect(messageRows[1].classList.contains('assistant-row')).toBe(true);
    expect(messageRows[1].querySelector('strong')?.textContent).toContain('Docker');
    expect(messageRows[1].querySelector('code')?.textContent).toContain('containerization');
  });

  it('should send prompt and clear input field on form submit', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    fixture.detectChanges();

    component.promptText = 'What is FastAPI?';
    component.sendMessage();

    expect(mockChatService.sendMessageStream).toHaveBeenCalledWith('session-42', 'What is FastAPI?');
    expect(component.promptText).toBe('');
  });

  it('should display stop button when streaming and trigger abortStream', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    isStreamingSignal.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const stopBtn = compiled.querySelector('.stop-btn') as HTMLButtonElement;
    expect(stopBtn).toBeTruthy();

    stopBtn.click();
    expect(mockChatService.abortStream).toHaveBeenCalled();
  });
});
