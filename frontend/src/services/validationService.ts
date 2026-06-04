/**
 * Validation Service
 * Handles API calls for validation execution and audit history retrieval
 */

import { apiRequest } from './apiClient';
import type { AxiosResponse } from 'axios';

/**
 * Validator result for individual validation
 */
export interface ValidatorResult {
  validator_name: string;
  status: string;
  passed: boolean;
  total_records: number;
  failed_records: number;
  pass_rate: number;
  message: string;
  execution_time_ms?: number;
  errors: string[];
}

/**
 * Validation execution request
 */
export interface ValidationExecutionRequest {
  dataset_name: string;
  dataset_path?: string;
  validation_types?: string[];
  schema_contract_id?: number;
  null_threshold?: number;
}

/**
 * Validation execution response
 */
export interface ValidationExecutionResponse {
  dataset_name: string;
  validation_timestamp: string;
  overall_status: string;
  overall_passed: boolean;
  total_validators: number;
  passed_validators: number;
  failed_validators: number;
  warning_validators: number;
  error_validators: number;
  total_records: number;
  total_execution_time_ms: number;
  validators: ValidatorResult[];
  metadata: Record<string, any>;
}

/**
 * Audit history item
 */
export interface AuditHistoryItem {
  id: number;
  dataset_name: string;
  validation_type: string;
  status: string;
  validator_name: string;
  total_records: number;
  failed_records: number;
  pass_rate: number;
  execution_time_ms?: number;
  triggered_by: string;
  environment: string;
  created_at: string;
  error_summary?: string;
}

/**
 * Audit history response
 */
export interface AuditHistoryResponse {
  total_count: number;
  items: AuditHistoryItem[];
  limit: number;
  offset: number;
}

/**
 * Audit history filters
 */
export interface AuditHistoryFilters {
  dataset_name?: string;
  validation_type?: string;
  status?: string;
  triggered_by?: string;
  environment?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/**
 * API error response
 */
export interface APIErrorResponse {
  status_code: number;
  error: string;
  message: string;
  details?: Array<{
    field?: string;
    message: string;
    type?: string;
  }>;
  timestamp: string;
}

/**
 * Validation Service class
 */
class ValidationService {
  /**
   * Execute validation on a dataset
   * @param request - Validation execution request
   * @returns Promise with validation execution response
   */
  async executeValidation(
    request: ValidationExecutionRequest
  ): Promise<ValidationExecutionResponse> {
    try {
      const response: AxiosResponse<ValidationExecutionResponse> = await apiRequest.post(
        '/validations/execute',
        request
      );
      return response.data;
    } catch (error: any) {
      console.error('Error executing validation:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Get audit history with optional filters
   * @param filters - Optional filters for audit history
   * @returns Promise with audit history response
   */
  async getAuditHistory(
    filters?: AuditHistoryFilters
  ): Promise<AuditHistoryResponse> {
    try {
      const params = new URLSearchParams();
      
      if (filters) {
        if (filters.dataset_name) params.append('dataset_name', filters.dataset_name);
        if (filters.validation_type) params.append('validation_type', filters.validation_type);
        if (filters.status) params.append('status', filters.status);
        if (filters.triggered_by) params.append('triggered_by', filters.triggered_by);
        if (filters.environment) params.append('environment', filters.environment);
        if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
        if (filters.offset !== undefined) params.append('offset', filters.offset.toString());
        if (filters.sort_by) params.append('sort_by', filters.sort_by);
        if (filters.sort_order) params.append('sort_order', filters.sort_order);
      }
      
      const queryString = params.toString();
      const url = queryString ? `/audit/history?${queryString}` : '/audit/history';
      
      const response: AxiosResponse<AuditHistoryResponse> = await apiRequest.get(url);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching audit history:', error);
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors and format them consistently
   * @param error - Error from API call
   * @returns Formatted error
   */
  private handleError(error: any): Error {
    if (error.response?.data) {
      const apiError = error.response.data as APIErrorResponse;
      const message = apiError.message || error.message || 'An error occurred';
      return new Error(message);
    }
    
    if (error.request) {
      return new Error('Network error - unable to reach the server');
    }
    
    return new Error(error.message || 'An unexpected error occurred');
  }
}

// Export singleton instance
export const validationService = new ValidationService();

// Export the class for testing
export default ValidationService;
