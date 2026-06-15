/**
 * Load Monitoring Service
 * API client for warehouse load monitoring endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface LoadAuditLog {
  id: number;
  batch_id: string;
  dataset_name: string;
  load_status: 'started' | 'completed' | 'failed' | 'retrying';
  load_started_at: string | null;
  load_completed_at: string | null;
  source_record_count: number | null;
  warehouse_record_count: number | null;
  records_inserted: number | null;
  records_updated: number | null;
  records_failed: number | null;
  execution_time_seconds: number | null;
  triggered_by: string | null;
  notes: string | null;
}

export interface LoadStatistics {
  total_loads: number;
  completed_loads: number;
  failed_loads: number;
  retrying_loads: number;
  success_rate: number;
  average_execution_time_seconds: number;
  period_days: number;
  dataset_name: string | null;
}

export interface FailedLoad {
  id: number;
  batch_id: string;
  dataset_name: string;
  failure_reason: string;
  error_message: string | null;
  source_record_count: number | null;
  warehouse_record_count: number | null;
  failed_record_count: number | null;
  retry_count: number;
  can_retry: boolean;
  load_failed_at: string | null;
  retry_validated_at: string | null;
  retry_validated_by: string | null;
}

export interface RetryValidationResult {
  batch_id: string;
  can_retry: boolean;
  validation_status: string;
  checks_passed: string[];
  checks_failed: string[];
  recommendations: string[];
  retry_count: number;
  validated_by: string;
  validated_at: string;
}

export class LoadMonitoringService {
  /**
   * Get load history with optional filters
   */
  static async getLoadHistory(params: {
    dataset_name?: string;
    status?: string;
    days?: number;
    limit?: number;
  }): Promise<LoadAuditLog[]> {
    const queryParams = new URLSearchParams();
    
    if (params.dataset_name) queryParams.append('dataset_name', params.dataset_name);
    if (params.status) queryParams.append('status', params.status);
    if (params.days) queryParams.append('days', params.days.toString());
    if (params.limit) queryParams.append('limit', params.limit.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/audit/history?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch load history');
    }

    const data = await response.json();
    return data.history || [];
  }

  /**
   * Get load statistics
   */
  static async getLoadStatistics(params: {
    dataset_name?: string;
    days?: number;
  }): Promise<LoadStatistics> {
    const queryParams = new URLSearchParams();
    
    if (params.dataset_name) queryParams.append('dataset_name', params.dataset_name);
    if (params.days) queryParams.append('days', params.days.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/audit/statistics?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch load statistics');
    }

    const data = await response.json();
    return data.statistics;
  }

  /**
   * Verify a batch load
   */
  static async verifyBatchLoad(params: {
    batch_id: string;
    dataset_name: string;
    source_record_count?: number;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    queryParams.append('dataset_name', params.dataset_name);
    if (params.source_record_count) {
      queryParams.append('source_record_count', params.source_record_count.toString());
    }

    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/verify/batch/${params.batch_id}?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to verify batch load');
    }

    const data = await response.json();
    return data.verification;
  }

  /**
   * Get retry-ready loads
   */
  static async getRetryReadyLoads(params: {
    dataset_name?: string;
    limit?: number;
  }): Promise<FailedLoad[]> {
    const queryParams = new URLSearchParams();
    
    if (params.dataset_name) queryParams.append('dataset_name', params.dataset_name);
    if (params.limit) queryParams.append('limit', params.limit.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/retry/ready?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch retry-ready loads');
    }

    const data = await response.json();
    return data.retry_ready_loads || [];
  }

  /**
   * Get failed loads summary
   */
  static async getFailedLoadsSummary(params: {
    dataset_name?: string;
  }): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params.dataset_name) queryParams.append('dataset_name', params.dataset_name);

    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/retry/summary?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch failed loads summary');
    }

    const data = await response.json();
    return data.summary;
  }

  /**
   * Validate a failed load for retry
   */
  static async validateForRetry(params: {
    batch_id: string;
    validated_by: string;
    validation_notes?: string;
  }): Promise<RetryValidationResult> {
    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/retry/validate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to validate retry');
    }

    const data = await response.json();
    return data.validation;
  }

  /**
   * Revoke retry approval
   */
  static async revokeRetryApproval(params: {
    batch_id: string;
    revoked_by: string;
    reason?: string;
  }): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/retry/revoke`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to revoke retry approval');
    }
  }

  /**
   * Log load start
   */
  static async logLoadStart(params: {
    batch_id: string;
    dataset_name: string;
    source_system?: string;
    source_record_count?: number;
    triggered_by?: string;
    metadata?: any;
  }): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/audit/start`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to log load start');
    }

    return await response.json();
  }

  /**
   * Log load completion
   */
  static async logLoadCompletion(params: {
    batch_id: string;
    warehouse_record_count: number;
    records_inserted?: number;
    records_updated?: number;
    records_failed?: number;
    notes?: string;
    metadata?: any;
  }): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/audit/complete`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to log load completion');
    }

    return await response.json();
  }

  /**
   * Log load failure
   */
  static async logLoadFailure(params: {
    batch_id: string;
    failure_reason: string;
    error_message?: string;
    warehouse_record_count?: number;
    failed_record_count?: number;
    notes?: string;
    metadata?: any;
  }): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/load-monitoring/audit/fail`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to log load failure');
    }

    return await response.json();
  }
}

export default LoadMonitoringService;
