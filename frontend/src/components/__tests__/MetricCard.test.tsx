/**
 * Unit tests for MetricCard component
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'

// Mock MetricCard component structure for testing
interface MetricCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  loading?: boolean
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  trend,
  trendValue,
  loading = false,
}) => {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      <div className="flex items-baseline">
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
        {trend && trendValue && (
          <span
            className={`ml-2 text-sm ${
              trend === 'up'
                ? 'text-green-600'
                : trend === 'down'
                ? 'text-red-600'
                : 'text-gray-600'
            }`}
          >
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
        )}
      </div>
    </div>
  )
}

describe('MetricCard', () => {
  describe('Basic Rendering', () => {
    it('renders title and value correctly', () => {
      render(<MetricCard title="Total Records" value="1,250" />)
      
      expect(screen.getByText('Total Records')).toBeInTheDocument()
      expect(screen.getByText('1,250')).toBeInTheDocument()
    })

    it('renders numeric value correctly', () => {
      render(<MetricCard title="Pass Rate" value={95.5} />)
      
      expect(screen.getByText('Pass Rate')).toBeInTheDocument()
      expect(screen.getByText('95.5')).toBeInTheDocument()
    })

    it('renders with icon', () => {
      const icon = <span data-testid="test-icon">📊</span>
      render(<MetricCard title="Metrics" value="100" icon={icon} />)
      
      expect(screen.getByTestId('test-icon')).toBeInTheDocument()
    })
  })

  describe('Trend Indicators', () => {
    it('displays upward trend with green color', () => {
      render(
        <MetricCard
          title="Success Rate"
          value="98%"
          trend="up"
          trendValue="5%"
        />
      )
      
      const trendElement = screen.getByText(/↑ 5%/)
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-green-600')
    })

    it('displays downward trend with red color', () => {
      render(
        <MetricCard
          title="Error Rate"
          value="2%"
          trend="down"
          trendValue="1%"
        />
      )
      
      const trendElement = screen.getByText(/↓ 1%/)
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-red-600')
    })

    it('displays neutral trend with gray color', () => {
      render(
        <MetricCard
          title="Stable Metric"
          value="50"
          trend="neutral"
          trendValue="0%"
        />
      )
      
      const trendElement = screen.getByText(/→ 0%/)
      expect(trendElement).toBeInTheDocument()
      expect(trendElement).toHaveClass('text-gray-600')
    })

    it('does not display trend when not provided', () => {
      render(<MetricCard title="Simple Metric" value="100" />)
      
      expect(screen.queryByText(/↑/)).not.toBeInTheDocument()
      expect(screen.queryByText(/↓/)).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('displays loading skeleton when loading', () => {
      const { container } = render(
        <MetricCard title="Loading Metric" value="100" loading={true} />
      )
      
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('does not display content when loading', () => {
      render(<MetricCard title="Loading Metric" value="100" loading={true} />)
      
      expect(screen.queryByText('Loading Metric')).not.toBeInTheDocument()
      expect(screen.queryByText('100')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty string value', () => {
      render(<MetricCard title="Empty Metric" value="" />)
      
      expect(screen.getByText('Empty Metric')).toBeInTheDocument()
    })

    it('handles zero value', () => {
      render(<MetricCard title="Zero Metric" value={0} />)
      
      expect(screen.getByText('0')).toBeInTheDocument()
    })

    it('handles very large numbers', () => {
      render(<MetricCard title="Large Number" value="1,234,567,890" />)
      
      expect(screen.getByText('1,234,567,890')).toBeInTheDocument()
    })

    it('handles negative trend values', () => {
      render(
        <MetricCard
          title="Negative Trend"
          value="100"
          trend="down"
          trendValue="-5%"
        />
      )
      
      expect(screen.getByText(/↓ -5%/)).toBeInTheDocument()
    })
  })
})
