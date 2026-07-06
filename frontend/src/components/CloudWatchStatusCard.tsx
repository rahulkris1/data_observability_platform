/**
 * CloudWatchStatusCard Component
 * 
 * Displays CloudWatch metrics and logs publishing status
 * Shows connection status, active provider, and service health
 */

import React, { useState, useEffect } from 'react';

interface CloudWatchStatus {
  metrics_enabled: boolean;
  metrics_available: boolean;
  logs_enabled: boolean;
  logs_available: boolean;
  namespace: string | null;
  log_group: string | null;
  region: string | null;
  active_log_streams: number;
  provider: string;
}

interface CloudWatchStatusCardProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function CloudWatchStatusCard({
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}: CloudWatchStatusCardProps) {
  const [status, setStatus] = useState<CloudWatchStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadStatus();

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadStatus();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/observability/cloudwatch/status');
      if (!response.ok) {
        throw new Error(`Failed to fetch CloudWatch status: ${response.statusText}`);
      }

      const data = await response.json();
      setStatus(data);
      setLastRefresh(new Date());
    } catch (err) {
      console.error('Failed to load CloudWatch status:', err);
      setError('Failed to load CloudWatch status');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadStatus();
  };

  if (loading && !status) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Loading CloudWatch status...</span>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-red-700">{error || 'CloudWatch status unavailable'}</span>
          </div>
          <button
            onClick={handleRefresh}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const isCloudWatchActive = status.provider === 'cloudwatch';
  const metricsAvailable = status.metrics_available;
  const logsAvailable = status.logs_available;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <svg className="w-5 h-5 mr-2 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
          CloudWatch Status
        </h3>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Provider Status */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Active Provider:</span>
          <div className="flex items-center space-x-2">
            {isCloudWatchActive ? (
              <>
                <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                <span className="text-sm font-bold text-orange-600">AWS CloudWatch</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                <span className="text-sm font-bold text-gray-600">Local</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Status */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Metrics Publishing:</span>
          {metricsAvailable ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Active
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              Disabled
            </span>
          )}
        </div>
        {status.namespace && (
          <div className="text-xs text-gray-500 ml-4">
            Namespace: <span className="font-mono">{status.namespace}</span>
          </div>
        )}
      </div>

      {/* Logs Status */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Logs Publishing:</span>
          {logsAvailable ? (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              Active
            </span>
          ) : (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
              <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              Disabled
            </span>
          )}
        </div>
        {status.log_group && (
          <div className="text-xs text-gray-500 ml-4">
            Log Group: <span className="font-mono">{status.log_group}</span>
          </div>
        )}
        {logsAvailable && status.active_log_streams > 0 && (
          <div className="text-xs text-gray-500 ml-4">
            Active Streams: <span className="font-semibold">{status.active_log_streams}</span>
          </div>
        )}
      </div>

      {/* Region Info */}
      {status.region && (
        <div className="mb-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">AWS Region:</span>
            <span className="text-sm text-gray-900 font-mono">{status.region}</span>
          </div>
        </div>
      )}

      {/* Last Refresh */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          Last updated: {lastRefresh.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
