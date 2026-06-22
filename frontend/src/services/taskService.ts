/**
 * Task Queue API service for frontend
 * Provides methods to interact with Celery task monitoring endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface TaskStatus {
  task_id: string;
  status: string;
  ready: boolean;
  successful?: boolean;
  result?: any;
  error?: string;
  info?: any;
}

export interface WorkerInfo {
  name: string;
  active_tasks: number;
  tasks: Array<{
    task_id: string;
    task_name: string;
    args: string;
    kwargs: string;
  }>;
  registered_tasks?: string[];
  stats?: any;
}

export interface WorkerStats {
  total_workers: number;
  workers: WorkerInfo[];
  timestamp: string;
}

export interface QueueMetrics {
  queued_tasks: number;
  running_tasks: number;
  scheduled_tasks: number;
  total_pending: number;
  timestamp: string;
}

export interface TaskSubmitResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskHealthCheck {
  healthy: boolean;
  workers_available: number;
  pending_tasks: number;
  status: string;
  message: string;
}

export interface ActiveTaskSummary {
  total_active_tasks: number;
  tasks_by_type: Array<{
    task_name: string;
    count: number;
    task_ids: string[];
  }>;
  timestamp: string;
}

/**
 * Get worker statistics
 */
export async function getWorkerStats(): Promise<WorkerStats> {
  const response = await fetch(`${API_BASE_URL}/tasks/workers/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch worker stats: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get queue metrics
 */
export async function getQueueMetrics(): Promise<QueueMetrics> {
  const response = await fetch(`${API_BASE_URL}/tasks/queue/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch queue metrics: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get task status by ID
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatus> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch task status: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get task result by ID
 */
export async function getTaskResult(taskId: string, timeout?: number): Promise<any> {
  const url = new URL(`${API_BASE_URL}/tasks/${taskId}/result`);
  if (timeout !== undefined) {
    url.searchParams.append('timeout', timeout.toString());
  }
  
  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error(`Failed to fetch task result: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Cancel a task
 */
export async function cancelTask(taskId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to cancel task: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get active task summary
 */
export async function getActiveTaskSummary(): Promise<ActiveTaskSummary> {
  const response = await fetch(`${API_BASE_URL}/tasks/active/summary`);
  if (!response.ok) {
    throw new Error(`Failed to fetch active task summary: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get task system health
 */
export async function getTaskSystemHealth(): Promise<TaskHealthCheck> {
  const response = await fetch(`${API_BASE_URL}/tasks/health`);
  if (!response.ok) {
    throw new Error(`Failed to fetch task system health: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Submit a validation task
 */
export async function submitValidationTask(
  contractName: string,
  datasetColumns: any[],
  datasetName: string
): Promise<TaskSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/tasks/validate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      contract_name: contractName,
      dataset_columns: datasetColumns,
      dataset_name: datasetName,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to submit validation task: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Submit a profiling task
 */
export async function submitProfilingTask(
  datasetPath: string,
  datasetName: string,
  columns?: string[]
): Promise<TaskSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/tasks/profile`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      dataset_path: datasetPath,
      dataset_name: datasetName,
      columns,
    }),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to submit profiling task: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get bulk task status
 */
export async function getBulkTaskStatus(taskIds: string[]): Promise<{ tasks: TaskStatus[] }> {
  const response = await fetch(`${API_BASE_URL}/tasks/bulk/status`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(taskIds),
  });
  
  if (!response.ok) {
    throw new Error(`Failed to fetch bulk task status: ${response.statusText}`);
  }
  return response.json();
}
