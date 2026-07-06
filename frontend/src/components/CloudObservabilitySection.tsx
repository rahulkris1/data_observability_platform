/**
 * CloudObservabilitySection Component
 * 
 * Comprehensive AWS cloud observability dashboard section
 * Displays CloudWatch status, metrics provider, and AWS service health
 */

import React, { useState, useEffect } from 'react';
import CloudWatchStatusCard from './CloudWatchStatusCard';
import MetricsProviderStatus from './MetricsProviderStatus';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unavailable';
  message: string;
}

interface CloudObservabilitySectionProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export default function CloudObservabilitySection({
  autoRefresh = true,
  refreshInterval = 30000
}: CloudObservabilitySectionProps) {
  const [serviceHealth, setServiceHealth] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    loadServiceHealth();

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadServiceHealth();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadServiceHealth = async () => {
    try {
      setLoading(true);

      // Fetch CloudWatch status
      const cwResponse = await fetch('/api/v1/observability/cloudwatch/status');
      const cwData = await cwResponse.json();

      // Fetch storage provider status
      const storageResponse = await fetch('/api/v1/storage/provider/status');
      const storageData = await storageResponse.json();

      // Fetch Glue status (if available)
      let glueStatus = 'unavailable';
      try {
        const glueResponse = await fetch('/api/v1/glue/status');
        if (glueResponse.ok) {
          const glueData = await glueResponse.json();
          glueStatus = glueData.available ? 'healthy' : 'unavailable';
        }
      } catch {
        glueStatus = 'unavailable';
      }

      // Build service health array
      const health: ServiceHealth[] = [
        {
          name: 'CloudWatch Metrics',
          status: cwData.metrics_available ? 'healthy' : 'unavailable',
          message: cwData.metrics_available
            ? `Active in ${cwData.region}`
            : 'Not configured or disabled'
        },
        {
          name: 'CloudWatch Logs',
          status: cwData.logs_available ? 'healthy' : 'unavailable',
          message: cwData.logs_available
            ? `${cwData.active_log_streams} active streams`
            : 'Not configured or disabled'
        },
        {
          name: 'S3 Storage',
          status: storageData.connected && storageData.provider === 's3' ? 'healthy' : 
                  storageData.provider === 'minio' ? 'unavailable' : 'degraded',
          message: storageData.provider === 's3'
            ? `Connected to ${storageData.provider.toUpperCase()}`
            : 'Using local MinIO storage'
        },
        {
          name: 'AWS Glue',
          status: glueStatus as 'healthy' | 'degraded' | 'unavailable',
          message: glueStatus === 'healthy'
            ? 'Service available'
            : 'Not configured or disabled'
        }
      ];

      setServiceHealth(health);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to load service health:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadServiceHealth();
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'unavailable':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'degraded':
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
      case 'unavailable':
        return (
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        );
      default:
        return null;
    }
  };

  const healthyCount = serviceHealth.filter(s => s.status === 'healthy').length;
  const totalServices = serviceHealth.length;
  const healthPercentage = totalServices > 0 ? (healthyCount / totalServices) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <svg className="w-7 h-7 mr-3 text-orange-600" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
          Cloud Observability
        </h2>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          <svg
            className={`-ml-1 mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Overall Health Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">AWS Services Health</h3>
            <p className="text-sm text-gray-600">
              {healthyCount} of {totalServices} services operational
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-blue-600">{healthPercentage.toFixed(0)}%</div>
            <div className="text-xs text-gray-600">Overall Health</div>
          </div>
        </div>
        <div className="mt-4 bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className="bg-gradient-to-r from-green-500 to-blue-500 h-2 transition-all duration-500"
            style={{ width: `${healthPercentage}%` }}
          ></div>
        </div>
      </div>

      {/* Metrics Provider and CloudWatch Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricsProviderStatus autoRefresh={autoRefresh} refreshInterval={refreshInterval} />
        <CloudWatchStatusCard autoRefresh={autoRefresh} refreshInterval={refreshInterval} />
      </div>

      {/* Service Health Status Cards */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {serviceHealth.map((service) => (
            <div
              key={service.name}
              className={`rounded-lg border p-4 ${getStatusColor(service.status)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(service.status)}
                  <div>
                    <h4 className="font-semibold text-gray-900">{service.name}</h4>
                    <p className="text-sm text-gray-600 mt-1">{service.message}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded capitalize`}>
                  {service.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Last Refresh Info */}
      <div className="text-center text-sm text-gray-500">
        Last refreshed: {lastRefresh.toLocaleString()}
      </div>
    </div>
  );
}
