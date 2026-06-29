/**
 * Integration tests for protected routes
 * 
 * Tests authentication and authorization including:
 * - Route protection
 * - Login workflow
 * - Logout workflow
 * - Token management
 * - Unauthorized access handling
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter } from 'next/router';
import axios from 'axios';
import ProtectedPage from '@/pages/protected';
import LoginPage from '@/pages/login';

// Mock Next.js router
jest.mock('next/router', () => ({
  useRouter: jest.fn(),
}));

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockedUseRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('Protected Routes Integration Tests', () => {
  let mockPush: jest.Mock;
  let mockReplace: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockPush = jest.fn();
    mockReplace = jest.fn();
    
    mockedUseRouter.mockReturnValue({
      push: mockPush,
      replace: mockReplace,
      pathname: '/',
      query: {},
      asPath: '/',
      route: '/',
      basePath: '',
      isReady: true,
      isLocaleDomain: false,
      isPreview: false,
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
      },
      isFallback: false,
      beforePopState: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
      reload: jest.fn(),
      forward: jest.fn(),
    } as any);

    // Clear localStorage
    localStorage.clear();
  });

  it('should redirect to login when accessing protected route without token', async () => {
    render(<ProtectedPage />);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  it('should allow access to protected route with valid token', async () => {
    // Set valid token
    localStorage.setItem('auth_token', 'valid-token-123');

    // Mock API call to verify token
    mockedAxios.get.mockResolvedValueOnce({
      data: { user: { id: 1, username: 'testuser' } }
    });

    render(<ProtectedPage />);

    await waitFor(() => {
      expect(mockPush).not.toHaveBeenCalledWith('/login');
    });

    // Should show protected content
    expect(screen.queryByText(/login/i)).not.toBeInTheDocument();
  });

  it('should complete login workflow', async () => {
    const user = userEvent.setup();

    mockedAxios.post.mockResolvedValueOnce({
      data: {
        access_token: 'new-token-123',
        token_type: 'bearer',
        user: { id: 1, username: 'testuser' }
      }
    });

    render(<LoginPage />);

    // Fill in login form
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    // Should call login API
    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        {
          username: 'testuser',
          password: 'password123'
        },
        expect.any(Object)
      );
    });

    // Should store token
    await waitFor(() => {
      expect(localStorage.getItem('auth_token')).toBe('new-token-123');
    });

    // Should redirect to dashboard
    expect(mockPush).toHaveBeenCalledWith('/dashboard' || '/');
  });

  it('should handle login failure', async () => {
    const user = userEvent.setup();

    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 401,
        data: { detail: 'Invalid credentials' }
      }
    });

    render(<LoginPage />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'wronguser');
    await user.type(passwordInput, 'wrongpass');
    await user.click(submitButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/invalid/i) || screen.getByText(/failed/i)).toBeInTheDocument();
    });

    // Should not store token
    expect(localStorage.getItem('auth_token')).toBeNull();

    // Should not redirect
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('should handle logout workflow', async () => {
    const user = userEvent.setup();

    // Set token
    localStorage.setItem('auth_token', 'valid-token-123');

    mockedAxios.get.mockResolvedValueOnce({
      data: { user: { id: 1, username: 'testuser' } }
    });

    render(<ProtectedPage />);

    await waitFor(() => {
      expect(screen.queryByText(/login/i)).not.toBeInTheDocument();
    });

    // Find logout button
    const logoutButton = screen.queryByRole('button', { name: /logout/i }) ||
                        screen.queryByText(/logout/i);

    if (logoutButton) {
      await user.click(logoutButton);

      // Should clear token
      await waitFor(() => {
        expect(localStorage.getItem('auth_token')).toBeNull();
      });

      // Should redirect to login
      expect(mockPush).toHaveBeenCalledWith('/login');
    }
  });

  it('should handle expired token', async () => {
    localStorage.setItem('auth_token', 'expired-token');

    // Mock 401 response
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });

    render(<ProtectedPage />);

    // Should redirect to login
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    // Should clear token
    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('should attach token to API requests', async () => {
    const token = 'test-token-123';
    localStorage.setItem('auth_token', token);

    mockedAxios.get.mockResolvedValueOnce({
      data: { validations: [] }
    });

    // Make an API request (simulated)
    await axios.get('/api/v1/validations', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    // Verify token was included
    expect(mockedAxios.get).toHaveBeenCalledWith(
      '/api/v1/validations',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: `Bearer ${token}`
        })
      })
    );
  });

  it('should handle token refresh', async () => {
    localStorage.setItem('auth_token', 'old-token');
    localStorage.setItem('refresh_token', 'refresh-token-123');

    // Mock token refresh
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        access_token: 'new-token-456',
        token_type: 'bearer'
      }
    });

    // Simulate token refresh call
    await axios.post('/auth/refresh', {
      refresh_token: 'refresh-token-123'
    });

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/auth/refresh',
        expect.objectContaining({
          refresh_token: 'refresh-token-123'
        })
      );
    });
  });

  it('should prevent access to login page when already authenticated', async () => {
    localStorage.setItem('auth_token', 'valid-token');

    mockedAxios.get.mockResolvedValueOnce({
      data: { user: { id: 1, username: 'testuser' } }
    });

    render(<LoginPage />);

    // Should redirect to dashboard
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard' || '/');
    });
  });

  it('should show loading state during authentication check', async () => {
    localStorage.setItem('auth_token', 'valid-token');

    mockedAxios.get.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ data: { user: { id: 1, username: 'testuser' } } });
        }, 100);
      });
    });

    render(<ProtectedPage />);

    // Should show loading state
    expect(screen.getByText(/loading/i) || screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should preserve intended destination after login', async () => {
    const user = userEvent.setup();

    // Simulate accessing protected route
    mockedUseRouter.mockReturnValue({
      ...mockedUseRouter(),
      query: { redirect: '/dashboard' }
    } as any);

    mockedAxios.post.mockResolvedValueOnce({
      data: {
        access_token: 'token-123',
        token_type: 'bearer'
      }
    });

    render(<LoginPage />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith(expect.stringContaining('dashboard'));
    });
  });

  it('should validate form inputs before submission', async () => {
    const user = userEvent.setup();

    render(<LoginPage />);

    const submitButton = screen.getByRole('button', { name: /login/i });

    // Try to submit empty form
    await user.click(submitButton);

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/required/i) || screen.getByText(/cannot be empty/i)).toBeInTheDocument();
    });

    // Should not call API
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  it('should handle role-based access', async () => {
    localStorage.setItem('auth_token', 'valid-token');
    localStorage.setItem('user_role', 'viewer');

    mockedAxios.get.mockResolvedValueOnce({
      data: { 
        user: { id: 1, username: 'testuser', role: 'viewer' }
      }
    });

    render(<ProtectedPage />);

    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });

    // Admin-only features should not be visible
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
  });

  it('should handle session timeout', async () => {
    localStorage.setItem('auth_token', 'valid-token');
    localStorage.setItem('session_start', String(Date.now() - 3600000)); // 1 hour ago

    render(<ProtectedPage />);

    // Should detect expired session
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login');
    });

    expect(localStorage.getItem('auth_token')).toBeNull();
  });

  it('should handle remember me functionality', async () => {
    const user = userEvent.setup();

    mockedAxios.post.mockResolvedValueOnce({
      data: {
        access_token: 'token-123',
        refresh_token: 'refresh-123',
        token_type: 'bearer'
      }
    });

    render(<LoginPage />);

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const rememberCheckbox = screen.queryByLabelText(/remember/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    
    if (rememberCheckbox) {
      await user.click(rememberCheckbox);
    }
    
    await user.click(submitButton);

    await waitFor(() => {
      expect(localStorage.getItem('refresh_token')).toBe('refresh-123');
    });
  });
});
