/**
 * Shared API Contract Specification Types
 * Derived from OpenAPI 3.1.0 schema (shared/openapi.json)
 */

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  database: 'healthy' | 'unhealthy' | 'unavailable';
  redis: 'healthy' | 'unhealthy' | 'unavailable';
}

export interface UserResponse {
  id: string;
  email: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
  role?: 'admin' | 'user';
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ChatSessionCreateRequest {
  title?: string;
}

export interface ChatSessionResponse {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageCreateRequest {
  content: string;
}

export interface ChatMessageResponse {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens?: number | null;
  created_at: string;
}

export interface ChatSessionDetailResponse extends ChatSessionResponse {
  messages: ChatMessageResponse[];
}

export type SseStreamEventType = 'chunk' | 'done' | 'error';

export interface SseChunkEvent {
  content: string;
}

export interface SseDoneEvent {
  message_id?: string | null;
  status: 'completed';
}

export interface SseErrorEvent {
  error: string;
}
