import { TestBed, ComponentFixture } from '@angular/core/testing';
import { signal } from '@angular/core';
import { of } from 'rxjs';
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
  const isExecutingToolSignal = signal<boolean>(false);
  const streamErrorSignal = signal<string | null>(null);

  let mockChatService: {
    activeSession: typeof activeSessionSignal;
    messages: typeof messagesSignal;
    isLoadingMessages: typeof isLoadingMessagesSignal;
    isStreaming: typeof isStreamingSignal;
    isExecutingTool: typeof isExecutingToolSignal;
    streamError: typeof streamErrorSignal;
    selectSession: ReturnType<typeof vi.fn>;
    sendMessageStream: ReturnType<typeof vi.fn>;
    approveToolCall: ReturnType<typeof vi.fn>;
    abortStream: ReturnType<typeof vi.fn>;
    getPdfBlob: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    activeSessionSignal.set(null);
    messagesSignal.set([]);
    isLoadingMessagesSignal.set(false);
    isStreamingSignal.set(false);
    isExecutingToolSignal.set(false);
    streamErrorSignal.set(null);

    mockChatService = {
      activeSession: activeSessionSignal,
      messages: messagesSignal,
      isLoadingMessages: isLoadingMessagesSignal,
      isStreaming: isStreamingSignal,
      isExecutingTool: isExecutingToolSignal,
      streamError: streamErrorSignal,
      selectSession: vi.fn(),
      sendMessageStream: vi.fn().mockResolvedValue(undefined),
      approveToolCall: vi.fn().mockResolvedValue(undefined),
      abortStream: vi.fn(),
      getPdfBlob: vi.fn().mockReturnValue(of(new Blob(['%PDF-1.4 test data'], { type: 'application/pdf' }))),
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

  it('should render tool call approval card and handle Approve & Run button click', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        role: 'user',
        content: 'Multiply 6 by 7',
      },
      {
        id: 'msg-tool-1',
        role: 'assistant',
        content: '',
        tool_calls: [
          {
            id: 'call-calc-1',
            tool: 'calculator',
            arguments: { operator: 'multiply', first_number: 6, second_number: 7 },
            status: 'pending',
          },
        ],
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const toolCard = compiled.querySelector('.tool-call-card');
    expect(toolCard).toBeTruthy();
    expect(toolCard?.textContent).toContain('calculator');
    expect(toolCard?.textContent).toContain('Approval Required');
    expect(toolCard?.textContent).toContain('operator');
    expect(toolCard?.textContent).toContain('multiply');

    const approveBtn = toolCard?.querySelector('.btn-approve') as HTMLButtonElement;
    expect(approveBtn).toBeTruthy();

    approveBtn.click();
    expect(mockChatService.approveToolCall).toHaveBeenCalledWith(
      'session-42',
      'msg-tool-1',
      'call-calc-1',
      true
    );
  });

  it('should handle tool call Reject button click', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        id: 'msg-tool-2',
        role: 'assistant',
        content: '',
        tool_calls: [
          {
            id: 'call-calc-2',
            tool: 'calculator',
            arguments: { operator: 'divide', first_number: 10, second_number: 0 },
            status: 'pending',
          },
        ],
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const rejectBtn = compiled.querySelector('.btn-reject') as HTMLButtonElement;
    expect(rejectBtn).toBeTruthy();

    rejectBtn.click();
    expect(mockChatService.approveToolCall).toHaveBeenCalledWith(
      'session-42',
      'msg-tool-2',
      'call-calc-2',
      false
    );
  });

  it('should render executed tool call result', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        id: 'msg-tool-3',
        role: 'assistant',
        content: 'Here is the answer.',
        tool_calls: [
          {
            id: 'call-calc-3',
            tool: 'calculator',
            arguments: { operator: 'add', first_number: 15, second_number: 25 },
            status: 'executed',
            result: 40,
          },
        ],
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const toolCard = compiled.querySelector('.tool-call-card');
    expect(toolCard?.textContent).toContain('Executed');
    expect(toolCard?.textContent).toContain('40');
    expect(toolCard?.querySelector('.btn-approve')).toBeFalsy();
  });

  it('should render PDF icon 📄 and View/Download buttons for executed PDF tool call', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        id: 'msg-tool-pdf',
        role: 'assistant',
        content: 'I generated the requested PDF report.',
        tool_calls: [
          {
            id: 'call-pdf-1',
            tool: 'create_pdf',
            arguments: { title: 'Architecture Report', content: 'Details here...' },
            status: 'executed',
            result: JSON.stringify({
              status: 'success',
              filename: 'architecture_report.pdf',
              file_path: '/path/to/architecture_report.pdf',
              page_count: 2,
            }),
          },
        ],
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const toolCard = compiled.querySelector('.tool-call-card');
    expect(toolCard).toBeTruthy();
    expect(toolCard?.querySelector('.tool-icon')?.textContent).toBe('📄');

    const viewBtn = toolCard?.querySelector('.btn-view-pdf') as HTMLButtonElement;
    const downloadBtn = toolCard?.querySelector('.btn-download-pdf') as HTMLButtonElement;
    expect(viewBtn).toBeTruthy();
    expect(downloadBtn).toBeTruthy();

    // Click View PDF
    viewBtn.click();
    expect(mockChatService.getPdfBlob).toHaveBeenCalledWith('architecture_report.pdf');

    fixture.detectChanges();
    const modal = compiled.querySelector('app-pdf-viewer-modal');
    expect(modal).toBeTruthy();
    expect(modal?.textContent).toContain('architecture_report.pdf');

    // Close Modal
    const closeBtn = modal?.querySelector('.btn-close') as HTMLButtonElement;
    closeBtn.click();
    fixture.detectChanges();
    expect(compiled.querySelector('app-pdf-viewer-modal')).toBeFalsy();
  });

  it('should trigger download when Download button is clicked', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        id: 'msg-tool-pdf-2',
        role: 'assistant',
        content: 'Report ready.',
        tool_calls: [
          {
            id: 'call-pdf-2',
            tool: 'merge_pdfs',
            arguments: { file_paths: ['a.pdf', 'b.pdf'] },
            status: 'executed',
            result: JSON.stringify({
              status: 'success',
              filename: 'merged_doc.pdf',
            }),
          },
        ],
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const downloadBtn = compiled.querySelector('.btn-download-pdf') as HTMLButtonElement;
    expect(downloadBtn).toBeTruthy();

    downloadBtn.click();
    expect(mockChatService.getPdfBlob).toHaveBeenCalledWith('merged_doc.pdf');
  });

  it('should toggle active tools popover displaying PDF MCP tools', () => {
    fixture.componentRef.setInput('sessionId', 'session-42');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.tools-popover')).toBeFalsy();

    const toggleBtn = compiled.querySelector('.btn-tools-toggle') as HTMLButtonElement;
    expect(toggleBtn).toBeTruthy();
    toggleBtn.click();
    fixture.detectChanges();

    const popover = compiled.querySelector('.tools-popover');
    expect(popover).toBeTruthy();
    expect(popover?.textContent).toContain('PDF MCP Server');
    expect(popover?.textContent).toContain('create_pdf');
    expect(popover?.textContent).toContain('inspect_pdf');
    expect(popover?.textContent).toContain('merge_pdfs');
    expect(popover?.textContent).toContain('Tavily Web Search');
    expect(popover?.textContent).toContain('Calculator');

    // Click selector button to toggle close
    const selectorBtn = compiled.querySelector('.btn-tools-selector') as HTMLButtonElement;
    selectorBtn.click();
    fixture.detectChanges();
    expect(compiled.querySelector('.tools-popover')).toBeFalsy();
  });

  it('should sanitize dangerous HTML in assistant markdown and preserve copy-code-btn click behavior', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      configurable: true,
    });

    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([
      {
        role: 'assistant',
        content: '<img src=x onerror=alert(1)>\n\n```python\nprint("hi")\n```',
      },
    ]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const markdownBody = compiled.querySelector('.markdown-body');
    expect(markdownBody).toBeTruthy();
    expect(markdownBody?.querySelector('img')).toBeFalsy();

    const copyBtn = markdownBody?.querySelector('.copy-code-btn') as HTMLElement;
    expect(copyBtn).toBeTruthy();
    copyBtn.click();
    await Promise.resolve();

    expect(writeTextMock).toHaveBeenCalledWith('print("hi")');
  });

  it('should preserve upward scroll during streaming and auto-scroll when near bottom or sending a message', async () => {
    await new Promise((resolve) => setTimeout(resolve, 30));
    vi.useFakeTimers();
    const cancelSpy = vi.spyOn(globalThis, 'cancelAnimationFrame');

    fixture.componentRef.setInput('sessionId', 'session-42');
    messagesSignal.set([{ id: 'm1', role: 'assistant', content: 'Initial' }]);
    fixture.detectChanges();
    vi.advanceTimersByTime(20);

    const viewport = (fixture.nativeElement as HTMLElement).querySelector('.messages-viewport') as HTMLDivElement;
    Object.defineProperty(viewport, 'scrollHeight', { value: 1000, configurable: true });
    Object.defineProperty(viewport, 'clientHeight', { value: 400, configurable: true });
    let currentScrollTop = 100;
    Object.defineProperty(viewport, 'scrollTop', {
      get: () => currentScrollTop,
      set: (v: number) => {
        currentScrollTop = v;
      },
      configurable: true,
    });

    // User scrolls up (1000 - 100 - 400 = 500 > 80)
    viewport.dispatchEvent(new Event('scroll'));

    // Incoming streamed token must NOT yank scrollTop back to bottom
    messagesSignal.set([{ id: 'm1', role: 'assistant', content: 'Initial + streamed' }]);
    fixture.detectChanges();
    vi.advanceTimersByTime(20);
    expect(currentScrollTop).toBe(100);

    // Sending a new message forces stick-to-bottom and schedules scroll
    component.promptText = 'Next question';
    component.sendMessage();
    vi.advanceTimersByTime(20);
    expect(currentScrollTop).toBe(1000);

    // Destroying cancels pending rAF if scheduled
    messagesSignal.set([{ id: 'm1', role: 'assistant', content: 'More' }]);
    fixture.detectChanges();
    fixture.destroy();
    expect(cancelSpy).toHaveBeenCalled();

    cancelSpy.mockRestore();
    vi.useRealTimers();
  });
});
