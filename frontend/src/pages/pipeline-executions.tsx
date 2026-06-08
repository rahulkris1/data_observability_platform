/**
 * Pipeline Executions Page
 * Displays DAG execution history and monitoring
 */
import React, { useState, useEffect } from 'react';
import MainLayout from '@/layouts/MainLayout';
import DAGExecutionTable from '@/components/DAGExecutionTable';
import DAGExecutionTimeline from '@/components/DAGExecutionTimeline';
import LoadingSpinner from '@/components/LoadingSpinner';
import {
  dagExecutionService,
  DAGExecution,
  DAGExecutionSummary,
} from '@/services/dagExecutionService';

export default function PipelineExecutionsPage() {
  const [executions, setExecutions] = useState<DAGExecution[]>([]);
  const [summary, setSummary] = useState<DAGExecutionSummary | null>(null);
  const [selectedExecution, setSelectedExecution] = useState<DAGExecution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Filters
  const [dagIdFilter, setDagIdFilter] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<string>('');

  const fetchExecutions = async () => {
    try {
      const filters: any = {
        limit: 50,
        offset: 0,
      };

      if (dagIdFilter) filters.dag_id = dagIdFilter;
      if (stateFilter) filters.state = stateFilter;
      if (dateFilter) {
        const date = new Date(dateFilter);
        filters.start_date = date.toISOString();
      }

      const [executionsData, summaryData] = await Promise.all([
        dagExecutionService.listExecutions(filters),
        dagExecutionService.getExecutionSummary(dagIdFilter || undefined),
      ]);

      setExecutions(executionsData.executions);
      setSummary(summaryData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch DAG executions');
      console.error('Error fetching executions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, [dagIdFilter, stateFilter, dateFilter]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchExecutions, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, dagIdFilter, stateFilter, dateFilter]);

  const handleRefresh = () => {
    setLoading(true);
    fetchExecutions();
  };

  const handleClearFilters = () => {
    setDagIdFilter('');
    setStateFilter('');
    setDateFilter('');
  };

  const uniqueDAGs = Array.from(new Set(executions.map((e) => e.dag_id)));

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pipeline Executions</h1>
            <p className="text-gray-600 mt-2">
              Monitor and track DAG execution history
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {/* Auto-refresh toggle */}
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Auto-refresh</span>
            </label>

            {/* Refresh button */}
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
              <p className="text-sm text-gray-600">Total Executions</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {summary.total_executions}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border border-green-200 bg-green-50">
              <p className="text-sm text-green-700">Successful</p>
              <p className="text-2xl font-bold text-green-900 mt-1">
                {summary.successful}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border border-red-200 bg-red-50">
              <p className="text-sm text-red-700">Failed</p>
              <p className="text-2xl font-bold text-red-900 mt-1">
                {summary.failed}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border border-blue-200 bg-blue-50">
              <p className="text-sm text-blue-700">Running</p>
              <p className="text-2xl font-bold text-blue-900 mt-1">
                {summary.running}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
              <p className="text-sm text-gray-600">Success Rate</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {summary.success_rate.toFixed(1)}%
              </p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* DAG ID filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                DAG ID
              </label>
              <select
                value={dagIdFilter}
                onChange={(e) => setDagIdFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All DAGs</option>
                {uniqueDAGs.map((dagId) => (
                  <option key={dagId} value={dagId}>
                    {dagId}
                  </option>
                ))}
              </select>
            </div>

            {/* State filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All States</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="running">Running</option>
              </select>
            </div>

            {/* Date filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Execution Date
              </label>
              <input
                type="date"
                value={dateFilter}
                onChange={(e) => setDateFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* Clear filters */}
            <div className="flex items-end">
              <button
                onClick={handleClearFilters}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Main content: Table and Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Execution table */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Execution History
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {executions.length} execution{executions.length !== 1 ? 's' : ''} found
              </p>
            </div>
            <div className="p-6">
              {loading && executions.length === 0 ? (
                <div className="flex justify-center py-12">
                  <LoadingSpinner />
                </div>
              ) : (
                <DAGExecutionTable
                  executions={executions}
                  loading={loading && executions.length === 0}
                  onRowClick={setSelectedExecution}
                />
              )}
            </div>
          </div>

          {/* Execution timeline */}
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Task Timeline</h2>
              <p className="text-sm text-gray-500 mt-1">
                {selectedExecution ? 'Task execution sequence' : 'No execution selected'}
              </p>
            </div>
            <div className="p-6">
              <DAGExecutionTimeline execution={selectedExecution} />
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
