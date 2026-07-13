/**
 * Unit tests for authService
 */

import authService from '../authService'
import apiClient from '../apiClient'

// Mock apiClient
jest.mock('../apiClient', () => ({
  apiClient: {
    post: jest.fn(),
    get: jest.fn(),
  },
}))

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.clear()
  })

  describe('login', () => {
    it('calls API with correct credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token-123',
          token_type: 'bearer',
          user_email: 'test@example.com',
          user_role: 'admin',
          expires_at: '2024-12-31T23:59:59Z',
        },
      }

      ;(apiClient.post as jest.Mock).mockResolvedValue(mockResponse)

      const result = await authService.login('test@example.com', 'password123')

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('handles login failure', async () => {
      const mockError = new Error('Invalid credentials')
      ;(apiClient.post as jest.Mock).mockRejectedValue(mockError)

      await expect(
        authService.login('test@example.com', 'wrong-password')
      ).rejects.toThrow('Invalid credentials')
    })
  })

  describe('verifyToken', () => {
    it('calls API with authorization header', async () => {
      const mockResponse = {
        data: {
          valid: true,
          user_email: 'test@example.com',
          user_role: 'admin',
        },
      }

      ;(apiClient.post as jest.Mock).mockResolvedValue(mockResponse)

      const result = await authService.verifyToken('test-token-123')

      expect(apiClient.post).toHaveBeenCalledWith(
        '/auth/verify',
        {},
        {
          headers: {
            Authorization: 'Bearer test-token-123',
          },
        }
      )
      expect(result).toEqual(mockResponse.data)
    })

    it('handles invalid token', async () => {
      const mockResponse = {
        data: {
          valid: false,
          message: 'Token expired',
        },
      }

      ;(apiClient.post as jest.Mock).mockResolvedValue(mockResponse)

      const result = await authService.verifyToken('expired-token')

      expect(result.valid).toBe(false)
      expect(result.message).toBe('Token expired')
    })
  })

  describe('getCurrentUser', () => {
    it('fetches current user with token', async () => {
      const mockResponse = {
        data: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          role: 'admin',
          is_active: true,
          created_at: '2023-01-01T00:00:00Z',
        },
      }

      ;(apiClient.get as jest.Mock).mockResolvedValue(mockResponse)

      const result = await authService.getCurrentUser('test-token-123')

      expect(apiClient.get).toHaveBeenCalledWith('/auth/me', {
        headers: {
          Authorization: 'Bearer test-token-123',
        },
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('handles unauthorized error', async () => {
      const mockError = new Error('Unauthorized')
      ;(apiClient.get as jest.Mock).mockRejectedValue(mockError)

      await expect(
        authService.getCurrentUser('invalid-token')
      ).rejects.toThrow('Unauthorized')
    })
  })

  describe('Token Storage', () => {
    it('stores token in localStorage', () => {
      authService.storeToken('test-token-123')

      expect(localStorage.setItem).toHaveBeenCalledWith('auth_token', 'test-token-123')
    })

    it('retrieves token from localStorage', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue('stored-token-456')

      const token = authService.getToken()

      expect(localStorage.getItem).toHaveBeenCalledWith('auth_token')
      expect(token).toBe('stored-token-456')
    })

    it('returns null when no token stored', () => {
      ;(localStorage.getItem as jest.Mock).mockReturnValue(null)

      const token = authService.getToken()

      expect(token).toBeNull()
    })

    it('removes token from localStorage', () => {
      authService.removeToken()

      expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token')
    })
  })

  describe('Edge Cases', () => {
    it('handles empty email in login', async () => {
      const mockResponse = { data: { error: 'Email required' } }
      ;(apiClient.post as jest.Mock).mockResolvedValue(mockResponse)

      await authService.login('', 'password')

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        email: '',
        password: 'password',
      })
    })

    it('handles empty password in login', async () => {
      const mockResponse = { data: { error: 'Password required' } }
      ;(apiClient.post as jest.Mock).mockResolvedValue(mockResponse)

      await authService.login('test@example.com', '')

      expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: '',
      })
    })

    it('handles network errors gracefully', async () => {
      const networkError = new Error('Network Error')
      ;(apiClient.post as jest.Mock).mockRejectedValue(networkError)

      await expect(
        authService.login('test@example.com', 'password')
      ).rejects.toThrow('Network Error')
    })
  })
})
