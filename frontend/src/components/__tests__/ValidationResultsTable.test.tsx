/**
 * Unit tests for ValidationResultsTable component
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import ValidationResultsTable, { ValidationResult } from '../ValidationResultsTable'

const mockResults: ValidationResult[] = [
  {
    validatorName: 'SchemaValidator',
    status: 'passed',
    passed: true,
    totalRecords: 1000,
    failedRecords: 0,
    passRate: 100,
    message: 'Schema validation passed',
    timestamp: '2023-03-20T10:00:00Z',
    executionTimeMs: 125.5,
    errors: [],
  },
  {
    validatorName: 'NullValidator',
    status: 'failed',
    passed: false,
    totalRecords: 1000,
    failedRecords: 50,
    passRate: 95,
    message: 'Null validation failed',
    timestamp: '2023-03-20T10:01:00Z',
    executionTimeMs: 89.2,
    errors: ['Column "email" contains null values'],
  },
  {
    validatorName: 'ChecksumValidator',
    status: 'passed',
    passed: true,
    totalRecords: 1000,
    failedRecords: 0,
    passRate: 100,
    message: 'Checksum validation passed',
    timestamp: '2023-03-20T10:02:00Z',
    executionTimeMs: 200.8,
    errors: [],
  },
]

describe('ValidationResultsTable', () => {
  describe('Basic Rendering', () => {
    it('renders table with results', () => {
      render(<ValidationResultsTable results={mockResults} />)
      
      expect(screen.getByText('SchemaValidator')).toBeInTheDocument()
      expect(screen.getByText('NullValidator')).toBeInTheDocument()
      expect(screen.getByText('ChecksumValidator')).toBeInTheDocument()
    })

    it('renders table headers correctly', () => {
      render(<ValidationResultsTable results={mockResults} />)
      
      expect(screen.getByText('Validator')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Total')).toBeInTheDocument()
      expect(screen.getByText('Failed')).toBeInTheDocument()
      expect(screen.getByText('Pass Rate')).toBeInTheDocument()
      expect(screen.getByText('Time (ms)')).toBeInTheDocument()
      expect(screen.getByText('Timestamp')).toBeInTheDocument()
    })

    it('displays correct data for each result', () => {
      render(<ValidationResultsTable results={mockResults} />)
      
      // Check first result
      expect(screen.getByText('1000')).toBeInTheDocument()
      expect(screen.getByText('100')).toBeInTheDocument()
      
      // Check failed records
      expect(screen.getByText('50')).toBeInTheDocument()
      expect(screen.getByText('95')).toBeInTheDocument()
    })
  })

  describe('Empty State', () => {
    it('displays empty state when no results', () => {
      render(<ValidationResultsTable results={[]} />)
      
      expect(screen.getByText('No validation results')).toBeInTheDocument()
      expect(screen.getByText('Run validations to see detailed results here.')).toBeInTheDocument()
    })

    it('does not render table when results are empty', () => {
      render(<ValidationResultsTable results={[]} />)
      
      expect(screen.queryByText('Validator')).not.toBeInTheDocument()
      expect(screen.queryByText('Status')).not.toBeInTheDocument()
    })
  })

  describe('Loading State', () => {
    it('displays loading skeleton when loading', () => {
      const { container } = render(
        <ValidationResultsTable results={mockResults} loading={true} />
      )
      
      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()
    })

    it('does not display results when loading', () => {
      render(<ValidationResultsTable results={mockResults} loading={true} />)
      
      expect(screen.queryByText('SchemaValidator')).not.toBeInTheDocument()
      expect(screen.queryByText('NullValidator')).not.toBeInTheDocument()
    })
  })

  describe('Row Click Handler', () => {
    it('calls onRowClick when row is clicked', () => {
      const handleRowClick = jest.fn()
      render(
        <ValidationResultsTable
          results={mockResults}
          onRowClick={handleRowClick}
        />
      )
      
      const firstRow = screen.getByText('SchemaValidator').closest('tr')
      fireEvent.click(firstRow!)
      
      expect(handleRowClick).toHaveBeenCalledTimes(1)
      expect(handleRowClick).toHaveBeenCalledWith(mockResults[0])
    })

    it('calls onRowClick with correct result', () => {
      const handleRowClick = jest.fn()
      render(
        <ValidationResultsTable
          results={mockResults}
          onRowClick={handleRowClick}
        />
      )
      
      const secondRow = screen.getByText('NullValidator').closest('tr')
      fireEvent.click(secondRow!)
      
      expect(handleRowClick).toHaveBeenCalledWith(mockResults[1])
    })

    it('does not add hover class when onRowClick is not provided', () => {
      const { container } = render(<ValidationResultsTable results={mockResults} />)
      
      const firstRow = screen.getByText('SchemaValidator').closest('tr')
      expect(firstRow).not.toHaveClass('cursor-pointer')
    })

    it('adds hover class when onRowClick is provided', () => {
      const handleRowClick = jest.fn()
      render(
        <ValidationResultsTable
          results={mockResults}
          onRowClick={handleRowClick}
        />
      )
      
      const firstRow = screen.getByText('SchemaValidator').closest('tr')
      expect(firstRow).toHaveClass('cursor-pointer')
    })
  })

  describe('Data Display', () => {
    it('displays execution time correctly', () => {
      render(<ValidationResultsTable results={mockResults} />)
      
      expect(screen.getByText('125.5')).toBeInTheDocument()
      expect(screen.getByText('89.2')).toBeInTheDocument()
      expect(screen.getByText('200.8')).toBeInTheDocument()
    })

    it('handles missing execution time', () => {
      const resultsWithoutTime: ValidationResult[] = [
        { ...mockResults[0], executionTimeMs: undefined },
      ]
      
      render(<ValidationResultsTable results={resultsWithoutTime} />)
      
      // Should still render without errors
      expect(screen.getByText('SchemaValidator')).toBeInTheDocument()
    })

    it('displays error messages correctly', () => {
      render(<ValidationResultsTable results={mockResults} />)
      
      // The NullValidator result has an error message
      expect(screen.getByText('Null validation failed')).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles single result', () => {
      render(<ValidationResultsTable results={[mockResults[0]]} />)
      
      expect(screen.getByText('SchemaValidator')).toBeInTheDocument()
      expect(screen.queryByText('NullValidator')).not.toBeInTheDocument()
    })

    it('handles large number of results', () => {
      const manyResults = Array.from({ length: 50 }, (_, i) => ({
        ...mockResults[0],
        validatorName: `Validator${i}`,
      }))
      
      render(<ValidationResultsTable results={manyResults} />)
      
      expect(screen.getByText('Validator0')).toBeInTheDocument()
      expect(screen.getByText('Validator49')).toBeInTheDocument()
    })

    it('handles results with 0 total records', () => {
      const zeroRecordResult: ValidationResult[] = [
        { ...mockResults[0], totalRecords: 0, failedRecords: 0 },
      ]
      
      render(<ValidationResultsTable results={zeroRecordResult} />)
      
      expect(screen.getByText('0')).toBeInTheDocument()
    })
  })
})
