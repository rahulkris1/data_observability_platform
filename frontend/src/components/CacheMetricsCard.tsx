import React, { useEffect, useState } from 'react';
import { Database, FileText, Activity, AlertCircle } from 'lucide-react';

interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  hit_rate: number;
  cached_contracts: number;
  cached_metadata: number;
}

interface CacheMetricsCardProps {
  refreshInterval?: number; // in milliseconds
}

export const CacheMetricsCard: React.FC<CacheMetricsCardProps> = ({
  refreshInterval = 15000, // Default: 15 seconds
}) => {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCacheStats = async () => {
    try {
      const response = await fetch('/api/v1/cache/stats');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cache stats');
    } finally {
      setLoading(false);
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
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-600">Cache Metrics</h3>
          <Activity className="h-5 w-5 text-gray-400 animate-spin" />
        </div>
        <div className="space-y-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 text-red-500">
          <AlertCircle className="h-5 w-5" />
          <p className="text-sm">Unable to load cache metrics</p>
        </div>
      </div>
    );
  }

  const totalCached = stats.cached_contracts + stats.cached_metadata;

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Cache Metrics</h3>
      </div>
      
      <div className="p-6">
        {/* Cached Contracts */}
        <div className="mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 p-3 bg-blue-100 rounded-lg">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Cached Contracts</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {stats.cached_contracts.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all duration-500"
                style={{
                  width: totalCached > 0 ? `${(stats.cached_contracts / totalCached) * 100}%` : '0%',
                }}
              />
            </div>
            <span className="ml-3 text-xs text-gray-500 font-medium">
              {totalCached > 0 ? ((stats.cached_contracts / totalCached) * 100).toFixed(0) : 0}%
            </span>
          </div>
        </div>

        {/* Cached Metadata */}
        <div className="mb-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0 p-3 bg-purple-100 rounded-lg">
                <Database className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">Cached Metadata</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {stats.cached_metadata.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-500"
                style={{
                  width: totalCached > 0 ? `${(stats.cached_metadata / totalCached) * 100}%` : '0%',
                }}
              />
            </div>
            <span className="ml-3 text-xs text-gray-500 font-medium">
              {totalCached > 0 ? ((stats.cached_metadata / totalCached) * 100).toFixed(0) : 0}%
            </span>
          </div>
        </div>

        {/* Total Summary */}
        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-600">Total Cached Items</span>
            <span className="text-xl font-bold text-gray-900">{totalCached.toLocaleString()}</span>
          </div>
          
          {/* Additional Metrics */}
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Cache Operations</p>
              <p className="text-lg font-semibold text-gray-900 mt-1">{stats.sets.toLocaleString()}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 uppercase">Invalidations</p>
              <p className="text-lg font-semibold text-gray-900 mt-1">{stats.deletes.toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Performance Indicator */}
        {stats.hit_rate >= 0 && (
          <div className="mt-4 p-3 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-700">Efficiency</span>
              <span className={`text-sm font-bold ${
                stats.hit_rate >= 70 ? 'text-green-600' : 
                stats.hit_rate >= 40 ? 'text-yellow-600' : 
                'text-red-600'
              }`}>
                {stats.hit_rate.toFixed(1)}% hit rate
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CacheMetricsCard;
