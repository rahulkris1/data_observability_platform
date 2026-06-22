import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle, Clock, RefreshCw, XCircle } from 'lucide-react';
import { getActiveTaskSummary, ActiveTaskSummary, getTaskStatus, TaskStatus } from '../services/taskService';

interface TaskStatusTableProps {
  refreshInterval?: number; // in milliseconds
}

export const TaskStatusTable: React.FC<TaskStatusTableProps> = ({
  refreshInterval = 5000, // Default: 5 seconds
}) => {
  const [summary, setSummary] = useState<ActiveTaskSummary | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<{ [key: string]: TaskStatus[] }>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedType, setExpandedType] = useState<string | null>(null);

  const fetchTaskSummary = async () => {
    try {
      const data = await getActiveTaskSummary();
      setSummary(data);
      setError(null);

      // Fetch details for expanded task type
      if (expandedType) {
        const taskType = data.tasks_by_type.find(t => t.task_name === expandedType);
        if (taskType) {
          await fetchTaskDetails(taskType.task_name, taskType.task_ids);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch task summary');
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskDetails = async (taskType: string, taskIds: string[]) => {
    try {
      const taskDetails = await Promise.all(
        taskIds.map(id => getTaskStatus(id))
      );
      setSelectedTasks(prev => ({
        ...prev,
        [taskType]: taskDetails,
      }));
    } catch (err) {
      console.error('Failed to fetch task details:', err);
    }
  };

  const handleToggleExpand = async (taskType: string, taskIds: string[]) => {
    if (expandedType === taskType) {
      setExpandedType(null);
    } else {
      setExpandedType(taskType);
      if (!selectedTasks[taskType]) {
        await fetchTaskDetails(taskType, taskIds);
      }
    }
  };

  useEffect(() => {
    fetchTaskSummary();
    const interval = setInterval(fetchTaskSummary, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval, expandedType]);

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'SUCCESS':
      case 'COMPLETED':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'FAILURE':
      case 'FAILED':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'PENDING':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'STARTED':
      case 'RUNNING':
        return <Activity className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const statusUpper = status.toUpperCase();
    let colorClass = 'bg-gray-100 text-gray-800';

    if (statusUpper === 'SUCCESS' || statusUpper === 'COMPLETED') {
      colorClass = 'bg-green-100 text-green-800';
    } else if (statusUpper === 'FAILURE' || statusUpper === 'FAILED') {
      colorClass = 'bg-red-100 text-red-800';
    } else if (statusUpper === 'PENDING') {
      colorClass = 'bg-yellow-100 text-yellow-800';
    } else if (statusUpper === 'STARTED' || statusUpper === 'RUNNING') {
      colorClass = 'bg-blue-100 text-blue-800';
    }

    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClass}`}>
        {status}
      </span>
    );
  };

  const formatExecutionTime = (result: any) => {
    if (result && result.execution_time) {
      return `${result.execution_time.toFixed(2)}s`;
    }
    return 'N/A';
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-gray-500 animate-spin" />
          <span className="text-sm text-gray-600">Loading task status...</span>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-sm text-red-700">Failed to load task status</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="h-6 w-6 text-indigo-500" />
            <h2 className="text-lg font-semibold text-gray-900">Active Tasks</h2>
          </div>
          <button
            onClick={() => fetchTaskSummary()}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-4">
        {summary.total_active_tasks === 0 ? (
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
            <p className="text-gray-600">No active tasks</p>
            <p className="text-sm text-gray-500 mt-1">All tasks have been completed</p>
          </div>
        ) : (
          <div className="space-y-2">
            {summary.tasks_by_type.map((taskType, index) => (
              <div key={index} className="border border-gray-200 rounded-lg overflow-hidden">
                {/* Task Type Header */}
                <button
                  onClick={() => handleToggleExpand(taskType.task_name, taskType.task_ids)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-gray-900">{taskType.task_name}</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                      {taskType.count} task{taskType.count > 1 ? 's' : ''}
                    </span>
                  </div>
                  <span className="text-gray-400">
                    {expandedType === taskType.task_name ? '▼' : '▶'}
                  </span>
                </button>

                {/* Task Details */}
                {expandedType === taskType.task_name && (
                  <div className="bg-white">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Task ID
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Execution Time
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {selectedTasks[taskType.task_name]?.map((task, taskIndex) => (
                          <tr key={taskIndex} className="hover:bg-gray-50">
                            <td className="px-4 py-3 text-sm font-mono text-gray-600">
                              {task.task_id.substring(0, 8)}...
                            </td>
                            <td className="px-4 py-3 text-sm">
                              <div className="flex items-center space-x-2">
                                {getStatusIcon(task.status)}
                                {getStatusBadge(task.status)}
                              </div>
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-600">
                              {formatExecutionTime(task.result)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className="mt-4 text-xs text-gray-500 text-right">
          Last updated: {new Date(summary.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default TaskStatusTable;
