/**
 * Profiling Service
 * Handles API calls for dataset profiling
 */

import { apiRequest } from './apiClient';
import type { AxiosResponse } from 'axios';

/**
 * Profiling execution request
 */
export interface ProfilingExecutionRequest {
  dataset_name: string;
  bucket_name: string;
  object_name: string;
  profiled_by?: string;
}

/**
 * Profiling execution response
 */
export interface ProfilingExecutionResponse {
  task_id: string;
  dataset_name: string;
  status: string;
  message: string;
}

/**
 * Task status response
 */
export interface TaskStatusResponse {
  task_id: string;
  status: string;
  result?: {
    status: string;
    profiling_id: number;
    dataset_name: string;
    row_count: number;
    column_count: number;
    execution_time_seconds: number;
    profiled_at: string;
  };
  error?: string;
}

/**
 * Column statistics
 */
export interface ColumnStatistics {
  column_name: string;
  data_type: string;
  null_count: number;
  null_percentage: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
}

/**
 * Column distribution
 */
export interface ColumnDistribution {
  column_name: string;
  unique_count: number;
  top_values: Array<{
    value: string;
    count: number;
    percentage: number;
  }>;
}

/**
 * Profiling result response
 */
export interface ProfilingResult {
  id: number;
  dataset_name: string;
  status: string;
  row_count: number | null;
  column_count: number | null;
  execution_time_ms: number | null;
  column_statistics: Record<string, ColumnStatistics> | null;
  column_distributions: Record<string, ColumnDistribution> | null;
  error_message: string | null;
  profiled_by: string;
  created_at: string;
}

/**
 * Profiling history response
 */
export interface ProfilingHistoryResponse {
  total: number;
  results: ProfilingResult[];
}

/**
 * Execute dataset profiling
 */
export async function executeProfileing(
  request: ProfilingExecutionRequest
): Promise<ProfilingExecutionResponse> {
  const response: AxiosResponse<ProfilingExecutionResponse> = await apiRequest({
    method: 'POST',
    url: '/api/v1/profiling/execute',
    data: request,
  });
  return response.data;
}

/**
 * Get profiling task status
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  const response: AxiosResponse<TaskStatusResponse> = await apiRequest({
    method: 'GET',
    url: `/api/v1/profiling/task/${taskId}`,
  });
  return response.data;
}

/**
 * Get latest profiling result for a dataset
 */
export async function getLatestProfiling(datasetName: string): Promise<ProfilingResult> {
  const response: AxiosResponse<ProfilingResult> = await apiRequest({
    method: 'GET',
    url: `/api/v1/profiling/results/latest/${datasetName}`,
  });
  return response.data;
}

/**
 * Get profiling result by ID
 */
export async function getProfilingById(profilingId: number): Promise<ProfilingResult> {
  const response: AxiosResponse<ProfilingResult> = await apiRequest({
    method: 'GET',
    url: `/api/v1/profiling/results/${profilingId}`,
  });
  return response.data;
}

/**
 * Get profiling history
 */
export async function getProfilingHistory(
  datasetName?: string,
  limit: number = 100
): Promise<ProfilingHistoryResponse> {
  const params = new URLSearchParams();
  if (datasetName) {
    params.append('dataset_name', datasetName);
  }
  params.append('limit', limit.toString());

  const response: AxiosResponse<ProfilingHistoryResponse> = await apiRequest({
    method: 'GET',
    url: `/api/v1/profiling/history?${params.toString()}`,
  });
  return response.data;
}
