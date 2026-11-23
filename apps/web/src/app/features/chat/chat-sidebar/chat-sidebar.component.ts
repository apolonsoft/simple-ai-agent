import { ChangeDetectionStrategy, Component, inject, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession } from '../../../core/models/chat.model';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './chat-sidebar.component.html',
  styleUrl: './chat-sidebar.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatSidebarComponent implements OnInit {
  private readonly chatService = inject(ChatService);

  readonly sessions = this.chatService.sessions;
  readonly activeSessionId = this.chatService.activeSessionId;
  readonly isLoading = this.chatService.isLoadingSessions;
  readonly isCreating = this.chatService.isCreatingSession;
  readonly sidebarError = this.chatService.sidebarError;

  ngOnInit(): void {
    this.chatService.loadSessions().subscribe({ error: () => {} });
  }

  onNewChat(): void {
    if (this.isCreating?.()) return;
    this.chatService.createSession().subscribe({ error: () => {} });
  }

  onDelete(id: string, event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    this.chatService.deleteSession(id).subscribe({ error: () => {} });
  }
}
