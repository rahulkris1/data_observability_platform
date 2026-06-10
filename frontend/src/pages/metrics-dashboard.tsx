import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import MetricCard from '../components/MetricCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { getMetricsSummary, MetricsSummary, MetricsFilters } from '../services/metricsService';

export default function MetricsDashboard() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(0); // 0 = manual only
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // Filter state
  const [filters, setFilters] = useState<MetricsFilters>({
    start_date: undefined,
    end_date: undefined,
    dataset_name: undefined,
    validation_type: undefined,
  });
  
  // Date range presets
  const [dateRange, setDateRange] = useState<string>('7days');
  
  // Fetch metrics data
  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Calculate date range based on preset
      const endDate = new Date();
      let startDate = new Date();
      
      switch (dateRange) {
        case '24hours':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7days':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30days':
          startDate.setDate(startDate.getDate() - 30);
          break;
        case '90days':
          startDate.setDate(startDate.getDate() - 90);
          break;
      }
      
      const currentFilters: MetricsFilters = {
        ...filters,
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      };
      
      const data = await getMetricsSummary(currentFilters);
      setMetrics(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching metrics:', err);
      setError('Failed to load metrics. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Initial load
  useEffect(() => {
    fetchMetrics();
  }, [dateRange, filters]);
  
  // Auto-refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchMetrics, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, dateRange, filters]);
  
  // Manual refresh
  const handleRefresh = () => {
    fetchMetrics();
  };
  
  // Clear filters
  const handleClearFilters = () => {
    setFilters({
      start_date: undefined,
      end_date: undefined,
      dataset_name: undefined,
      validation_type: undefined,
    });
  };
  
  // Render loading state
  if (loading && !metrics) {
    return (
      <DashboardLayout
        title="Metrics Dashboard"
        subtitle="Monitor validation, ingestion, and performance metrics"
      >
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </DashboardLayout>
    );
  }
  
  // Render error state
  if (error && !metrics) {
    return (
      <DashboardLayout
        title="Metrics Dashboard"
        subtitle="Monitor validation, ingestion, and performance metrics"
      >
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-red-800 font-medium mb-2">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </DashboardLayout>
    );
  }
  
  // Render empty state
  if (!loading && !metrics) {
    return (
      <DashboardLayout
        title="Metrics Dashboard"
        subtitle="Monitor validation, ingestion, and performance metrics"
      >
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Metrics Available</h3>
          <p className="text-gray-600 mb-6">
            No metrics data found for the selected filters. Try adjusting your filters or run some validations first.
          </p>
          <button
            onClick={handleClearFilters}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title="Metrics Dashboard"
      subtitle="Monitor validation, ingestion, and performance metrics"
    >
      {/* Controls Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date Range Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Time Range:</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="24hours">Last 24 Hours</option>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </select>
          </div>
          
          {/* Dataset Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Dataset:</label>
            <input
              type="text"
              placeholder="All datasets"
              value={filters.dataset_name || ''}
              onChange={(e) => setFilters({ ...filters, dataset_name: e.target.value || undefined })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Validation Type Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Validation Type:</label>
            <select
              value={filters.validation_type || ''}
              onChange={(e) => setFilters({ ...filters, validation_type: e.target.value || undefined })}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All types</option>
              <option value="schema">Schema</option>
              <option value="null">Null Check</option>
              <option value="datatype">Data Type</option>
              <option value="checksum">Checksum</option>
              <option value="aggregated">Aggregated</option>
            </select>
          </div>
          
          {/* Refresh Interval */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Auto-refresh:</label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={0}>Manual</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
            </select>
          </div>
          
          {/* Manual Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 flex items-center gap-2"
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
        
        {/* Last Updated */}
        {lastUpdated && (
          <div className="mt-2 text-xs text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </div>

      {/* Validation Metrics */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Validation Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Total Validations"
            value={metrics?.validation.total || 0}
            subtitle={`${metrics?.period.days || 0} days`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Success Count"
            value={metrics?.validation.success || 0}
            subtitle={`${metrics?.validation.success_rate.toFixed(1) || 0}% success rate`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Failure Count"
            value={metrics?.validation.failure || 0}
            subtitle="Failed validations"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Warning Count"
            value={metrics?.validation.warning || 0}
            subtitle="Validations with warnings"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
            loading={loading}
          />
        </div>
      </div>

      {/* Ingestion Metrics */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Ingestion Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <MetricCard
            title="Total Executions"
            value={metrics?.ingestion.total_executions || 0}
            subtitle="Ingestion runs"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Success Count"
            value={metrics?.ingestion.success || 0}
            subtitle={`${metrics?.ingestion.success_rate.toFixed(1) || 0}% success rate`}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Failure Count"
            value={metrics?.ingestion.failure || 0}
            subtitle="Failed ingestions"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            }
            loading={loading}
          />
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <MetricCard
            title="Avg Validation Duration"
            value={`${metrics?.performance.avg_validation_duration_ms.toFixed(0) || 0} ms`}
            subtitle="Average execution time"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Avg Ingestion Duration"
            value={`${metrics?.performance.avg_ingestion_duration_ms.toFixed(0) || 0} ms`}
            subtitle="Average execution time"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            }
            loading={loading}
          />
          
          <MetricCard
            title="Avg API Response Time"
            value={`${metrics?.performance.avg_api_duration_ms.toFixed(0) || 0} ms`}
            subtitle="Average API latency"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
            loading={loading}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
