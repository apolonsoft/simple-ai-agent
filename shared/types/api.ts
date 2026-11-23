/**
 * Shared API Contract Specification Types
 * Derived from OpenAPI 3.1.0 schema (shared/openapi.json)
 */

export type UserRole = 'user' | 'admin' | 'super_admin';

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  database: 'healthy' | 'unhealthy' | 'unavailable';
  redis: 'healthy' | 'unhealthy' | 'unavailable';
}

export interface UserResponse {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  full_name?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface UserRegisterRequest {
  email: string;
  password: string;
}

export interface UserProfileUpdate {
  full_name?: string | null;
  bio?: string | null;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface VerifyResetTokenResponse {
  valid: boolean;
  email?: string;
}

export interface MessageResponse {
  message: string;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name?: string | null;
  role: UserRole;
  is_active: boolean;
  is_banned: boolean;
  banned_at?: string | null;
  ban_reason?: string | null;
  created_at?: string | null;
}

export interface AdminUserDetail extends AdminUser {
  avatar_url?: string | null;
  bio?: string | null;
  chat_sessions_count: number;
  updated_at?: string | null;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface AdminActionResponse {
  success: boolean;
  message: string;
  user: AdminUser;
}

export interface BanUserRequest {
  reason?: string | null;
}

export interface UpdateUserRoleRequest {
  role: UserRole;
}

export interface AdminUserFilter {
  page?: number;
  limit?: number;
  search?: string;
  role?: string;
  status?: string;
}

export interface PaginationParams {
  limit?: number;
  before?: string;
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

export interface ToolCall {
  id: string;
  tool: string;
  arguments: Record<string, any>;
  status?: 'pending' | 'approved' | 'rejected' | 'executed' | 'executing' | 'failed';
  result?: any;
}

export interface ToolApprovalRequest {
  tool_call_id: string;
  approved: boolean;
  message_id?: string;
  tool_name?: string;
  arguments?: Record<string, any>;
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
  tool_calls?: ToolCall[] | null;
}

export interface ChatSessionDetailResponse extends ChatSessionResponse {
  messages: ChatMessageResponse[];
}

export type SseStreamEventType = 'chunk' | 'done' | 'error' | 'tool_call' | 'tool_result';

export interface SseChunkEvent {
  content: string;
}

export interface SseDoneEvent {
  message_id?: string | null;
  status: 'completed' | 'awaiting_approval';
  tool_calls?: ToolCall[];
}

export interface SseErrorEvent {
  error: string;
}

export interface SseToolCallEvent {
  id: string;
  tool: string;
  arguments: Record<string, any>;
  status?: string;
}

export interface SseToolResultEvent {
  tool_call_id: string;
  status: 'executed' | 'failed' | 'rejected';
  result?: any;
}
