/**
 * Observability API Service
 * 
 * Handles all API calls related to logs and metrics
 */

import { apiRequest } from './apiClient';

/**
 * Log Entry Record
 */
export interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  module?: string;
  function?: string;
  line?: number;
  extra_fields?: Record<string, any>;
  [key: string]: any;
}

/**
 * Logs Request Parameters
 */
export interface LogsParams {
  page?: number;
  page_size?: number;
  level?: string;
  logger?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * Logs Response
 */
export interface LogsResponse {
  logs: LogEntry[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * Log Statistics Response
 */
export interface LogStatistics {
  total_lines: number;
  file_size_bytes: number;
  levels: Record<string, number>;
  loggers: Record<string, number>;
}

/**
 * Metrics Response
 */
export interface MetricsResponse {
  counters: Record<string, any>;
  histograms: Record<string, any>;
  timestamp: string;
}

/**
 * Fetch application logs
 */
export async function getLogs(params: LogsParams = {}): Promise<LogsResponse> {
  const queryParams = new URLSearchParams();
  
  if (params.page !== undefined) queryParams.append('page', params.page.toString());
  if (params.page_size !== undefined) queryParams.append('page_size', params.page_size.toString());
  if (params.level) queryParams.append('level', params.level);
  if (params.logger) queryParams.append('logger', params.logger);
  if (params.search) queryParams.append('search', params.search);
  if (params.start_date) queryParams.append('start_date', params.start_date);
  if (params.end_date) queryParams.append('end_date', params.end_date);
  
  const url = `/api/v1/observability/logs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return apiRequest<LogsResponse>(url);
}

/**
 * Fetch log statistics
 */
export async function getLogStatistics(): Promise<LogStatistics> {
  return apiRequest<LogStatistics>('/api/v1/observability/logs/stats');
}

/**
 * Fetch application metrics
 */
export async function getMetrics(): Promise<MetricsResponse> {
  return apiRequest<MetricsResponse>('/api/v1/observability/metrics');
}

/**
 * Reset application metrics
 */
export async function resetMetrics(): Promise<{ message: string }> {
  return apiRequest<{ message: string }>('/api/v1/observability/metrics/reset', {
    method: 'POST',
  });
}
