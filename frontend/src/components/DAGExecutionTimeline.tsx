/**
 * DAG Execution Timeline Component
 * Displays task execution sequence and status
 */
import React from 'react';
import { DAGExecution } from '@/services/dagExecutionService';

interface DAGExecutionTimelineProps {
  execution: DAGExecution | null;
}

interface TaskInfo {
  name: string;
  status: string;
  order: number;
}

const DAGExecutionTimeline: React.FC<DAGExecutionTimelineProps> = ({ execution }) => {
  if (!execution) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Select a DAG execution to view task timeline</p>
      </div>
    );
  }

  // Extract task information from task_details
  const getTasks = (): TaskInfo[] => {
    if (!execution.task_details) {
      // Default tasks for data_quality_pipeline
      return [
        { name: 'ingest_dataset', status: 'success', order: 1 },
        { name: 'validate_dataset', status: 'success', order: 2 },
        { name: 'audit_logging', status: 'success', order: 3 },
        { name: 'pipeline_completion', status: 'success', order: 4 },
      ];
    }

    return Object.entries(execution.task_details).map(([name, details]: [string, any], index) => ({
      name,
      status: details.status || 'unknown',
      order: index + 1,
    }));
  };

  const tasks = getTasks();

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'success':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'running':
        return 'bg-blue-500 animate-pulse';
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'success':
        return '✓';
      case 'failed':
        return '✗';
      case 'running':
        return '↻';
      default:
        return '•';
    }
  };

  const formatTaskName = (name: string): string => {
    return name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getTaskDuration = (taskName: string): string => {
    if (!execution.task_details || !execution.task_details[taskName]) {
      return '-';
    }

    const taskDetail = execution.task_details[taskName];
    if (taskDetail.duration_seconds) {
      return `${taskDetail.duration_seconds.toFixed(1)}s`;
    }

    return '-';
  };

  const getTaskMetrics = (taskName: string): string | null => {
    if (!execution.task_details || !execution.task_details[taskName]) {
      return null;
    }

    const taskDetail = execution.task_details[taskName];
    
    if (taskName === 'ingestion' && taskDetail.records) {
      return `${taskDetail.records} records`;
    }
    
    if (taskName === 'validation') {
      if (taskDetail.passed !== undefined && taskDetail.failed !== undefined) {
        return `${taskDetail.passed} passed, ${taskDetail.failed} failed`;
      }
      if (taskDetail.overall_status) {
        return `Status: ${taskDetail.overall_status}`;
      }
    }

    return null;
  };

  return (
    <div className="space-y-6">
      {/* Execution Header */}
      <div className="border-b border-gray-200 pb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {execution.dag_id}
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Run: {execution.dag_run_id.split('__').pop() || execution.dag_run_id}
        </p>
      </div>

      {/* Task Timeline */}
      <div className="relative">
        {tasks.map((task, index) => (
          <div key={task.name} className="relative pb-8 last:pb-0">
            {/* Connecting line */}
            {index < tasks.length - 1 && (
              <div
                className="absolute left-4 top-8 bottom-0 w-0.5 bg-gray-200"
                aria-hidden="true"
              />
            )}

            <div className="relative flex items-start space-x-4">
              {/* Status indicator */}
              <div className="relative flex items-center justify-center">
                <div
                  className={`h-8 w-8 rounded-full ${getStatusColor(
                    task.status
                  )} flex items-center justify-center text-white font-semibold text-sm shadow-lg`}
                >
                  {getStatusIcon(task.status)}
                </div>
              </div>

              {/* Task details */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {formatTaskName(task.name)}
                    </p>
                    <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                      <span className="capitalize">{task.status}</span>
                      {getTaskDuration(task.name) !== '-' && (
                        <>
                          <span>•</span>
                          <span>{getTaskDuration(task.name)}</span>
                        </>
                      )}
                    </div>
                    {getTaskMetrics(task.name) && (
                      <p className="mt-1 text-xs text-gray-600">
                        {getTaskMetrics(task.name)}
                      </p>
                    )}
                  </div>

                  {/* Task order badge */}
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                    {task.order}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Execution Summary */}
      {execution.duration_seconds && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">Total Duration</dt>
              <dd className="mt-1 font-semibold text-gray-900">
                {execution.duration_seconds < 60
                  ? `${execution.duration_seconds.toFixed(1)}s`
                  : `${(execution.duration_seconds / 60).toFixed(1)}m`}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">Tasks Completed</dt>
              <dd className="mt-1 font-semibold text-gray-900">
                {execution.completed_tasks} / {execution.total_tasks}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Error message if present */}
      {execution.error_message && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm font-medium text-red-800">Error</p>
          <p className="mt-1 text-sm text-red-700">{execution.error_message}</p>
        </div>
      )}
    </div>
  );
};

export default DAGExecutionTimeline;
