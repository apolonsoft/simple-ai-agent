export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface ChatMessage {
  id?: string;
  session_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens?: number;
  created_at?: string;
  isStreaming?: boolean;
}

export interface CreateSessionRequest {
  title?: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface StreamEventData {
  content?: string;
  message_id?: string;
  status?: string;
  error?: string;
}
