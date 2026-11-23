import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { ChatLayoutComponent } from './chat-layout.component';
import { AuthService } from '../../../core/services/auth.service';
import { ChatService } from '../../../core/services/chat.service';
import { User } from '../../../core/models/user.model';
import { ChatSession } from '../../../core/models/chat.model';

describe('ChatLayoutComponent', () => {
  let component: ChatLayoutComponent;
  let fixture: ComponentFixture<ChatLayoutComponent>;
  let currentUserSignal = signal<User | null>(null);
  let mockAuthService: { currentUser: typeof currentUserSignal; logout: ReturnType<typeof vi.fn> };
  let mockChatService: {
    sessions: ReturnType<typeof signal<ChatSession[]>>;
    activeSessionId: ReturnType<typeof signal<string | null>>;
    isLoadingSessions: ReturnType<typeof signal<boolean>>;
    isCreatingSession: ReturnType<typeof signal<boolean>>;
    sidebarError: ReturnType<typeof signal<string | null>>;
    loadSessions: ReturnType<typeof vi.fn>;
    createSession: ReturnType<typeof vi.fn>;
    deleteSession: ReturnType<typeof vi.fn>;
    selectSession: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    currentUserSignal = signal<User | null>({
      id: 'uuid-1',
      email: 'lead_dev@example.com',
      role: 'user',
      is_active: true,
    });

    mockAuthService = {
      currentUser: currentUserSignal,
      logout: vi.fn(),
    };

    mockChatService = {
      sessions: signal<ChatSession[]>([]),
      activeSessionId: signal<string | null>(null),
      isLoadingSessions: signal<boolean>(false),
      isCreatingSession: signal<boolean>(false),
      sidebarError: signal<string | null>(null),
      loadSessions: vi.fn().mockReturnValue(of([])),
      createSession: vi.fn().mockReturnValue(of({})),
      deleteSession: vi.fn().mockReturnValue(of(undefined)),
      selectSession: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [ChatLayoutComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
        { provide: ChatService, useValue: mockChatService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should render header with brand title and user email', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.brand-title')?.textContent).toContain('Enterprise AI Agent');
    expect(compiled.querySelector('.user-email')?.textContent).toContain('lead_dev@example.com');
    expect(compiled.querySelector('.user-chip')?.getAttribute('href')).toBe('/profile');
  });

  it('should render user avatar img if avatar_url is provided', () => {
    currentUserSignal.set({
      id: 'uuid-1',
      email: 'lead_dev@example.com',
      role: 'user',
      is_active: true,
      full_name: 'Lead Developer',
      avatar_url: 'http://localhost:8333/avatars/lead.png',
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const avatarImg = compiled.querySelector('.user-chip img') as HTMLImageElement;
    expect(avatarImg).toBeTruthy();
    expect(avatarImg.getAttribute('src')).toBe('http://localhost:8333/avatars/lead.png');
    expect(compiled.querySelector('.user-email')?.textContent).toContain('Lead Developer');
  });

  it('should call authService.logout on sign out button click', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const logoutBtn = compiled.querySelector('.logout-btn') as HTMLButtonElement;
    logoutBtn.click();

    expect(mockAuthService.logout).toHaveBeenCalled();
  });

  it('should render admin nav pill when user role is admin or super_admin', () => {
    currentUserSignal.set({
      id: 'uuid-admin',
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const adminPill = compiled.querySelector('.admin-nav-pill');
    expect(adminPill).toBeTruthy();
    expect(adminPill?.getAttribute('href')).toBe('/admin/users');
    expect(adminPill?.textContent).toContain('Admin');

    // Also check super_admin
    currentUserSignal.set({
      id: 'uuid-super',
      email: 'super@example.com',
      role: 'super_admin',
      is_active: true,
    });
    fixture.detectChanges();

    expect(compiled.querySelector('.admin-nav-pill')).toBeTruthy();
  });

  it('should NOT render admin nav pill when user role is regular user', () => {
    currentUserSignal.set({
      id: 'uuid-user',
      email: 'user@example.com',
      role: 'user',
      is_active: true,
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.admin-nav-pill')).toBeNull();
  });
});
