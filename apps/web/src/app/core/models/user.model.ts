export interface User {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  full_name?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface UserProfileUpdate {
  full_name?: string | null;
  bio?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  role?: string;
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
