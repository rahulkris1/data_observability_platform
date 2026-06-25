/**
 * Health Score Service
 * Handles API calls for pipeline health score calculation and retrieval
 */

import { apiRequest } from './apiClient';
import type { AxiosResponse } from 'axios';

/**
 * Health score response for a single pipeline
 */
export interface HealthScore {
  id: number;
  pipeline_name: string;
  overall_score: number;
  validation_score: number;
  freshness_score: number;
  latency_score: number;
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  validation_pass_rate?: number;
  freshness_violations?: number;
  avg_latency_seconds?: number;
  total_validations?: number;
  passed_validations?: number;
  failed_validations?: number;
  score_metadata?: Record<string, any>;
}

/**
 * Health score calculation request
 */
export interface HealthScoreCalculateRequest {
  pipeline_name: string;
  lookback_hours?: number;
  async_execution?: boolean;
}

/**
 * Bulk health score calculation request
 */
export interface BulkHealthScoreRequest {
  pipeline_names: string[];
  lookback_hours?: number;
}

/**
 * Async task response
 */
export interface AsyncTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

/**
 * Health score summary response
 */
export interface HealthScoreSummary {
  total_pipelines: number;
  healthy_count: number;
  degraded_count: number;
  unhealthy_count: number;
  average_overall_score: number;
  pipelines: HealthScore[];
}

/**
 * Calculate health score for a pipeline
 */
export const calculateHealthScore = async (
  request: HealthScoreCalculateRequest
): Promise<HealthScore> => {
  const response: AxiosResponse<HealthScore> = await apiRequest<HealthScore>({
    method: 'POST',
    url: '/health/calculate',
    data: request,
  });
  return response.data;
};

/**
 * Get latest health score for a pipeline
 */
export const getHealthScore = async (pipelineName: string): Promise<HealthScore> => {
  const response: AxiosResponse<HealthScore> = await apiRequest<HealthScore>({
    method: 'GET',
    url: `/health/pipeline/${encodeURIComponent(pipelineName)}`,
  });
  return response.data;
};

/**
 * Get health score history for a pipeline
 */
export const getHealthScoreHistory = async (
  pipelineName: string,
  lookbackHours: number = 168
): Promise<HealthScore[]> => {
  const response: AxiosResponse<HealthScore[]> = await apiRequest<HealthScore[]>({
    method: 'GET',
    url: `/health/pipeline/${encodeURIComponent(pipelineName)}/history`,
    params: {
      lookback_hours: lookbackHours,
    },
  });
  return response.data;
};

/**
 * Get all pipeline health scores with summary
 */
export const getAllHealthScores = async (
  limit: number = 100
): Promise<HealthScoreSummary> => {
  const response: AxiosResponse<HealthScoreSummary> = await apiRequest<HealthScoreSummary>({
    method: 'GET',
    url: '/health/all',
    params: {
      limit,
    },
  });
  return response.data;
};

/**
 * Calculate health scores for multiple pipelines
 */
export const calculateBulkHealthScores = async (
  request: BulkHealthScoreRequest
): Promise<AsyncTaskResponse> => {
  const response: AxiosResponse<AsyncTaskResponse> = await apiRequest<AsyncTaskResponse>({
    method: 'POST',
    url: '/health/calculate/bulk',
    data: request,
  });
  return response.data;
};
