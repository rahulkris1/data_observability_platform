/**
 * Unit tests for Authentication Flow
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock authentication flow component
interface AuthFlowProps {
  onLoginSuccess?: (token: string) => void
  onLoginError?: (error: string) => void
}

const AuthFlow: React.FC<AuthFlowProps> = ({ onLoginSuccess, onLoginError }) => {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState('')
  const [isAuthenticated, setIsAuthenticated] = React.useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      // Simulate API call
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          if (email === 'test@example.com' && password === 'password123') {
            resolve({ token: 'mock-token-123' })
          } else {
            reject(new Error('Invalid credentials'))
          }
        }, 100)
      })

      setIsAuthenticated(true)
      if (onLoginSuccess) {
        onLoginSuccess('mock-token-123')
      }
    } catch (err: any) {
      const errorMsg = err.message || 'Login failed'
      setError(errorMsg)
      if (onLoginError) {
        onLoginError(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setEmail('')
    setPassword('')
  }

  if (isAuthenticated) {
    return (
      <div>
        <h2>Welcome!</h2>
        <p data-testid="auth-status">You are logged in</p>
        <button onClick={handleLogout} data-testid="logout-button">
          Logout
        </button>
      </div>
    )
  }

  return (
    <div>
      <h2>Login</h2>
      <form onSubmit={handleLogin} data-testid="login-form">
        {error && (
          <div data-testid="error-message" className="text-red-600">
            {error}
          </div>
        )}
        
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            data-testid="email-input"
            disabled={loading}
          />
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            data-testid="password-input"
            disabled={loading}
          />
        </div>

        <button type="submit" data-testid="submit-button" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  )
}

describe('Authentication Flow', () => {
  describe('Login Form Rendering', () => {
    it('renders login form', () => {
      render(<AuthFlow />)
      
      expect(screen.getByText('Login')).toBeInTheDocument()
      expect(screen.getByTestId('email-input')).toBeInTheDocument()
      expect(screen.getByTestId('password-input')).toBeInTheDocument()
      expect(screen.getByTestId('submit-button')).toBeInTheDocument()
    })

    it('has empty inputs initially', () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input') as HTMLInputElement
      const passwordInput = screen.getByTestId('password-input') as HTMLInputElement
      
      expect(emailInput.value).toBe('')
      expect(passwordInput.value).toBe('')
    })

    it('has submit button enabled initially', () => {
      render(<AuthFlow />)
      
      const submitButton = screen.getByTestId('submit-button') as HTMLButtonElement
      expect(submitButton.disabled).toBe(false)
    })
  })

  describe('Form Input Handling', () => {
    it('updates email input on change', () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input') as HTMLInputElement
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      
      expect(emailInput.value).toBe('test@example.com')
    })

    it('updates password input on change', () => {
      render(<AuthFlow />)
      
      const passwordInput = screen.getByTestId('password-input') as HTMLInputElement
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      
      expect(passwordInput.value).toBe('password123')
    })

    it('handles multiple input changes', () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input') as HTMLInputElement
      const passwordInput = screen.getByTestId('password-input') as HTMLInputElement
      
      fireEvent.change(emailInput, { target: { value: 'user@test.com' } })
      fireEvent.change(passwordInput, { target: { value: 'mypassword' } })
      
      expect(emailInput.value).toBe('user@test.com')
      expect(passwordInput.value).toBe('mypassword')
    })
  })

  describe('Successful Login', () => {
    it('calls onLoginSuccess with token on successful login', async () => {
      const mockOnSuccess = jest.fn()
      render(<AuthFlow onLoginSuccess={mockOnSuccess} />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(mockOnSuccess).toHaveBeenCalledWith('mock-token-123')
      })
    })

    it('displays welcome message after successful login', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText('Welcome!')).toBeInTheDocument()
        expect(screen.getByText('You are logged in')).toBeInTheDocument()
      })
    })

    it('hides login form after successful authentication', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.queryByTestId('login-form')).not.toBeInTheDocument()
      })
    })
  })

  describe('Failed Login', () => {
    it('displays error message on invalid credentials', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('error-message')).toBeInTheDocument()
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      })
    })

    it('calls onLoginError with error message', async () => {
      const mockOnError = jest.fn()
      render(<AuthFlow onLoginError={mockOnError} />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('Invalid credentials')
      })
    })

    it('keeps login form visible after failed login', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('login-form')).toBeInTheDocument()
      })
    })
  })

  describe('Loading State', () => {
    it('shows loading text on submit button during login', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      // Check loading state immediately after click
      expect(screen.getByText('Logging in...')).toBeInTheDocument()
    })

    it('disables inputs during login', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input') as HTMLInputElement
      const passwordInput = screen.getByTestId('password-input') as HTMLInputElement
      const submitButton = screen.getByTestId('submit-button') as HTMLButtonElement
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      // Check that inputs are disabled during loading
      expect(emailInput.disabled).toBe(true)
      expect(passwordInput.disabled).toBe(true)
      expect(submitButton.disabled).toBe(true)
    })
  })

  describe('Logout Flow', () => {
    it('displays logout button when authenticated', async () => {
      render(<AuthFlow />)
      
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('logout-button')).toBeInTheDocument()
      })
    })

    it('returns to login form after logout', async () => {
      render(<AuthFlow />)
      
      // Login first
      const emailInput = screen.getByTestId('email-input')
      const passwordInput = screen.getByTestId('password-input')
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('logout-button')).toBeInTheDocument()
      })
      
      // Logout
      const logoutButton = screen.getByTestId('logout-button')
      fireEvent.click(logoutButton)
      
      // Should show login form again
      expect(screen.getByTestId('login-form')).toBeInTheDocument()
      expect(screen.queryByText('Welcome!')).not.toBeInTheDocument()
    })

    it('clears form inputs after logout', async () => {
      render(<AuthFlow />)
      
      // Login
      const emailInput = screen.getByTestId('email-input') as HTMLInputElement
      const passwordInput = screen.getByTestId('password-input') as HTMLInputElement
      const submitButton = screen.getByTestId('submit-button')
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByTestId('logout-button')).toBeInTheDocument()
      })
      
      // Logout
      const logoutButton = screen.getByTestId('logout-button')
      fireEvent.click(logoutButton)
      
      // Check inputs are cleared
      const emailInputAfter = screen.getByTestId('email-input') as HTMLInputElement
      const passwordInputAfter = screen.getByTestId('password-input') as HTMLInputElement
      
      expect(emailInputAfter.value).toBe('')
      expect(passwordInputAfter.value).toBe('')
    })
  })
})
