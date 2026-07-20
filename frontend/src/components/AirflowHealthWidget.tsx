/**
 * Airflow Health Widget
 * Displays the overall health status of Airflow components
 */
import React, { useEffect, useState } from 'react';
import { airflowService, AirflowHealth } from '@/services/airflowService';

interface AirflowHealthWidgetProps {
  refreshInterval?: number; // in milliseconds
}

export const AirflowHealthWidget: React.FC<AirflowHealthWidgetProps> = ({
  refreshInterval = 30000,
}) => {
  const [health, setHealth] = useState<AirflowHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const data = await airflowService.getHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch Airflow health');
      if (process.env.NODE_ENV === 'development') {
        console.error('Error fetching Airflow health:', err);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-green-600 bg-green-50';
      case 'unhealthy':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return '✓';
      case 'unhealthy':
        return '✗';
      default:
        return '?';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Airflow Health</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Airflow Health</h3>
        <div className="bg-red-50 border border-red-200 rounded p-4">
          <p className="text-red-600 text-sm">{error || 'Unable to load health data'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Airflow Health</h3>
        <div
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            health.is_healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}
        >
          {health.is_healthy ? 'Healthy' : 'Unhealthy'}
        </div>
      </div>

      <div className="space-y-3">
        {/* Metadatabase Status */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div className="flex items-center space-x-3">
            <span
              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${getStatusColor(
                health.metadatabase
              )}`}
            >
              {getStatusIcon(health.metadatabase)}
            </span>
            <div>
              <p className="text-sm font-medium text-gray-900">Metadatabase</p>
              <p className="text-xs text-gray-500 capitalize">{health.metadatabase}</p>
            </div>
          </div>
        </div>

        {/* Scheduler Status */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
          <div className="flex items-center space-x-3">
            <span
              className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${getStatusColor(
                health.scheduler
              )}`}
            >
              {getStatusIcon(health.scheduler)}
            </span>
            <div>
              <p className="text-sm font-medium text-gray-900">Scheduler</p>
              <p className="text-xs text-gray-500 capitalize">{health.scheduler}</p>
            </div>
          </div>
        </div>

        {/* Triggerer Status (if available) */}
        {health.triggerer && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <div className="flex items-center space-x-3">
              <span
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${getStatusColor(
                  health.triggerer
                )}`}
              >
                {getStatusIcon(health.triggerer)}
              </span>
              <div>
                <p className="text-sm font-medium text-gray-900">Triggerer</p>
                <p className="text-xs text-gray-500 capitalize">{health.triggerer}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AirflowHealthWidget;
