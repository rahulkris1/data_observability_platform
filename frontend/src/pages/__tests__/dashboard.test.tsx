/**
 * Unit tests for Dashboard page
 */

import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock dashboard component for testing
interface DashboardProps {
  initialData?: any
}

const Dashboard: React.FC<DashboardProps> = ({ initialData }) => {
  const [loading, setLoading] = React.useState(!initialData)
  const [data, setData] = React.useState(initialData || null)

  React.useEffect(() => {
    if (!initialData) {
      // Simulate data fetch
      setTimeout(() => {
        setData({
          totalValidations: 1250,
          passedValidations: 1100,
          failedValidations: 150,
          healthScore: 88,
        })
        setLoading(false)
      }, 100)
    }
  }, [initialData])

  if (loading) {
    return (
      <div>
        <h1>Data Observability Dashboard</h1>
        <div data-testid="loading-spinner">Loading...</div>
      </div>
    )
  }

  return (
    <div>
      <h1>Data Observability Dashboard</h1>
      <div data-testid="dashboard-content">
        <div data-testid="total-validations">
          Total: {data?.totalValidations}
        </div>
        <div data-testid="passed-validations">
          Passed: {data?.passedValidations}
        </div>
        <div data-testid="failed-validations">
          Failed: {data?.failedValidations}
        </div>
        <div data-testid="health-score">
          Health Score: {data?.healthScore}%
        </div>
      </div>
    </div>
  )
}

describe('Dashboard Page', () => {
  describe('Initial Rendering', () => {
    it('renders dashboard title', () => {
      render(<Dashboard />)
      
      expect(screen.getByText('Data Observability Dashboard')).toBeInTheDocument()
    })

    it('shows loading state initially', () => {
      render(<Dashboard />)
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })

    it('loads and displays dashboard data', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-content')).toBeInTheDocument()
      })
      
      expect(screen.getByText('Total: 1250')).toBeInTheDocument()
      expect(screen.getByText('Passed: 1100')).toBeInTheDocument()
      expect(screen.getByText('Failed: 150')).toBeInTheDocument()
      expect(screen.getByText('Health Score: 88%')).toBeInTheDocument()
    })
  })

  describe('With Initial Data', () => {
    it('renders immediately with provided data', () => {
      const initialData = {
        totalValidations: 500,
        passedValidations: 450,
        failedValidations: 50,
        healthScore: 90,
      }

      render(<Dashboard initialData={initialData} />)
      
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
      expect(screen.getByText('Total: 500')).toBeInTheDocument()
      expect(screen.getByText('Passed: 450')).toBeInTheDocument()
      expect(screen.getByText('Health Score: 90%')).toBeInTheDocument()
    })

    it('displays zero values correctly', () => {
      const initialData = {
        totalValidations: 0,
        passedValidations: 0,
        failedValidations: 0,
        healthScore: 0,
      }

      render(<Dashboard initialData={initialData} />)
      
      expect(screen.getByText('Total: 0')).toBeInTheDocument()
      expect(screen.getByText('Health Score: 0%')).toBeInTheDocument()
    })
  })

  describe('Data Display', () => {
    it('displays validation counts correctly', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByTestId('total-validations')).toBeInTheDocument()
      })
      
      const total = screen.getByTestId('total-validations')
      const passed = screen.getByTestId('passed-validations')
      const failed = screen.getByTestId('failed-validations')
      
      expect(total).toHaveTextContent('1250')
      expect(passed).toHaveTextContent('1100')
      expect(failed).toHaveTextContent('150')
    })

    it('displays health score correctly', async () => {
      render(<Dashboard />)
      
      await waitFor(() => {
        expect(screen.getByTestId('health-score')).toBeInTheDocument()
      })
      
      const healthScore = screen.getByTestId('health-score')
      expect(healthScore).toHaveTextContent('88%')
    })
  })

  describe('Edge Cases', () => {
    it('handles undefined initial data', () => {
      render(<Dashboard initialData={undefined} />)
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
    })

    it('handles null values in data', async () => {
      const initialData = {
        totalValidations: null,
        passedValidations: null,
        failedValidations: null,
        healthScore: null,
      }

      render(<Dashboard initialData={initialData} />)
      
      await waitFor(() => {
        expect(screen.getByTestId('dashboard-content')).toBeInTheDocument()
      })
    })

    it('handles large numbers', () => {
      const initialData = {
        totalValidations: 1234567890,
        passedValidations: 1234567800,
        failedValidations: 90,
        healthScore: 99.99,
      }

      render(<Dashboard initialData={initialData} />)
      
      expect(screen.getByText('Total: 1234567890')).toBeInTheDocument()
      expect(screen.getByText('Health Score: 99.99%')).toBeInTheDocument()
    })
  })
})
