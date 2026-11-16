export type UserRole = 'user' | 'admin' | 'super_admin';

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
