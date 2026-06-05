/**
 * Scheduler Status Indicator
 * Displays detailed scheduler health and heartbeat information
 */
import React, { useEffect, useState } from 'react';
import { airflowService, SchedulerHealth } from '@/services/airflowService';

interface SchedulerStatusIndicatorProps {
  refreshInterval?: number; // in milliseconds
  compact?: boolean;
}

export const SchedulerStatusIndicator: React.FC<SchedulerStatusIndicatorProps> = ({
  refreshInterval = 10000,
  compact = false,
}) => {
  const [health, setHealth] = useState<SchedulerHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      const data = await airflowService.getSchedulerHealth();
      setHealth(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch scheduler health');
      console.error('Error fetching scheduler health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatHeartbeat = (heartbeat: string | null): string => {
    if (!heartbeat) return 'Never';
    
    try {
      const date = new Date(heartbeat);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffSeconds = Math.floor(diffMs / 1000);
      const diffMinutes = Math.floor(diffSeconds / 60);
      
      if (diffSeconds < 60) {
        return `${diffSeconds}s ago`;
      } else if (diffMinutes < 60) {
        return `${diffMinutes}m ago`;
      } else {
        return date.toLocaleTimeString();
      }
    } catch {
      return heartbeat;
    }
  };

  const getStatusStyle = (isHealthy: boolean) => {
    return isHealthy
      ? 'bg-green-100 text-green-800 border-green-300'
      : 'bg-red-100 text-red-800 border-red-300';
  };

  const getIndicatorColor = (isHealthy: boolean) => {
    return isHealthy ? 'bg-green-500' : 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 bg-gray-400 rounded-full animate-pulse"></div>
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="flex items-center space-x-2">
        <div className="w-3 h-3 bg-red-500 rounded-full"></div>
        <span className="text-sm text-red-600">Scheduler Unavailable</span>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${getIndicatorColor(health.is_healthy)} ${
          health.is_healthy ? 'animate-pulse' : ''
        }`}></div>
        <span className="text-sm font-medium">
          Scheduler: <span className="capitalize">{health.status}</span>
        </span>
      </div>
    );
  }

  return (
    <div className={`border rounded-lg p-4 ${getStatusStyle(health.is_healthy)}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`w-4 h-4 rounded-full ${getIndicatorColor(health.is_healthy)} ${
            health.is_healthy ? 'animate-pulse' : ''
          }`}></div>
          <h4 className="font-semibold text-lg">Scheduler Status</h4>
        </div>
        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase">
          {health.status}
        </span>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="font-medium">Last Heartbeat:</span>
          <span>{formatHeartbeat(health.latest_heartbeat)}</span>
        </div>
        
        {health.error && (
          <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs">
            <span className="font-medium">Error:</span> {health.error}
          </div>
        )}
      </div>
    </div>
  );
};

export default SchedulerStatusIndicator;
