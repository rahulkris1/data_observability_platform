import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import LoadingSpinner from '../components/LoadingSpinner';
import FreshnessMetricsChart from '../components/FreshnessMetricsChart';
import LatencyChart from '../components/LatencyChart';
import SLAIndicatorCard from '../components/SLAIndicatorCard';
import ThresholdStatusBadge from '../components/ThresholdStatusBadge';
import MetricCard from '../components/MetricCard';
import {
  getFreshnessMetrics,
  getFreshnessSummary,
  getFreshnessTimeSeries,
  FreshnessMetricsSummary,
  FreshnessMetricsListResponse,
  FreshnessTimeSeriesResponse,
  FreshnessFilters
} from '../services/freshnessService';

export default function FreshnessMonitoring() {
  const [summary, setSummary] = useState<FreshnessMetricsSummary | null>(null);
  const [timeSeries, setTimeSeries] = useState<FreshnessTimeSeriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(0); // 0 = manual only
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Filter state
  const [filters, setFilters] = useState<FreshnessFilters>({
    dataset_name: undefined,
    freshness_status: undefined,
    sla_status: undefined,
    start_date: undefined,
    end_date: undefined,
  });

  // Date range presets
  const [dateRange, setDateRange] = useState<string>('7days');

  // Fetch all freshness data
  const fetchFreshnessData = async () => {
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
      }

      const dateFilters = {
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
      };

      // Fetch summary and time series in parallel
      const [summaryData, timeSeriesData] = await Promise.all([
        getFreshnessSummary(dateFilters),
        getFreshnessTimeSeries({
          ...dateFilters,
          dataset_name: filters.dataset_name,
        }),
      ]);

      setSummary(summaryData);
      setTimeSeries(timeSeriesData);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching freshness data:', err);
      setError('Failed to load freshness metrics. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchFreshnessData();
  }, [dateRange, filters.dataset_name]);

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchFreshnessData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [refreshInterval, dateRange, filters]);

  // Manual refresh
  const handleRefresh = () => {
    fetchFreshnessData();
  };

  // Clear filters
  const handleClearFilters = () => {
    setFilters({
      dataset_name: undefined,
      freshness_status: undefined,
      sla_status: undefined,
      start_date: undefined,
      end_date: undefined,
    });
  };

  // Render loading state
  if (loading && !summary) {
    return (
      <DashboardLayout
        title="Freshness Monitoring"
        subtitle="Monitor dataset freshness, latency, and SLA compliance"
      >
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" />
        </div>
      </DashboardLayout>
    );
  }

  // Render error state
  if (error && !summary) {
    return (
      <DashboardLayout
        title="Freshness Monitoring"
        subtitle="Monitor dataset freshness, latency, and SLA compliance"
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

  return (
    <DashboardLayout
      title="Freshness Monitoring"
      subtitle="Monitor dataset freshness, latency, and SLA compliance"
    >
      {/* Controls */}
      <div className="mb-6 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
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
            </select>
          </div>

          {/* Dataset Filter */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Dataset:</label>
            <input
              type="text"
              value={filters.dataset_name || ''}
              onChange={(e) => setFilters({ ...filters, dataset_name: e.target.value || undefined })}
              placeholder="All datasets"
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Refresh Controls */}
          <div className="flex items-center gap-2 ml-auto">
            <label className="text-sm font-medium text-gray-700">Auto-refresh:</label>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="0">Manual</option>
              <option value="30">30 seconds</option>
              <option value="60">1 minute</option>
              <option value="300">5 minutes</option>
            </select>
          </div>

          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>

          {filters.dataset_name && (
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>

        {lastUpdated && (
          <div className="mt-2 text-xs text-gray-500">
            Last updated: {lastUpdated.toLocaleString()}
          </div>
        )}
      </div>

      {/* Empty State */}
      {!loading && (!summary || summary.total_datasets === 0) && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Freshness Data Available</h3>
          <p className="text-gray-600">
            No freshness metrics found for the selected time range. Run some data ingestions to see metrics.
          </p>
        </div>
      )}

      {/* Main Content */}
      {summary && summary.total_datasets > 0 && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Total Datasets"
              value={summary.total_datasets}
              subtitle="Monitored datasets"
              loading={loading}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                </svg>
              }
            />

            <MetricCard
              title="Healthy Datasets"
              value={summary.healthy_count}
              subtitle={`${((summary.healthy_count / summary.total_datasets) * 100).toFixed(0)}% of total`}
              loading={loading}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />

            <MetricCard
              title="Warning"
              value={summary.warning_count}
              subtitle="Aging datasets"
              loading={loading}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              }
            />

            <MetricCard
              title="Critical"
              value={summary.critical_count}
              subtitle="Stale datasets"
              loading={loading}
              icon={
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            />
          </div>

          {/* SLA and Latency Overview */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* SLA Indicator */}
            <SLAIndicatorCard
              compliancePercentage={
                summary.total_datasets > 0
                  ? (summary.sla_compliant_count / summary.total_datasets) * 100
                  : 100
              }
              breachCount={summary.sla_breached_count}
              compliantCount={summary.sla_compliant_count}
              totalOperations={summary.total_datasets}
              loading={loading}
            />

            {/* Average Latencies */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Average Latencies</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-blue-900 mb-1">Ingestion</div>
                  <div className="text-2xl font-bold text-blue-900">
                    {summary.avg_ingestion_latency_seconds
                      ? `${summary.avg_ingestion_latency_seconds.toFixed(2)}s`
                      : 'N/A'}
                  </div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="text-sm text-purple-900 mb-1">Validation</div>
                  <div className="text-2xl font-bold text-purple-900">
                    {summary.avg_validation_latency_seconds
                      ? `${summary.avg_validation_latency_seconds.toFixed(2)}s`
                      : 'N/A'}
                  </div>
                </div>
                <div className="col-span-2 bg-gray-50 rounded-lg p-4">
                  <div className="text-sm text-gray-700 mb-1">Average Dataset Age</div>
                  <div className="text-2xl font-bold text-gray-900">
                    {summary.avg_dataset_age_hours
                      ? `${summary.avg_dataset_age_hours.toFixed(1)}h`
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 gap-6">
            {/* Freshness Chart */}
            {timeSeries && (
              <FreshnessMetricsChart
                dataPoints={timeSeries.data_points}
                datasetName={filters.dataset_name}
                loading={loading}
              />
            )}

            {/* Latency Chart */}
            {timeSeries && (
              <LatencyChart
                dataPoints={timeSeries.data_points}
                datasetName={filters.dataset_name}
                loading={loading}
              />
            )}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}
