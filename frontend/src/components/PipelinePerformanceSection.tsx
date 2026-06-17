import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';

interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  hit_rate: number;
  cached_contracts: number;
  cached_metadata: number;
}

interface RefreshResponse {
  message: string;
  invalidated_contracts: number;
  invalidated_metadata: number;
  stats_reset: boolean;
}

interface PipelinePerformanceSectionProps {
  refreshInterval?: number; // in milliseconds
}

export const PipelinePerformanceSection: React.FC<PipelinePerformanceSectionProps> = ({
  refreshInterval = 10000, // Default: 10 seconds
}) => {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchCacheStats = async () => {
    try {
      const response = await fetch('/api/v1/cache/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStats(data);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cache stats');
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshCache = async () => {
    setRefreshing(true);
    try {
      const response = await fetch('/api/v1/cache/refresh', {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data: RefreshResponse = await response.json();
      
      // Show success message (you can integrate with a toast notification system)
      console.log('Cache refreshed:', data);
      
      // Immediately fetch updated stats
      await fetchCacheStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh cache');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCacheStats();
    const interval = setInterval(fetchCacheStats, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40">
          <Activity className="h-8 w-8 text-gray-400 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-40 text-red-500">
          <p>Error: {error || 'Unable to load cache statistics'}</p>
        </div>
      </div>
    );
  }

  const totalRequests = stats.hits + stats.misses;
  const hitRateColor = stats.hit_rate >= 70 ? 'text-green-600' : stats.hit_rate >= 40 ? 'text-yellow-600' : 'text-red-600';

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Cache Performance</h2>
          <button
            onClick={handleRefreshCache}
            disabled={refreshing}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              refreshing
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>{refreshing ? 'Refreshing...' : 'Refresh Cache'}</span>
          </button>
        </div>
        {lastUpdated && (
          <p className="text-xs text-gray-500 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="p-6">
        {/* Hit Rate Display */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Cache Hit Rate</span>
            <div className="flex items-center space-x-2">
              {stats.hit_rate >= 50 ? (
                <TrendingUp className="h-5 w-5 text-green-500" />
              ) : (
                <TrendingDown className="h-5 w-5 text-red-500" />
              )}
              <span className={`text-3xl font-bold ${hitRateColor}`}>
                {stats.hit_rate.toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                stats.hit_rate >= 70 ? 'bg-green-500' : stats.hit_rate >= 40 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${stats.hit_rate}%` }}
            />
          </div>
        </div>

        {/* Cache Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Cache Hits */}
          <div className="p-4 bg-green-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-green-600 uppercase">Hits</span>
            </div>
            <p className="text-2xl font-bold text-green-700">{stats.hits.toLocaleString()}</p>
            <p className="text-xs text-green-600 mt-1">
              {totalRequests > 0 ? ((stats.hits / totalRequests) * 100).toFixed(1) : 0}% of requests
            </p>
          </div>

          {/* Cache Misses */}
          <div className="p-4 bg-red-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-red-600 uppercase">Misses</span>
            </div>
            <p className="text-2xl font-bold text-red-700">{stats.misses.toLocaleString()}</p>
            <p className="text-xs text-red-600 mt-1">
              {totalRequests > 0 ? ((stats.misses / totalRequests) * 100).toFixed(1) : 0}% of requests
            </p>
          </div>

          {/* Cache Sets */}
          <div className="p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-blue-600 uppercase">Sets</span>
            </div>
            <p className="text-2xl font-bold text-blue-700">{stats.sets.toLocaleString()}</p>
            <p className="text-xs text-blue-600 mt-1">Write operations</p>
          </div>

          {/* Cache Deletes */}
          <div className="p-4 bg-purple-50 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-purple-600 uppercase">Deletes</span>
            </div>
            <p className="text-2xl font-bold text-purple-700">{stats.deletes.toLocaleString()}</p>
            <p className="text-xs text-purple-600 mt-1">Invalidations</p>
          </div>
        </div>

        {/* Total Requests */}
        <div className="mt-4 p-3 bg-gray-100 rounded-lg">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Total Cache Requests</span>
            <span className="text-lg font-bold text-gray-900">{totalRequests.toLocaleString()}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelinePerformanceSection;
