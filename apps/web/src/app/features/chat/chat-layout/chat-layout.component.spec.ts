import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { ChatLayoutComponent } from './chat-layout.component';
import { AuthService } from '../../../core/services/auth.service';
import { User } from '../../../core/models/user.model';

describe('ChatLayoutComponent', () => {
  let component: ChatLayoutComponent;
  let fixture: ComponentFixture<ChatLayoutComponent>;
  let currentUserSignal = signal<User | null>(null);
  let mockAuthService: { currentUser: typeof currentUserSignal; logout: ReturnType<typeof vi.fn> };

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

    await TestBed.configureTestingModule({
      imports: [ChatLayoutComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: mockAuthService },
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
  });

  it('should call authService.logout on sign out button click', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const logoutBtn = compiled.querySelector('.logout-btn') as HTMLButtonElement;
    logoutBtn.click();

    expect(mockAuthService.logout).toHaveBeenCalled();
  });
});
