/**
 * MetricsProviderStatus Component
 * 
 * Displays the active metrics provider (CloudWatch or Local)
 * Shows which provider is currently being used for metrics storage
 */

import React, { useState, useEffect } from 'react';

interface MetricsProviderInfo {
  active_provider: string;
  cloudwatch_enabled: boolean;
  local_enabled: boolean;
  execution_mode: string;
}

interface MetricsProviderStatusProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function MetricsProviderStatus({
  autoRefresh = true,
  refreshInterval = 30000 // 30 seconds
}: MetricsProviderStatusProps) {
  const [provider, setProvider] = useState<MetricsProviderInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProviderStatus();

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadProviderStatus();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadProviderStatus = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/observability/metrics/provider');
      if (!response.ok) {
        throw new Error(`Failed to fetch metrics provider: ${response.statusText}`);
      }

      const data = await response.json();
      setProvider(data);
    } catch (err) {
      console.error('Failed to load metrics provider status:', err);
      setError('Failed to load metrics provider');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !provider) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Loading...</span>
        </div>
      </div>
    );
  }

  if (error || !provider) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-4">
        <div className="flex items-center space-x-2">
          <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-red-700">{error || 'Provider status unavailable'}</span>
        </div>
      </div>
    );
  }

  const isCloudWatch = provider.active_provider === 'cloudwatch';
  const isLocal = provider.active_provider === 'local';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        {/* Provider Icon and Name */}
        <div className="flex items-center space-x-3">
          {isCloudWatch ? (
            <>
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                  </svg>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Metrics Provider</p>
                <p className="text-lg font-bold text-orange-600">AWS CloudWatch</p>
              </div>
            </>
          ) : (
            <>
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20 6h-2.18c.11-.31.18-.65.18-1a2.996 2.996 0 00-5.5-1.65l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76l1-1.36 1 1.36L15.38 12 17 10.83 14.92 8H20v6z" />
                  </svg>
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Metrics Provider</p>
                <p className="text-lg font-bold text-gray-700">Local Storage</p>
              </div>
            </>
          )}
        </div>

        {/* Status Badge */}
        <div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Active
          </span>
        </div>
      </div>

      {/* Additional Info */}
      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div>
            <span className="text-gray-500">Execution Mode:</span>
            <span className="ml-1 font-semibold text-gray-900 capitalize">{provider.execution_mode}</span>
          </div>
          <div>
            <span className="text-gray-500">Dual Storage:</span>
            <span className="ml-1 font-semibold text-gray-900">
              {provider.cloudwatch_enabled && provider.local_enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        </div>

        {/* Provider Details */}
        <div className="mt-2 flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isCloudWatch ? 'bg-orange-500' : 'bg-gray-300'}`}></div>
            <span className="text-gray-600">CloudWatch</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${isLocal || provider.local_enabled ? 'bg-blue-500' : 'bg-gray-300'}`}></div>
            <span className="text-gray-600">PostgreSQL</span>
          </div>
        </div>
      </div>
    </div>
  );
}
