import { apiClient } from './apiClient';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user_email: string;
  user_role: string;
  expires_at: string;
}

export interface TokenVerificationResponse {
  valid: boolean;
  user_email?: string;
  user_role?: string;
  message?: string;
}

export interface UserResponse {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

/**
 * Authentication Service
 * Handles login, token verification, and user info
 */
class AuthService {
  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', {
      email,
      password,
    });
    return response.data;
  }

  /**
   * Verify JWT token
   */
  async verifyToken(token: string): Promise<TokenVerificationResponse> {
    const response = await apiClient.post<TokenVerificationResponse>(
      '/auth/verify',
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  }

  /**
   * Get current user information
   */
  async getCurrentUser(token: string): Promise<UserResponse> {
    const response = await apiClient.get<UserResponse>('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  /**
   * Store token in localStorage
   */
  storeToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token);
    }
  }

  /**
   * Get token from localStorage
   */
  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token');
    }
    return null;
  }

  /**
   * Remove token from localStorage
   */
  removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
    }
  }

  /**
   * Store user info in localStorage
   */
  storeUserInfo(email: string, role: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('user_email', email);
      localStorage.setItem('user_role', role);
    }
  }

  /**
   * Get user info from localStorage
   */
  getUserInfo(): { email: string | null; role: string | null } {
    if (typeof window !== 'undefined') {
      return {
        email: localStorage.getItem('user_email'),
        role: localStorage.getItem('user_role'),
      };
    }
    return { email: null, role: null };
  }

  /**
   * Remove user info from localStorage
   */
  removeUserInfo(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user_email');
      localStorage.removeItem('user_role');
    }
  }

  /**
   * Logout - clear all auth data
   */
  logout(): void {
    this.removeToken();
    this.removeUserInfo();
  }
}

export const authService = new AuthService();
