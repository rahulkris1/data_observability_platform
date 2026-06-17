import React, { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface CacheStatus {
  connected: boolean;
  redis_version?: string;
  used_memory?: string;
  connected_clients?: number;
  uptime_days?: number;
  error?: string;
}

interface CacheStatusIndicatorProps {
  refreshInterval?: number; // in milliseconds
}

export const CacheStatusIndicator: React.FC<CacheStatusIndicatorProps> = ({
  refreshInterval = 30000, // Default: 30 seconds
}) => {
  const [status, setStatus] = useState<CacheStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCacheStatus = async () => {
    try {
      const response = await fetch('/api/v1/cache/status');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cache status');
      setStatus({ connected: false, error: 'Connection failed' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCacheStatus();
    const interval = setInterval(fetchCacheStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg">
        <Activity className="h-4 w-4 text-gray-500 animate-spin" />
        <span className="text-sm text-gray-600">Checking cache...</span>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 rounded-lg">
        <AlertCircle className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-700">Cache status unavailable</span>
      </div>
    );
  }

  if (!status.connected) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-red-50 rounded-lg">
        <XCircle className="h-4 w-4 text-red-500" />
        <div className="flex flex-col">
          <span className="text-sm font-medium text-red-700">Redis Disconnected</span>
          {status.error && (
            <span className="text-xs text-red-600">{status.error}</span>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-3 px-3 py-2 bg-green-50 rounded-lg">
      <CheckCircle className="h-4 w-4 text-green-500" />
      <div className="flex flex-col">
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-green-700">Redis Connected</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
            v{status.redis_version}
          </span>
        </div>
        <div className="flex items-center space-x-3 text-xs text-gray-600 mt-1">
          <span>Memory: {status.used_memory}</span>
          <span>•</span>
          <span>Clients: {status.connected_clients}</span>
          <span>•</span>
          <span>Uptime: {status.uptime_days}d</span>
        </div>
      </div>
    </div>
  );
};

export default CacheStatusIndicator;
