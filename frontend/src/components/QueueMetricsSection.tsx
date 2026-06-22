import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, Clock, List, Play } from 'lucide-react';
import { getQueueMetrics, QueueMetrics } from '../services/taskService';

interface QueueMetricsSectionProps {
  refreshInterval?: number; // in milliseconds
}

export const QueueMetricsSection: React.FC<QueueMetricsSectionProps> = ({
  refreshInterval = 5000, // Default: 5 seconds
}) => {
  const [metrics, setMetrics] = useState<QueueMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueueMetrics = async () => {
    try {
      const data = await getQueueMetrics();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueMetrics();
    const interval = setInterval(fetchQueueMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-gray-500 animate-spin" />
          <span className="text-sm text-gray-600">Loading queue metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-5 w-5 text-red-500" />
          <span className="text-sm text-red-700">Failed to load queue metrics</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <List className="h-6 w-6 text-blue-500" />
          <h2 className="text-lg font-semibold text-gray-900">Queue Metrics</h2>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="px-6 py-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Queued Tasks */}
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-900">Queued</span>
            </div>
            <div className="text-3xl font-bold text-yellow-700">{metrics.queued_tasks}</div>
            <div className="text-xs text-yellow-600 mt-1">Waiting to start</div>
          </div>

          {/* Running Tasks */}
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Play className="h-5 w-5 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">Running</span>
            </div>
            <div className="text-3xl font-bold text-blue-700">{metrics.running_tasks}</div>
            <div className="text-xs text-blue-600 mt-1">Currently executing</div>
          </div>

          {/* Scheduled Tasks */}
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Activity className="h-5 w-5 text-purple-600" />
              <span className="text-sm font-medium text-purple-900">Scheduled</span>
            </div>
            <div className="text-3xl font-bold text-purple-700">{metrics.scheduled_tasks}</div>
            <div className="text-xs text-purple-600 mt-1">Scheduled for later</div>
          </div>

          {/* Total Pending */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <List className="h-5 w-5 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Total</span>
            </div>
            <div className="text-3xl font-bold text-gray-700">{metrics.total_pending}</div>
            <div className="text-xs text-gray-600 mt-1">All pending tasks</div>
          </div>
        </div>

        {/* Summary */}
        <div className="mt-4 p-4 bg-gray-50 rounded-md">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              {metrics.total_pending === 0 ? (
                <span className="text-green-600 font-medium">✓ All tasks processed</span>
              ) : (
                <>
                  <span className="font-medium">{metrics.total_pending} task{metrics.total_pending > 1 ? 's' : ''}</span>
                  {' '}in queue or processing
                </>
              )}
            </div>
            <div className="text-xs text-gray-500">
              Updated: {new Date(metrics.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueueMetricsSection;
