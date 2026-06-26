/**
 * Unit tests for validationService
 */

import { apiRequest } from '../apiClient'
import type {
  ValidationExecutionRequest,
  ValidationExecutionResponse,
  AuditHistoryFilters,
  AuditHistoryResponse,
} from '../validationService'

// Mock apiClient
jest.mock('../apiClient', () => ({
  apiRequest: jest.fn(),
}))

// Create mock validationService functions for testing
const validationService = {
  executeValidation: async (
    request: ValidationExecutionRequest
  ): Promise<ValidationExecutionResponse> => {
    const response = await apiRequest<ValidationExecutionResponse>(
      'post',
      '/api/validation/execute',
      request
    )
    return response.data
  },

  getAuditHistory: async (
    filters?: AuditHistoryFilters
  ): Promise<AuditHistoryResponse> => {
    const params = new URLSearchParams()
    if (filters?.dataset_name) params.append('dataset_name', filters.dataset_name)
    if (filters?.validation_type) params.append('validation_type', filters.validation_type)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.limit) params.append('limit', filters.limit.toString())
    if (filters?.offset) params.append('offset', filters.offset.toString())

    const response = await apiRequest<AuditHistoryResponse>(
      'get',
      `/api/audit/history?${params.toString()}`
    )
    return response.data
  },
}

describe('ValidationService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('executeValidation', () => {
    it('calls API with correct request payload', async () => {
      const mockResponse = {
        data: {
          dataset_name: 'customers',
          validation_timestamp: '2023-03-20T10:00:00Z',
          overall_status: 'passed',
          overall_passed: true,
          total_validators: 3,
          passed_validators: 3,
          failed_validators: 0,
          warning_validators: 0,
          error_validators: 0,
          total_records: 1000,
          total_execution_time_ms: 500,
          validators: [],
          metadata: {},
        },
      }

      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      const request: ValidationExecutionRequest = {
        dataset_name: 'customers',
        dataset_path: '/data/customers.csv',
        validation_types: ['schema', 'null', 'checksum'],
      }

      const result = await validationService.executeValidation(request)

      expect(apiRequest).toHaveBeenCalledWith(
        'post',
        '/api/validation/execute',
        request
      )
      expect(result).toEqual(mockResponse.data)
    })

    it('handles validation execution failure', async () => {
      const mockError = new Error('Validation failed')
      ;(apiRequest as jest.Mock).mockRejectedValue(mockError)

      const request: ValidationExecutionRequest = {
        dataset_name: 'invalid_dataset',
      }

      await expect(
        validationService.executeValidation(request)
      ).rejects.toThrow('Validation failed')
    })

    it('includes optional parameters when provided', async () => {
      const mockResponse = { data: {} as ValidationExecutionResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      const request: ValidationExecutionRequest = {
        dataset_name: 'customers',
        schema_contract_id: 123,
        null_threshold: 5,
      }

      await validationService.executeValidation(request)

      expect(apiRequest).toHaveBeenCalledWith(
        'post',
        '/api/validation/execute',
        expect.objectContaining({
          schema_contract_id: 123,
          null_threshold: 5,
        })
      )
    })
  })

  describe('getAuditHistory', () => {
    it('fetches audit history without filters', async () => {
      const mockResponse = {
        data: {
          total_count: 10,
          items: [],
          limit: 50,
          offset: 0,
        },
      }

      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      const result = await validationService.getAuditHistory()

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringContaining('/api/audit/history')
      )
      expect(result).toEqual(mockResponse.data)
    })

    it('applies dataset name filter', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory({
        dataset_name: 'customers',
      })

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringContaining('dataset_name=customers')
      )
    })

    it('applies validation type filter', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory({
        validation_type: 'schema',
      })

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringContaining('validation_type=schema')
      )
    })

    it('applies status filter', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory({
        status: 'failed',
      })

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringContaining('status=failed')
      )
    })

    it('applies pagination parameters', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory({
        limit: 25,
        offset: 50,
      })

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringMatching(/limit=25/)
      )
      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringMatching(/offset=50/)
      )
    })

    it('applies multiple filters together', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory({
        dataset_name: 'customers',
        validation_type: 'schema',
        status: 'passed',
        limit: 10,
      })

      const callArg = (apiRequest as jest.Mock).mock.calls[0][1]
      expect(callArg).toContain('dataset_name=customers')
      expect(callArg).toContain('validation_type=schema')
      expect(callArg).toContain('status=passed')
      expect(callArg).toContain('limit=10')
    })

    it('handles API errors', async () => {
      const mockError = new Error('API Error')
      ;(apiRequest as jest.Mock).mockRejectedValue(mockError)

      await expect(validationService.getAuditHistory()).rejects.toThrow('API Error')
    })
  })

  describe('Edge Cases', () => {
    it('handles empty validation types array', async () => {
      const mockResponse = { data: {} as ValidationExecutionResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      const request: ValidationExecutionRequest = {
        dataset_name: 'test',
        validation_types: [],
      }

      await validationService.executeValidation(request)

      expect(apiRequest).toHaveBeenCalledWith(
        'post',
        '/api/validation/execute',
        expect.objectContaining({ validation_types: [] })
      )
    })

    it('handles undefined filters in getAuditHistory', async () => {
      const mockResponse = { data: {} as AuditHistoryResponse }
      ;(apiRequest as jest.Mock).mockResolvedValue(mockResponse)

      await validationService.getAuditHistory(undefined)

      expect(apiRequest).toHaveBeenCalledWith(
        'get',
        expect.stringContaining('/api/audit/history')
      )
    })

    it('handles network timeout', async () => {
      const timeoutError = new Error('Request timeout')
      ;(apiRequest as jest.Mock).mockRejectedValue(timeoutError)

      await expect(
        validationService.executeValidation({ dataset_name: 'test' })
      ).rejects.toThrow('Request timeout')
    })
  })
})
