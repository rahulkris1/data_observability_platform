/**
 * Cache API service for frontend
 * Provides methods to interact with cache monitoring endpoints
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface CacheStatus {
  connected: boolean;
  redis_version?: string;
  used_memory?: string;
  connected_clients?: number;
  uptime_days?: number;
  error?: string;
}

export interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  hit_rate: number;
  cached_contracts: number;
  cached_metadata: number;
}

export interface CacheRefreshResponse {
  message: string;
  invalidated_contracts: number;
  invalidated_metadata: number;
  stats_reset: boolean;
}

export interface CacheMetrics {
  cache_performance: {
    hits: number;
    misses: number;
    hit_rate: number;
    total_requests: number;
  };
  cache_operations: {
    sets: number;
    deletes: number;
  };
  cached_items: {
    contracts: number;
    metadata: number;
    total: number;
  };
  redis_server: {
    connected: boolean;
    version: string;
    used_memory: string;
    connected_clients: number;
    uptime_days: number;
  };
  invalidation_stats: any;
}

/**
 * Get cache connection status
 */
export async function getCacheStatus(): Promise<CacheStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cache status: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get cache performance statistics
 */
export async function getCacheStats(): Promise<CacheStats> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/stats`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cache stats: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Refresh cache (invalidate all and reset stats)
 */
export async function refreshCache(): Promise<CacheRefreshResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/refresh`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error(`Failed to refresh cache: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Invalidate cache for a specific table
 */
export async function invalidateTableCache(tableName: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/invalidate/${tableName}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to invalidate cache for ${tableName}: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get cache health check
 */
export async function getCacheHealth(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/health`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cache health: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get comprehensive cache metrics
 */
export async function getCacheMetrics(): Promise<CacheMetrics> {
  const response = await fetch(`${API_BASE_URL}/api/v1/cache/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cache metrics: ${response.statusText}`);
  }
  return response.json();
}

export default {
  getCacheStatus,
  getCacheStats,
  refreshCache,
  invalidateTableCache,
  getCacheHealth,
  getCacheMetrics,
};
