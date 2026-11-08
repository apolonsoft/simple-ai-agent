import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { ChatSidebarComponent } from './chat-sidebar.component';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession } from '../../../core/models/chat.model';

describe('ChatSidebarComponent', () => {
  let component: ChatSidebarComponent;
  let fixture: ComponentFixture<ChatSidebarComponent>;

  const mockSessions: ChatSession[] = [
    {
      id: 'session-101',
      user_id: 'user-1',
      title: 'Architectural Analysis',
      created_at: '2026-11-08T10:00:00Z',
      updated_at: '2026-11-08T10:00:00Z',
    },
    {
      id: 'session-102',
      user_id: 'user-1',
      title: 'Code Refactoring Plan',
      created_at: '2026-11-08T11:00:00Z',
      updated_at: '2026-11-08T11:00:00Z',
    },
  ];

  let sessionsSignal = signal<ChatSession[]>([]);
  let activeSessionIdSignal = signal<string | null>(null);
  let isLoadingSignal = signal<boolean>(false);

  let mockChatService: {
    sessions: typeof sessionsSignal;
    activeSessionId: typeof activeSessionIdSignal;
    isLoadingSessions: typeof isLoadingSignal;
    loadSessions: ReturnType<typeof vi.fn>;
    createSession: ReturnType<typeof vi.fn>;
    deleteSession: ReturnType<typeof vi.fn>;
    selectSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    sessionsSignal = signal<ChatSession[]>([]);
    activeSessionIdSignal = signal<string | null>(null);
    isLoadingSignal = signal<boolean>(false);

    mockChatService = {
      sessions: sessionsSignal,
      activeSessionId: activeSessionIdSignal,
      isLoadingSessions: isLoadingSignal,
      loadSessions: vi.fn().mockReturnValue(of([])),
      createSession: vi.fn().mockReturnValue(of(mockSessions[0])),
      deleteSession: vi.fn().mockReturnValue(of(undefined)),
      selectSession: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ChatSidebarComponent],
      providers: [
        provideRouter([{ path: 'chat/:sessionId', component: ChatSidebarComponent }]),
        { provide: ChatService, useValue: mockChatService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatSidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should call loadSessions on init', () => {
    expect(mockChatService.loadSessions).toHaveBeenCalled();
  });

  it('should display loading state when isLoading is true', () => {
    isLoadingSignal.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.loading-state')).toBeTruthy();
    expect(compiled.textContent).toContain('Loading history...');
  });

  it('should display empty state when there are no sessions and not loading', () => {
    isLoadingSignal.set(false);
    sessionsSignal.set([]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-state')).toBeTruthy();
    expect(compiled.textContent).toContain('No conversations yet.');
  });

  it('should render session items and highlight active session', () => {
    sessionsSignal.set(mockSessions);
    activeSessionIdSignal.set('session-102');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const items = compiled.querySelectorAll('.session-item');
    expect(items.length).toBe(2);
    expect(items[0].textContent).toContain('Architectural Analysis');
    expect(items[1].textContent).toContain('Code Refactoring Plan');

    expect(items[0].classList.contains('active')).toBe(false);
    expect(items[1].classList.contains('active')).toBe(true);
  });

  it('should trigger createSession on + New Chat button click', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const newChatBtn = compiled.querySelector('.new-chat-btn') as HTMLButtonElement;
    newChatBtn.click();

    expect(mockChatService.createSession).toHaveBeenCalled();
  });

  it('should trigger selectSession on item click', async () => {
    sessionsSignal.set(mockSessions);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const firstItem = compiled.querySelector('.session-item') as HTMLElement;
    firstItem.click();

    expect(mockChatService.selectSession).toHaveBeenCalledWith('session-101');
    await fixture.whenStable();
  });

  it('should trigger deleteSession and stop propagation on delete button click', () => {
    sessionsSignal.set(mockSessions);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const deleteBtn = compiled.querySelector('.delete-btn') as HTMLButtonElement;
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    const stopPropagationSpy = vi.spyOn(clickEvent, 'stopPropagation');
    const preventDefaultSpy = vi.spyOn(clickEvent, 'preventDefault');

    deleteBtn.dispatchEvent(clickEvent);

    expect(mockChatService.deleteSession).toHaveBeenCalledWith('session-101');
    expect(stopPropagationSpy).toHaveBeenCalled();
    expect(preventDefaultSpy).toHaveBeenCalled();
  });
});
