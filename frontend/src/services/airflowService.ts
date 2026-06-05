/**
 * Airflow Service
 * Handles API calls to Airflow endpoints
 */
import apiClient from './apiClient';
import type { ApiResponse } from './types';

// Airflow-specific types
export interface AirflowHealth {
  metadatabase: string;
  scheduler: string;
  triggerer?: string | null;
  is_healthy: boolean;
}

export interface SchedulerHealth {
  status: string;
  latest_heartbeat: string | null;
  is_healthy: boolean;
  error?: string;
}

export interface AirflowStatistics {
  total_dags: number;
  scheduler_healthy: boolean;
  database_healthy: boolean;
  version: string | null;
  error?: string;
}

export interface DAGInfo {
  dag_id: string;
  is_paused: boolean;
  is_active: boolean;
  last_parsed_time: string | null;
  tags: string[];
}

export interface DAGRun {
  dag_run_id: string;
  dag_id: string;
  execution_date: string;
  start_date: string | null;
  end_date: string | null;
  state: string;
  external_trigger: boolean;
}

export interface PipelineSummary {
  total_pipelines: number;
  active_pipelines: number;
  paused_pipelines: number;
  recent_runs: {
    success: number;
    failed: number;
    running: number;
    total: number;
  };
}

class AirflowService {
  private baseURL = '/airflow';

  /**
   * Get Airflow health status
   */
  async getHealth(): Promise<AirflowHealth> {
    const response = await apiClient.get<AirflowHealth>(`${this.baseURL}/health`);
    return response.data;
  }

  /**
   * Get Airflow version
   */
  async getVersion(): Promise<{ version: string }> {
    const response = await apiClient.get<{ version: string }>(`${this.baseURL}/version`);
    return response.data;
  }

  /**
   * Get scheduler health
   */
  async getSchedulerHealth(): Promise<SchedulerHealth> {
    const response = await apiClient.get<SchedulerHealth>(`${this.baseURL}/scheduler/health`);
    return response.data;
  }

  /**
   * Get Airflow statistics
   */
  async getStatistics(): Promise<AirflowStatistics> {
    const response = await apiClient.get<AirflowStatistics>(`${this.baseURL}/statistics`);
    return response.data;
  }

  /**
   * List all DAGs
   */
  async listDAGs(params?: { limit?: number; offset?: number }): Promise<DAGInfo[]> {
    const response = await apiClient.get<DAGInfo[]>(`${this.baseURL}/dags`, { params });
    return response.data;
  }

  /**
   * Get specific DAG
   */
  async getDAG(dagId: string): Promise<DAGInfo> {
    const response = await apiClient.get<DAGInfo>(`${this.baseURL}/dags/${dagId}`);
    return response.data;
  }

  /**
   * List DAG runs
   */
  async listDAGRuns(
    dagId: string,
    params?: { limit?: number; offset?: number; state?: string }
  ): Promise<DAGRun[]> {
    const response = await apiClient.get<DAGRun[]>(`${this.baseURL}/dags/${dagId}/runs`, { params });
    return response.data;
  }

  /**
   * Trigger a DAG
   */
  async triggerDAG(dagId: string, conf?: any): Promise<DAGRun> {
    const response = await apiClient.post<DAGRun>(`${this.baseURL}/dags/${dagId}/trigger`, { conf });
    return response.data;
  }

  /**
   * Pause a DAG
   */
  async pauseDAG(dagId: string): Promise<{ message: string }> {
    const response = await apiClient.patch<{ message: string }>(`${this.baseURL}/dags/${dagId}/pause`);
    return response.data;
  }

  /**
   * Unpause a DAG
   */
  async unpauseDAG(dagId: string): Promise<{ message: string }> {
    const response = await apiClient.patch<{ message: string }>(`${this.baseURL}/dags/${dagId}/unpause`);
    return response.data;
  }

  /**
   * Get pipeline summary
   */
  async getPipelineSummary(): Promise<PipelineSummary> {
    const response = await apiClient.get<PipelineSummary>(`${this.baseURL}/pipelines/summary`);
    return response.data;
  }
}

export const airflowService = new AirflowService();
export default airflowService;
