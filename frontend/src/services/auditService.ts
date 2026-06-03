/**
 * Audit API Service
 * 
 * Handles all API calls related to audit logs and history
 */

import { apiRequest } from './apiClient';

/**
 * Audit Log Record
 */
export interface AuditLog {
  id: number;
  dataset_name: string;
  validation_type: string;
  status: string;
  execution_time_ms: number | null;
  total_records: number;
  failed_records: number;
  pass_rate: number;
  validator_name: string;
  triggered_by: string;
  environment: string;
  metadata: Record<string, any> | null;
  error_summary: string | null;
  details: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

/**
 * Audit History Request Parameters
 */
export interface AuditHistoryParams {
  dataset_name?: string;
  validation_type?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  triggered_by?: string;
  environment?: string;
  limit?: number;
  offset?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

/**
 * Audit History Response
 */
export interface AuditHistoryResponse {
  total_count: number;
  page: number;
  page_size: number;
  audits: AuditLog[];
}

/**
 * Audit Statistics Response
 */
export interface AuditStatistics {
  total_audits: number;
  status_distribution: Record<string, number>;
  validation_type_distribution: Record<string, number>;
  average_execution_time_ms: number;
}

/**
 * Filter Options
 */
export interface AuditFilterOptions {
  datasets: string[];
  validation_types: string[];
  statuses: string[];
  triggered_by: string[];
  environments: string[];
}

/**
 * Get audit history with optional filters and pagination
 */
export const getAuditHistory = async (
  params?: AuditHistoryParams
): Promise<AuditHistoryResponse> => {
  const response = await apiRequest.get<AuditHistoryResponse>('/audit/history', {
    params,
  });
  return response.data;
};

/**
 * Get a specific audit record by ID
 */
export const getAuditById = async (auditId: number): Promise<AuditLog> => {
  const response = await apiRequest.get<AuditLog>(`/audit/${auditId}`);
  return response.data;
};

/**
 * Get audit statistics
 */
export const getAuditStatistics = async (
  dataset_name?: string,
  start_date?: string,
  end_date?: string
): Promise<AuditStatistics> => {
  const response = await apiRequest.get<AuditStatistics>('/audit/statistics/summary', {
    params: { dataset_name, start_date, end_date },
  });
  return response.data;
};

/**
 * Get available filter options
 */
export const getFilterOptions = async (): Promise<AuditFilterOptions> => {
  const response = await apiRequest.get<AuditFilterOptions>('/audit/filters/options');
  return response.data;
};

/**
 * Get recent audit records
 */
export const getRecentAudits = async (limit: number = 10): Promise<AuditLog[]> => {
  const response = await apiRequest.get<AuditLog[]>('/audit/recent/list', {
    params: { limit },
  });
  return response.data;
};

/**
 * Create a new audit record
 */
export const createAuditRecord = async (
  auditData: Omit<AuditLog, 'id' | 'created_at' | 'updated_at'>
): Promise<AuditLog> => {
  const response = await apiRequest.post<AuditLog>('/audit/', auditData);
  return response.data;
};
