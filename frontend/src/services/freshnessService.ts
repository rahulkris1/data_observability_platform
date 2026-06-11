/**
 * Freshness Monitoring Service
 * Handles API calls for freshness, latency, and SLA metrics
 */

import { apiRequest } from './apiClient';

/**
 * Freshness validation result
 */
export interface FreshnessValidationResult {
  dataset_name: string;
  ingestion_timestamp: string;
  validation_timestamp?: string;
  dataset_age_hours: number;
  freshness_status: string;
  freshness_threshold_hours: number;
  is_fresh: boolean;
  message?: string;
}

/**
 * Latency metrics
 */
export interface LatencyMetrics {
  dataset_name: string;
  ingestion_start_time?: string;
  ingestion_end_time?: string;
  ingestion_latency_seconds?: number;
  validation_start_time?: string;
  validation_end_time?: string;
  validation_latency_seconds?: number;
  total_latency_seconds?: number;
}

/**
 * SLA evaluation result
 */
export interface SLAEvaluationResult {
  dataset_name: string;
  sla_threshold_hours: number;
  actual_latency_hours: number;
  sla_status: string;
  compliance_percentage?: number;
  breach_duration_hours?: number;
}

/**
 * Freshness metric response
 */
export interface FreshnessMetricResponse {
  id: number;
  dataset_name: string;
  ingestion_timestamp: string;
  validation_timestamp?: string;
  dataset_age_hours: number;
  freshness_status: string;
  freshness_threshold_hours: number;
  ingestion_start_time?: string;
  ingestion_end_time?: string;
  ingestion_latency_seconds?: number;
  validation_start_time?: string;
  validation_end_time?: string;
  validation_latency_seconds?: number;
  sla_threshold_hours?: number;
  sla_status?: string;
  dag_id?: string;
  task_id?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Freshness metrics summary
 */
export interface FreshnessMetricsSummary {
  total_datasets: number;
  healthy_count: number;
  warning_count: number;
  critical_count: number;
  sla_compliant_count: number;
  sla_breached_count: number;
  avg_ingestion_latency_seconds?: number;
  avg_validation_latency_seconds?: number;
  avg_dataset_age_hours?: number;
}

/**
 * Time series point
 */
export interface FreshnessTimeSeriesPoint {
  timestamp: string;
  dataset_name: string;
  dataset_age_hours: number;
  freshness_status: string;
  ingestion_latency_seconds?: number;
  validation_latency_seconds?: number;
}

/**
 * Freshness metrics list response
 */
export interface FreshnessMetricsListResponse {
  metrics: FreshnessMetricResponse[];
  total: number;
  summary?: FreshnessMetricsSummary;
}

/**
 * Time series response
 */
export interface FreshnessTimeSeriesResponse {
  data_points: FreshnessTimeSeriesPoint[];
  dataset_name?: string;
  start_time: string;
  end_time: string;
}

/**
 * Freshness filters
 */
export interface FreshnessFilters {
  dataset_name?: string;
  freshness_status?: string;
  sla_status?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

/**
 * Get freshness metrics with filters
 */
export async function getFreshnessMetrics(filters?: FreshnessFilters): Promise<FreshnessMetricsListResponse> {
  const response = await apiRequest<FreshnessMetricsListResponse>({
    method: 'GET',
    url: '/api/v1/freshness/metrics',
    params: filters,
  });
  return response.data;
}

/**
 * Get freshness summary statistics
 */
export async function getFreshnessSummary(filters?: { start_date?: string; end_date?: string }): Promise<FreshnessMetricsSummary> {
  const response = await apiRequest<FreshnessMetricsSummary>({
    method: 'GET',
    url: '/api/v1/freshness/summary',
    params: filters,
  });
  return response.data;
}

/**
 * Get freshness time series data
 */
export async function getFreshnessTimeSeries(filters?: {
  dataset_name?: string;
  start_date?: string;
  end_date?: string;
}): Promise<FreshnessTimeSeriesResponse> {
  const response = await apiRequest<FreshnessTimeSeriesResponse>({
    method: 'GET',
    url: '/api/v1/freshness/time-series',
    params: filters,
  });
  return response.data;
}

/**
 * Get latest freshness metric for a dataset
 */
export async function getLatestFreshnessMetric(datasetName: string): Promise<FreshnessMetricResponse> {
  const response = await apiRequest<FreshnessMetricResponse>({
    method: 'GET',
    url: `/api/v1/freshness/latest/${datasetName}`,
  });
  return response.data;
}

/**
 * Get SLA thresholds configuration
 */
export async function getSLAThresholds(): Promise<Record<string, number>> {
  const response = await apiRequest<{ thresholds: Record<string, number> }>({
    method: 'GET',
    url: '/api/v1/freshness/sla/thresholds',
  });
  return response.data.thresholds;
}

/**
 * Get freshness thresholds configuration
 */
export async function getFreshnessThresholds(): Promise<Record<string, { healthy: number; warning: number }>> {
  const response = await apiRequest<{ thresholds: Record<string, { healthy: number; warning: number }> }>({
    method: 'GET',
    url: '/api/v1/freshness/freshness/thresholds',
  });
  return response.data.thresholds;
}
