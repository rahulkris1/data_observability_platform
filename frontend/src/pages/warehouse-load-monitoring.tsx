/**
 * Warehouse Load Monitoring Page
 * Comprehensive monitoring for warehouse loads, failures, and retry management
 */
import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import LoadHistoryTable, { LoadHistoryRecord } from '../components/LoadHistoryTable';
import FailedLoadSection, { FailedLoadWithDetails } from '../components/FailedLoadSection';
import LoadStatusIndicator from '../components/LoadStatusIndicator';

interface LoadStatistics {
  total_loads: number;
  completed_loads: number;
  failed_loads: number;
  retrying_loads: number;
  success_rate: number;
  average_execution_time_seconds: number;
  period_days: number;
  dataset_name: string | null;
}

interface FailedLoadSummary {
  total_failed_loads: number;
  ready_for_retry: number;
  needs_validation: number;
  max_retries_reached: number;
  failure_reasons: Record<string, number>;
  dataset_name: string | null;
}

export default function WarehouseLoadMonitoring() {
  const [activeTab, setActiveTab] = useState<'history' | 'failed'>('history');
  const [loadHistory, setLoadHistory] = useState<LoadHistoryRecord[]>([]);
  const [failedLoads, setFailedLoads] = useState<FailedLoadWithDetails[]>([]);
  const [statistics, setStatistics] = useState<LoadStatistics | null>(null);
  const [failedSummary, setFailedSummary] = useState<FailedLoadSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [days, setDays] = useState(7);
  const [datasetFilter, setDatasetFilter] = useState<string>('');

  const fetchLoadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch load history
      const historyParams = new URLSearchParams();
      historyParams.append('days', days.toString());
      historyParams.append('limit', '100');
      if (datasetFilter) {
        historyParams.append('dataset_name', datasetFilter);
      }
      
      const historyResponse = await fetch(
        `/api/load-monitoring/audit/history?${historyParams.toString()}`
      );
      
      if (!historyResponse.ok) {
        throw new Error('Failed to fetch load history');
      }
      
      const historyData = await historyResponse.json();
      setLoadHistory(historyData.history || []);

      // Fetch load statistics
      const statsParams = new URLSearchParams();
      statsParams.append('days', days.toString());
      if (datasetFilter) {
        statsParams.append('dataset_name', datasetFilter);
      }
      
      const statsResponse = await fetch(
        `/api/load-monitoring/audit/statistics?${statsParams.toString()}`
      );
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatistics(statsData.statistics);
      }

      // Fetch failed loads summary
      const summaryParams = new URLSearchParams();
      if (datasetFilter) {
        summaryParams.append('dataset_name', datasetFilter);
      }
      
      const summaryResponse = await fetch(
        `/api/load-monitoring/retry/summary?${summaryParams.toString()}`
      );
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setFailedSummary(summaryData.summary);
      }

      // Fetch retry-ready loads for failed loads tab
      const failedParams = new URLSearchParams();
      failedParams.append('limit', '50');
      if (datasetFilter) {
        failedParams.append('dataset_name', datasetFilter);
      }
      
      const failedResponse = await fetch(
        `/api/load-monitoring/retry/ready?${failedParams.toString()}`
      );
      
      if (failedResponse.ok) {
        const failedData = await failedResponse.json();
        setFailedLoads(failedData.retry_ready_loads || []);
      }
      
    } catch (err: any) {
      console.error('Error fetching load monitoring data:', err);
      setError(err.message || 'Failed to fetch load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLoadData();
  }, [days, datasetFilter]);

  const handleRefresh = () => {
    fetchLoadData();
  };

  const handleClearFilters = () => {
    setDays(7);
    setDatasetFilter('');
  };

  const handleValidateRetry = async (batchId: string) => {
    try {
      const response = await fetch('/api/load-monitoring/retry/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch_id: batchId,
          validated_by: 'system_user', // In production, use actual user
          validation_notes: 'Manual validation from UI',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to validate retry');
      }

      const result = await response.json();
      
      if (result.validation.can_retry) {
        alert(`Retry validated successfully for batch ${batchId}`);
      } else {
        alert(`Retry validation failed:\n${result.validation.checks_failed.join('\n')}`);
      }
      
      // Refresh data
      fetchLoadData();
      
    } catch (err: any) {
      console.error('Error validating retry:', err);
      alert(`Error: ${err.message}`);
    }
  };

  const handleRevokeRetry = async (batchId: string) => {
    if (!confirm(`Are you sure you want to revoke retry approval for batch ${batchId}?`)) {
      return;
    }

    try {
      const response = await fetch('/api/load-monitoring/retry/revoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch_id: batchId,
          revoked_by: 'system_user', // In production, use actual user
          reason: 'Manual revocation from UI',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to revoke retry approval');
      }

      alert(`Retry approval revoked for batch ${batchId}`);
      
      // Refresh data
      fetchLoadData();
      
    } catch (err: any) {
      console.error('Error revoking retry:', err);
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <DashboardLayout 
      title="Warehouse Load Monitoring"
      subtitle="Monitor load history, track failures, and manage retry validation"
    >
      {/* Statistics Cards */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="text-sm text-gray-600 font-medium">Total Loads</div>
            <div className="text-3xl font-bold text-gray-900 mt-2">
              {statistics.total_loads}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Last {statistics.period_days} days
            </div>
          </div>

          <div className="bg-green-50 rounded-lg shadow-sm border border-green-200 p-6">
            <div className="text-sm text-green-700 font-medium">Completed</div>
            <div className="text-3xl font-bold text-green-900 mt-2">
              {statistics.completed_loads}
            </div>
            <div className="text-xs text-green-600 mt-1">
              {statistics.success_rate.toFixed(1)}% success rate
            </div>
          </div>

          <div className="bg-red-50 rounded-lg shadow-sm border border-red-200 p-6">
            <div className="text-sm text-red-700 font-medium">Failed</div>
            <div className="text-3xl font-bold text-red-900 mt-2">
              {statistics.failed_loads}
            </div>
            <div className="text-xs text-red-600 mt-1">
              {failedSummary?.ready_for_retry || 0} ready for retry
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg shadow-sm border border-blue-200 p-6">
            <div className="text-sm text-blue-700 font-medium">Avg Duration</div>
            <div className="text-3xl font-bold text-blue-900 mt-2">
              {Math.round(statistics.average_execution_time_seconds)}s
            </div>
            <div className="text-xs text-blue-600 mt-1">
              Average execution time
            </div>
          </div>
        </div>
      )}

      {/* Filters and Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Filters & Controls
          </h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear Filters
            </button>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              <svg 
                className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Period
            </label>
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dataset
            </label>
            <input
              type="text"
              value={datasetFilter}
              onChange={(e) => setDatasetFilter(e.target.value)}
              placeholder="Filter by dataset name..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Load History
            </button>
            <button
              onClick={() => setActiveTab('failed')}
              className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'failed'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Failed Loads
              {failedSummary && failedSummary.total_failed_loads > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">
                  {failedSummary.total_failed_loads}
                </span>
              )}
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'history' && (
            <LoadHistoryTable 
              history={loadHistory}
              loading={loading}
              onRowClick={(record) => {
                console.log('Load history record clicked:', record);
                // Could implement modal or detail view here
              }}
            />
          )}

          {activeTab === 'failed' && (
            <FailedLoadSection 
              failedLoads={failedLoads}
              loading={loading}
              onValidateRetry={handleValidateRetry}
              onRevokeRetry={handleRevokeRetry}
              onViewDetails={(load) => {
                console.log('Failed load details:', load);
                // Could implement modal or detail view here
              }}
            />
          )}
        </div>
      </div>

      {/* Important Notice */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <svg className="w-5 h-5 text-yellow-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-yellow-800">Manual Retry Policy</h4>
            <p className="text-sm text-yellow-700 mt-1">
              This system does NOT perform automatic retries. All failed loads must be validated manually before retry. 
              Use the &quot;Validate for Retry&quot; button to approve loads for manual retry execution.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
