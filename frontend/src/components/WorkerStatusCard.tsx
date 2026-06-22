import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle, Server, XCircle } from 'lucide-react';
import { getWorkerStats, WorkerStats } from '../services/taskService';

interface WorkerStatusCardProps {
  refreshInterval?: number; // in milliseconds
}

export const WorkerStatusCard: React.FC<WorkerStatusCardProps> = ({
  refreshInterval = 5000, // Default: 5 seconds
}) => {
  const [workerStats, setWorkerStats] = useState<WorkerStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWorkerStats = async () => {
    try {
      const data = await getWorkerStats();
      setWorkerStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch worker stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkerStats();
    const interval = setInterval(fetchWorkerStats, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-gray-500 animate-spin" />
          <span className="text-sm text-gray-600">Loading worker stats...</span>
        </div>
      </div>
    );
  }

  if (error || !workerStats) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-sm text-red-700">Failed to load worker stats</span>
        </div>
      </div>
    );
  }

  const isHealthy = workerStats.total_workers > 0;

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Server className={`h-6 w-6 ${isHealthy ? 'text-green-500' : 'text-red-500'}`} />
            <h2 className="text-lg font-semibold text-gray-900">Worker Status</h2>
          </div>
          {isHealthy ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-4">
        {/* Worker Count */}
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Active Workers</span>
            <span className={`text-2xl font-bold ${isHealthy ? 'text-green-600' : 'text-red-600'}`}>
              {workerStats.total_workers}
            </span>
          </div>
        </div>

        {/* Status Message */}
        <div className={`px-4 py-3 rounded-md ${isHealthy ? 'bg-green-50' : 'bg-red-50'}`}>
          <p className={`text-sm ${isHealthy ? 'text-green-700' : 'text-red-700'}`}>
            {isHealthy
              ? `${workerStats.total_workers} worker${workerStats.total_workers > 1 ? 's' : ''} available to process tasks`
              : 'No workers available - tasks will queue but not execute'}
          </p>
        </div>

        {/* Worker Details */}
        {workerStats.total_workers > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Worker Details</h3>
            <div className="space-y-2">
              {workerStats.workers.map((worker, index) => (
                <div key={index} className="bg-gray-50 rounded-md p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-900">{worker.name}</span>
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {worker.active_tasks} active
                    </span>
                  </div>
                  {worker.active_tasks > 0 && (
                    <div className="mt-2 space-y-1">
                      {worker.tasks.slice(0, 3).map((task, taskIndex) => (
                        <div key={taskIndex} className="text-xs text-gray-600 pl-2 border-l-2 border-blue-300">
                          {task.task_name}
                        </div>
                      ))}
                      {worker.tasks.length > 3 && (
                        <div className="text-xs text-gray-500 pl-2">
                          +{worker.tasks.length - 3} more...
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="mt-4 text-xs text-gray-500 text-right">
          Last updated: {new Date(workerStats.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default WorkerStatusCard;
