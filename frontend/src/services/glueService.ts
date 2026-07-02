/**
 * Glue Service API Client
 * 
 * Provides methods for interacting with AWS Glue job management APIs.
 */

import { apiClient } from './apiClient';

export interface GlueJobRun {
  job_run_id: string;
  job_name: string;
  state: string;
  started_on?: string;
  completed_on?: string;
  execution_time: number;
  error_message?: string;
}

export interface ExecutionEnvironment {
  execution_mode: string;
  is_glue_enabled: boolean;
  glue_job_name: string;
  glue_available: boolean;
  aws_region: string;
  storage_provider: string;
}

export interface GlueConfigValidation {
  is_valid: boolean;
  issues: string[];
  warnings: string[];
  execution_mode: string;
}

export interface GlueJobRunRequest {
  job_name?: string;
  arguments?: Record<string, string>;
}

export interface GlueJobRunResponse {
  job_run_id: string;
  job_name: string;
  status: string;
}

export interface GlueJobHistoryResponse {
  job_runs: GlueJobRun[];
  count: number;
}

/**
 * Get execution environment information
 */
export async function getExecutionEnvironment(): Promise<ExecutionEnvironment> {
  const response = await apiClient.get('/api/v1/glue/environment');
  return response.data;
}

/**
 * Validate Glue configuration
 */
export async function validateGlueConfiguration(): Promise<GlueConfigValidation> {
  const response = await apiClient.get('/api/v1/glue/validate-config');
  return response.data;
}

/**
 * Start a Glue job run
 */
export async function startGlueJobRun(request: GlueJobRunRequest = {}): Promise<GlueJobRunResponse> {
  const response = await apiClient.post('/api/v1/glue/jobs/run', request);
  return response.data;
}

/**
 * Get status of a specific Glue job run
 */
export async function getGlueJobStatus(jobRunId: string, jobName?: string): Promise<GlueJobRun> {
  const params = jobName ? { job_name: jobName } : {};
  const response = await apiClient.get(`/api/v1/glue/jobs/${jobRunId}/status`, { params });
  return response.data;
}

/**
 * Get history of Glue job runs
 */
export async function getGlueJobHistory(jobName?: string, maxResults: number = 10): Promise<GlueJobHistoryResponse> {
  const params: Record<string, any> = { max_results: maxResults };
  if (jobName) {
    params.job_name = jobName;
  }
  const response = await apiClient.get('/api/v1/glue/jobs/history', { params });
  return response.data;
}

/**
 * Stop a running Glue job
 */
export async function stopGlueJobRun(jobRunId: string, jobName?: string): Promise<{ message: string; success: boolean }> {
  const params = jobName ? { job_name: jobName } : {};
  const response = await apiClient.post(`/api/v1/glue/jobs/${jobRunId}/stop`, null, { params });
  return response.data;
}

/**
 * Check Glue service health
 */
export async function checkGlueHealth(): Promise<{
  service: string;
  available: boolean;
  configuration_valid: boolean;
  execution_mode: string;
  issues: string[];
  warnings: string[];
}> {
  const response = await apiClient.get('/api/v1/glue/health');
  return response.data;
}

export const glueService = {
  getExecutionEnvironment,
  validateGlueConfiguration,
  startGlueJobRun,
  getGlueJobStatus,
  getGlueJobHistory,
  stopGlueJobRun,
  checkGlueHealth,
};
