import { TestBed, ComponentFixture } from '@angular/core/testing';
import { signal } from '@angular/core';
import { ChatWindowComponent } from './chat-window.component';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession } from '../../../core/models/chat.model';

describe('ChatWindowComponent', () => {
  let component: ChatWindowComponent;
  let fixture: ComponentFixture<ChatWindowComponent>;

  const activeSessionSignal = signal<ChatSession | null>(null);
  let mockChatService: {
    activeSession: typeof activeSessionSignal;
    selectSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    activeSessionSignal.set(null);
    mockChatService = {
      activeSession: activeSessionSignal,
      selectSession: vi.fn(),
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
});
