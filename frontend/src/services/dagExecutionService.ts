/**
 * DAG Execution Service
 * Handles API calls for DAG execution metadata
 */
import apiClient from './apiClient';

export interface DAGExecution {
  id: number;
  dag_id: string;
  dag_run_id: string;
  execution_date: string;
  start_date: string | null;
  end_date: string | null;
  state: string;
  run_type: string | null;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  duration_seconds: number | null;
  conf: Record<string, any> | null;
  task_details: Record<string, any> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface DAGExecutionSummary {
  total_executions: number;
  successful: number;
  failed: number;
  running: number;
  average_duration_seconds: number;
  success_rate: number;
}

export interface DAGExecutionListResponse {
  executions: DAGExecution[];
  total: number;
  limit: number;
  offset: number;
}

export interface DAGExecutionFilters {
  dag_id?: string;
  state?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

class DAGExecutionService {
  private baseURL = '/api/v1/dag-executions';

  /**
   * List DAG executions with optional filters
   */
  async listExecutions(filters?: DAGExecutionFilters): Promise<DAGExecutionListResponse> {
    const response = await apiClient.get<DAGExecutionListResponse>(this.baseURL, {
      params: filters,
    });
    return response.data;
  }

  /**
   * Get summary statistics for DAG executions
   */
  async getExecutionSummary(dagId?: string): Promise<DAGExecutionSummary> {
    const response = await apiClient.get<DAGExecutionSummary>(`${this.baseURL}/summary`, {
      params: dagId ? { dag_id: dagId } : undefined,
    });
    return response.data;
  }

  /**
   * Get details of a specific DAG execution
   */
  async getExecution(dagRunId: string): Promise<DAGExecution> {
    const response = await apiClient.get<DAGExecution>(`${this.baseURL}/${dagRunId}`);
    return response.data;
  }
}

export const dagExecutionService = new DAGExecutionService();
export default dagExecutionService;
