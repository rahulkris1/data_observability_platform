/**
 * Unit tests for HealthScoreWidget component
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import HealthScoreWidget from '../HealthScoreWidget'

describe('HealthScoreWidget', () => {
  describe('Basic Rendering', () => {
    it('renders pipeline name correctly', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
        />
      )
      
      expect(screen.getByText('Pipeline Health')).toBeInTheDocument()
    })

    it('renders score correctly', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={85}
          status="healthy"
        />
      )
      
      // Score should be displayed somewhere in the component
      expect(screen.getByText(/85/)).toBeInTheDocument()
    })

    it('renders status badge', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
        />
      )
      
      expect(screen.getByText('HEALTHY')).toBeInTheDocument()
    })
  })

  describe('Status Colors', () => {
    it('displays green for healthy status', () => {
      const { container } = render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
        />
      )
      
      const badge = screen.getByText('HEALTHY')
      expect(badge).toHaveClass('text-green-700')
      expect(badge).toHaveClass('bg-green-50')
    })

    it('displays yellow for degraded status', () => {
      const { container } = render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={65}
          status="degraded"
        />
      )
      
      const badge = screen.getByText('DEGRADED')
      expect(badge).toHaveClass('text-yellow-700')
      expect(badge).toHaveClass('bg-yellow-50')
    })

    it('displays red for unhealthy status', () => {
      const { container } = render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={35}
          status="unhealthy"
        />
      )
      
      const badge = screen.getByText('UNHEALTHY')
      expect(badge).toHaveClass('text-red-700')
      expect(badge).toHaveClass('bg-red-50')
    })
  })

  describe('Loading State', () => {
    it('displays loading spinner when loading prop is true', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
          loading={true}
        />
      )
      
      expect(screen.getByText('Loading health score...')).toBeInTheDocument()
    })

    it('does not display content when loading', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
          loading={true}
        />
      )
      
      expect(screen.queryByText('HEALTHY')).not.toBeInTheDocument()
      expect(screen.queryByText(/95/)).not.toBeInTheDocument()
    })
  })

  describe('Timestamp Formatting', () => {
    it('displays "Just now" when no timestamp provided', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
        />
      )
      
      expect(screen.getByText('Just now')).toBeInTheDocument()
    })

    it('formats recent timestamp correctly', () => {
      const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString()
      
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={95}
          status="healthy"
          timestamp={fiveMinutesAgo}
        />
      )
      
      expect(screen.getByText(/5 minutes ago/)).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles score of 0', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={0}
          status="unhealthy"
        />
      )
      
      expect(screen.getByText(/0/)).toBeInTheDocument()
    })

    it('handles score of 100', () => {
      render(
        <HealthScoreWidget
          pipelineName="Test Pipeline"
          overallScore={100}
          status="healthy"
        />
      )
      
      expect(screen.getByText(/100/)).toBeInTheDocument()
    })

    it('renders with empty pipeline name', () => {
      render(
        <HealthScoreWidget
          pipelineName=""
          overallScore={95}
          status="healthy"
        />
      )
      
      expect(screen.getByText('Pipeline Health')).toBeInTheDocument()
    })
  })
})
