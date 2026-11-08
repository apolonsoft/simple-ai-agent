import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ChatService } from '../../../core/services/chat.service';
import { ChatSession } from '../../../core/models/chat.model';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './chat-sidebar.component.html',
  styleUrl: './chat-sidebar.component.scss',
})
export class ChatSidebarComponent implements OnInit {
  private readonly chatService = inject(ChatService);

  readonly sessions = this.chatService.sessions;
  readonly activeSessionId = this.chatService.activeSessionId;
  readonly isLoading = this.chatService.isLoadingSessions;

  ngOnInit(): void {
    this.chatService.loadSessions().subscribe();
  }

  onNewChat(): void {
    this.chatService.createSession().subscribe();
  }

  onSelect(id: string): void {
    this.chatService.selectSession(id);
  }

  onDelete(id: string, event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault();
    this.chatService.deleteSession(id).subscribe();
  }
}
