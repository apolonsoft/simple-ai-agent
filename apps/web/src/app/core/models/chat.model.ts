export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: ChatMessage[];
}

export interface ToolCall {
  id: string;
  tool: string;
  arguments: Record<string, any>;
  status?: 'pending' | 'approved' | 'rejected' | 'executed';
  result?: any;
}

export interface ChatMessage {
  id?: string;
  session_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens?: number;
  created_at?: string;
  isStreaming?: boolean;
  tool_calls?: ToolCall[];
}

export interface CreateSessionRequest {
  title?: string;
}

export interface SendMessageRequest {
  content: string;
}

export interface ToolApprovalRequest {
  tool_call_id: string;
  approved: boolean;
  message_id?: string;
  tool_name?: string;
  arguments?: Record<string, any>;
}

export interface StreamEventData {
  content?: string;
  message_id?: string;
  status?: string;
  error?: string;
  tool_call?: ToolCall;
  tool_calls?: ToolCall[];
  result?: any;
}
