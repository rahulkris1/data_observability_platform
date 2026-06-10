/**
 * Metrics Service
 * Handles API calls for metrics data retrieval and aggregation
 */

import { apiRequest } from './apiClient';
import type { AxiosResponse } from 'axios';

/**
 * Metrics summary response
 */
export interface MetricsSummary {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  filters: {
    dataset_name?: string;
    validation_type?: string;
  };
  validation: {
    total: number;
    success: number;
    failure: number;
    warning: number;
    success_rate: number;
  };
  ingestion: {
    total_executions: number;
    success: number;
    failure: number;
    success_rate: number;
  };
  performance: {
    avg_validation_duration_ms: number;
    avg_ingestion_duration_ms: number;
    avg_api_duration_ms: number;
  };
}

/**
 * Daily aggregation data point
 */
export interface DailyAggregation {
  date: string;
  total: number;
  count: number;
  average: number;
  minimum: number;
  maximum: number;
}

/**
 * Daily aggregation response
 */
export interface DailyAggregationResponse {
  metric_name: string;
  aggregations: DailyAggregation[];
  total_days: number;
}

/**
 * Validation type aggregation
 */
export interface ValidationTypeAggregation {
  validation_type: string;
  total: number;
  count: number;
  average: number;
}

/**
 * Validation type aggregation response
 */
export interface ValidationTypeAggregationResponse {
  metric_name: string;
  aggregations: ValidationTypeAggregation[];
  total_types: number;
}

/**
 * Dataset aggregation
 */
export interface DatasetAggregation {
  dataset_name: string;
  total: number;
  count: number;
  average: number;
}

/**
 * Dataset aggregation response
 */
export interface DatasetAggregationResponse {
  metric_name: string;
  aggregations: DatasetAggregation[];
  total_datasets: number;
}

/**
 * Time series data point
 */
export interface TimeSeriesPoint {
  timestamp: string;
  total: number;
  count: number;
  average: number;
}

/**
 * Time series response
 */
export interface TimeSeriesResponse {
  metric_name: string;
  data_points: TimeSeriesPoint[];
  total_points: number;
}

/**
 * Metrics filter parameters
 */
export interface MetricsFilters {
  start_date?: string;
  end_date?: string;
  dataset_name?: string;
  validation_type?: string;
}

/**
 * Get metrics summary
 */
export const getMetricsSummary = async (
  filters?: MetricsFilters
): Promise<MetricsSummary> => {
  const params = new URLSearchParams();
  
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.dataset_name) params.append('dataset_name', filters.dataset_name);
  if (filters?.validation_type) params.append('validation_type', filters.validation_type);
  
  const response: AxiosResponse<MetricsSummary> = await apiRequest({
    method: 'GET',
    url: `/metrics/summary?${params.toString()}`,
  });
  
  return response.data;
};

/**
 * Get daily aggregated metrics
 */
export const getDailyMetrics = async (
  metricName: string,
  filters?: MetricsFilters
): Promise<DailyAggregationResponse> => {
  const params = new URLSearchParams({ metric_name: metricName });
  
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.dataset_name) params.append('dataset_name', filters.dataset_name);
  if (filters?.validation_type) params.append('validation_type', filters.validation_type);
  
  const response: AxiosResponse<DailyAggregationResponse> = await apiRequest({
    method: 'GET',
    url: `/metrics/daily?${params.toString()}`,
  });
  
  return response.data;
};

/**
 * Get metrics by validation type
 */
export const getMetricsByValidationType = async (
  metricName: string,
  filters?: MetricsFilters
): Promise<ValidationTypeAggregationResponse> => {
  const params = new URLSearchParams({ metric_name: metricName });
  
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.dataset_name) params.append('dataset_name', filters.dataset_name);
  
  const response: AxiosResponse<ValidationTypeAggregationResponse> = await apiRequest({
    method: 'GET',
    url: `/metrics/by-validation-type?${params.toString()}`,
  });
  
  return response.data;
};

/**
 * Get metrics by dataset
 */
export const getMetricsByDataset = async (
  metricName: string,
  filters?: MetricsFilters
): Promise<DatasetAggregationResponse> => {
  const params = new URLSearchParams({ metric_name: metricName });
  
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.validation_type) params.append('validation_type', filters.validation_type);
  
  const response: AxiosResponse<DatasetAggregationResponse> = await apiRequest({
    method: 'GET',
    url: `/metrics/by-dataset?${params.toString()}`,
  });
  
  return response.data;
};

/**
 * Get time series metrics
 */
export const getTimeSeriesMetrics = async (
  metricName: string,
  filters?: MetricsFilters & { interval_hours?: number }
): Promise<TimeSeriesResponse> => {
  const params = new URLSearchParams({ metric_name: metricName });
  
  if (filters?.start_date) params.append('start_date', filters.start_date);
  if (filters?.end_date) params.append('end_date', filters.end_date);
  if (filters?.dataset_name) params.append('dataset_name', filters.dataset_name);
  if (filters?.validation_type) params.append('validation_type', filters.validation_type);
  if (filters?.interval_hours) params.append('interval_hours', filters.interval_hours.toString());
  
  const response: AxiosResponse<TimeSeriesResponse> = await apiRequest({
    method: 'GET',
    url: `/metrics/timeseries?${params.toString()}`,
  });
  
  return response.data;
};
