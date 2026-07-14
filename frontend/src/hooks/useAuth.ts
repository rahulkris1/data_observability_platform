import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { authService, AuthResponse } from '@/services/authService';

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  userEmail: string | null;
  userRole: string | null;
  error: string | null;
}

/**
 * Custom hook for authentication
 * Manages JWT token, login, logout, and authentication state
 */
export function useAuth() {
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    userEmail: null,
    userRole: null,
    error: null,
  });

  /**
   * Check if user is authenticated on mount
   */
  useEffect(() => {
    checkAuth();
  }, []);

  /**
   * Check authentication status
   */
  const checkAuth = useCallback(async () => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

    const token = authService.getToken();
    
    if (!token) {
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        userEmail: null,
        userRole: null,
        error: null,
      });
      return;
    }

    try {
      // Verify token with backend
      const verification = await authService.verifyToken(token);

      if (verification.valid) {
        setAuthState({
          isAuthenticated: true,
          isLoading: false,
          userEmail: verification.user_email || null,
          userRole: verification.user_role || null,
          error: null,
        });
      } else {
        // Token is invalid, clear it
        authService.logout();
        setAuthState({
          isAuthenticated: false,
          isLoading: false,
          userEmail: null,
          userRole: null,
          error: 'Session expired',
        });
      }
    } catch (error) {
      // Error verifying token, clear auth state
      authService.logout();
      setAuthState({
        isAuthenticated: false,
        isLoading: false,
        userEmail: null,
        userRole: null,
        error: 'Authentication failed',
      });
    }
  }, []);

  /**
   * Login with email and password
   */
  const login = useCallback(async (email: string, password: string) => {
    setAuthState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response: AuthResponse = await authService.login(email, password);

      // Store token and user info
      authService.storeToken(response.access_token);
      authService.storeUserInfo(response.user_email, response.user_role);

      setAuthState({
        isAuthenticated: true,
        isLoading: false,
        userEmail: response.user_email,
        userRole: response.user_role,
        error: null,
      });

      return { success: true };
    } catch (error: any) {
      // Handle both FastAPI's "detail" field and custom "error" field
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.error || 
        error.message || 
        'Login failed';
      
      console.error('Login error:', error);
      console.error('Error response:', error.response?.data);
      
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));

      return { success: false, error: errorMessage };
    }
  }, []);

  /**
   * Logout user
   */
  const logout = useCallback(() => {
    authService.logout();
    
    setAuthState({
      isAuthenticated: false,
      isLoading: false,
      userEmail: null,
      userRole: null,
      error: null,
    });

    // Redirect to login page
    router.push('/login');
  }, [router]);

  /**
   * Check if user has specific role
   */
  const hasRole = useCallback((role: string) => {
    return authState.userRole === role;
  }, [authState.userRole]);

  /**
   * Check if user is admin
   */
  const isAdmin = useCallback(() => {
    return authState.userRole === 'admin';
  }, [authState.userRole]);

  return {
    ...authState,
    login,
    logout,
    checkAuth,
    hasRole,
    isAdmin,
  };
}
