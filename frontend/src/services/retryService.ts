/**
 * Retry Service
 * Handles API calls for validation retry operations
 */

import { apiRequest } from './apiClient';
import type { AxiosResponse } from 'axios';

/**
 * Retry request creation
 */
export interface CreateRetryRequest {
  validation_log_id: number;
  initiated_by: string;
  retry_reason?: string;
  max_retries?: number;
}

/**
 * Retry execution request
 */
export interface ExecuteRetryRequest {
  executor?: string;
}

/**
 * Bulk retry execution request
 */
export interface BulkExecuteRetryRequest {
  retry_ids: number[];
  executor?: string;
}

/**
 * Retry response
 */
export interface RetryResponse {
  retry_id: number;
  validation_log_id: number;
  retry_status: string;
  retry_count: number;
  max_retries: number;
  initiated_by: string;
  created_at: string;
  is_retryable: boolean;
}

/**
 * Retry execution result
 */
export interface RetryExecutionResult {
  retry_id: number;
  validation_log_id: number;
  success: boolean;
  message: string;
  new_validation_log_id?: number;
  execution_time_ms: number;
}

/**
 * Retry history item
 */
export interface RetryHistoryItem {
  retry_id: number;
  validation_log_id: number;
  retry_status: string;
  retry_count: number;
  max_retries: number;
  initiated_by: string;
  retry_reason?: string;
  created_at: string;
  last_retry_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_results?: any[];
  is_retryable: boolean;
}

/**
 * Failed validation item
 */
export interface FailedValidation {
  validation_log_id: number;
  dataset_name: string;
  validation_type: string;
  status: string;
  total_records: number;
  failed_records: number;
  pass_rate: number;
  validator_name: string;
  message: string;
  created_at: string;
  errors?: string[];
}

/**
 * Retry metrics
 */
export interface RetryMetrics {
  total_retries: number;
  status_breakdown: {
    pending: number;
    in_progress: number;
    completed: number;
    failed: number;
    cancelled: number;
  };
  success_rate: number;
  first_attempt_success_rate: number;
  average_retry_count: number;
  most_retried_validations: Array<{
    dataset_name: string;
    validation_type: string;
    retry_count: number;
  }>;
  period_days: number;
}

/**
 * Failure insights
 */
export interface FailureInsights {
  common_failure_patterns: Array<{
    pattern: string;
    count: number;
    validation_type: string;
    example_errors: string[];
  }>;
  total_unique_patterns: number;
  analysis_period_days: number;
}

class RetryService {
  private baseUrl = '/api/v1/retries';

  /**
   * Create a retry request for a failed validation
   */
  async createRetryRequest(request: CreateRetryRequest): Promise<RetryResponse> {
    const response: AxiosResponse<RetryResponse> = await apiRequest({
      url: this.baseUrl,
      method: 'POST',
      data: request,
    });
    return response.data;
  }

  /**
   * Execute a retry
   */
  async executeRetry(
    retryId: number,
    request: ExecuteRetryRequest
  ): Promise<RetryExecutionResult> {
    const response: AxiosResponse<RetryExecutionResult> = await apiRequest({
      url: `${this.baseUrl}/${retryId}/execute`,
      method: 'POST',
      data: request,
    });
    return response.data;
  }

  /**
   * Execute multiple retries in bulk
   */
  async executeBulkRetries(
    request: BulkExecuteRetryRequest
  ): Promise<any> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/execute-bulk`,
      method: 'POST',
      data: request,
    });
    return response.data;
  }

  /**
   * Get retry status
   */
  async getRetryStatus(retryId: number): Promise<RetryResponse> {
    const response: AxiosResponse<RetryResponse> = await apiRequest({
      url: `${this.baseUrl}/${retryId}`,
      method: 'GET',
    });
    return response.data;
  }

  /**
   * Cancel a retry
   */
  async cancelRetry(retryId: number, cancelledBy: string): Promise<RetryResponse> {
    const response: AxiosResponse<RetryResponse> = await apiRequest({
      url: `${this.baseUrl}/${retryId}/cancel`,
      method: 'POST',
      data: { cancelled_by: cancelledBy },
    });
    return response.data;
  }

  /**
   * Get retry history for a validation
   */
  async getValidationRetryHistory(validationLogId: number): Promise<any> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/validation/${validationLogId}/history`,
      method: 'GET',
    });
    return response.data;
  }

  /**
   * Get retry timeline for a validation
   */
  async getRetryTimeline(validationLogId: number): Promise<any> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/validation/${validationLogId}/timeline`,
      method: 'GET',
    });
    return response.data;
  }

  /**
   * Get pending retries
   */
  async getPendingRetries(limit: number = 100): Promise<any> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/pending`,
      method: 'GET',
      params: { limit },
    });
    return response.data;
  }

  /**
   * Get failed validations that can be retried
   */
  async getFailedValidations(
    datasetName?: string,
    validationType?: string,
    limit: number = 100
  ): Promise<{ total: number; validations: FailedValidation[] }> {
    const params: any = { limit };
    if (datasetName) params.dataset_name = datasetName;
    if (validationType) params.validation_type = validationType;

    const response: AxiosResponse<{ total: number; validations: FailedValidation[] }> =
      await apiRequest({
        url: `${this.baseUrl}/failed-validations`,
        method: 'GET',
        params,
      });
    return response.data;
  }

  /**
   * Get retry history with filters
   */
  async getRetryHistory(params: {
    validation_log_id?: number;
    dataset_name?: string;
    status?: string;
    initiated_by?: string;
    days_back?: number;
    limit?: number;
    offset?: number;
  }): Promise<{
    retries: RetryHistoryItem[];
    total_count: number;
    limit: number;
    offset: number;
    has_more: boolean;
  }> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/history`,
      method: 'GET',
      params,
    });
    return response.data;
  }

  /**
   * Get retry metrics
   */
  async getRetryMetrics(
    datasetName?: string,
    daysBack: number = 7
  ): Promise<RetryMetrics> {
    const params: any = { days_back: daysBack };
    if (datasetName) params.dataset_name = datasetName;

    const response: AxiosResponse<RetryMetrics> = await apiRequest({
      url: `${this.baseUrl}/metrics`,
      method: 'GET',
      params,
    });
    return response.data;
  }

  /**
   * Get user retry activity
   */
  async getUserRetryActivity(daysBack: number = 30): Promise<any> {
    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/user-activity`,
      method: 'GET',
      params: { days_back: daysBack },
    });
    return response.data;
  }

  /**
   * Get failure insights
   */
  async getFailureInsights(
    datasetName?: string,
    daysBack: number = 7
  ): Promise<FailureInsights> {
    const params: any = { days_back: daysBack };
    if (datasetName) params.dataset_name = datasetName;

    const response: AxiosResponse<FailureInsights> = await apiRequest({
      url: `${this.baseUrl}/failure-insights`,
      method: 'GET',
      params,
    });
    return response.data;
  }

  /**
   * Get retry statistics
   */
  async getRetryStatistics(validationLogId?: number): Promise<any> {
    const params: any = {};
    if (validationLogId) params.validation_log_id = validationLogId;

    const response: AxiosResponse<any> = await apiRequest({
      url: `${this.baseUrl}/statistics`,
      method: 'GET',
      params,
    });
    return response.data;
  }
}

// Export singleton instance
export const retryService = new RetryService();
export default retryService;
