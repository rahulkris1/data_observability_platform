/**
 * Failure Insights Panel Component
 * Displays failure patterns, retry metrics, and insights
 */
import React, { useState, useEffect } from 'react';
import { retryService, type RetryMetrics, type FailureInsights } from '../services/retryService';
import { LoadingSpinner } from './LoadingSpinner';
import { Alert } from './Alert';

interface FailureInsightsPanelProps {
  datasetName?: string;
  daysBack?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const FailureInsightsPanel: React.FC<FailureInsightsPanelProps> = ({
  datasetName,
  daysBack = 7,
  autoRefresh = false,
  refreshInterval = 60000,
}) => {
  const [metrics, setMetrics] = useState<RetryMetrics | null>(null);
  const [insights, setInsights] = useState<FailureInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'metrics' | 'patterns'>('metrics');

  useEffect(() => {
    loadData();

    if (autoRefresh) {
      const interval = setInterval(loadData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [datasetName, daysBack]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsData, insightsData] = await Promise.all([
        retryService.getRetryMetrics(datasetName, daysBack),
        retryService.getFailureInsights(datasetName, daysBack),
      ]);

      setMetrics(metricsData);
      setInsights(insightsData);
    } catch (err: any) {
      setError(err.message || 'Failed to load failure insights');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !metrics) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert variant="error" message={error} onClose={() => setError(null)} />;
  }

  if (!metrics || !insights) {
    return null;
  }

  const getStatusColor = (value: number, type: 'success' | 'warning' | 'error'): string => {
    if (type === 'success') {
      return value >= 80 ? 'text-green-600' : value >= 50 ? 'text-yellow-600' : 'text-red-600';
    } else if (type === 'warning') {
      return value >= 20 ? 'text-yellow-600' : 'text-green-600';
    } else {
      return value >= 20 ? 'text-red-600' : value >= 10 ? 'text-yellow-600' : 'text-green-600';
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Failure Insights</h3>
            <p className="text-sm text-gray-600 mt-1">
              Analysis for the last {daysBack} days
            </p>
          </div>
          <button
            onClick={loadData}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('metrics')}
              className={`py-4 px-6 text-sm font-medium border-b-2 ${
                activeTab === 'metrics'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Retry Metrics
            </button>
            <button
              onClick={() => setActiveTab('patterns')}
              className={`py-4 px-6 text-sm font-medium border-b-2 ${
                activeTab === 'patterns'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Failure Patterns
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'metrics' ? (
            <div className="space-y-6">
              {/* Overall Statistics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs font-medium text-gray-500 uppercase">Total Retries</p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {metrics.total_retries}
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs font-medium text-gray-500 uppercase">Success Rate</p>
                  <p className={`mt-2 text-3xl font-semibold ${getStatusColor(metrics.success_rate, 'success')}`}>
                    {metrics.success_rate.toFixed(1)}%
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs font-medium text-gray-500 uppercase">First Attempt Success</p>
                  <p className={`mt-2 text-3xl font-semibold ${getStatusColor(metrics.first_attempt_success_rate, 'success')}`}>
                    {metrics.first_attempt_success_rate.toFixed(1)}%
                  </p>
                </div>

                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <p className="text-xs font-medium text-gray-500 uppercase">Avg Retry Count</p>
                  <p className="mt-2 text-3xl font-semibold text-gray-900">
                    {metrics.average_retry_count}
                  </p>
                </div>
              </div>

              {/* Status Breakdown */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-3">Status Breakdown</h4>
                <div className="space-y-2">
                  {Object.entries(metrics.status_breakdown).map(([status, count]) => {
                    const percentage = metrics.total_retries > 0
                      ? (count / metrics.total_retries) * 100
                      : 0;

                    const colors: Record<string, string> = {
                      pending: 'bg-yellow-500',
                      in_progress: 'bg-blue-500',
                      completed: 'bg-green-500',
                      failed: 'bg-red-500',
                      cancelled: 'bg-gray-500',
                    };

                    return (
                      <div key={status} className="flex items-center">
                        <div className="w-32 text-sm text-gray-600 capitalize">
                          {status.replace('_', ' ')}
                        </div>
                        <div className="flex-1 ml-4">
                          <div className="bg-gray-200 rounded-full h-6 overflow-hidden">
                            <div
                              className={`h-full ${colors[status]} flex items-center justify-end px-2 text-xs text-white font-medium`}
                              style={{ width: `${percentage}%`, minWidth: count > 0 ? '2rem' : '0' }}
                            >
                              {count > 0 && count}
                            </div>
                          </div>
                        </div>
                        <div className="w-20 text-right text-sm text-gray-600 ml-4">
                          {percentage.toFixed(1)}%
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Most Retried Validations */}
              {metrics.most_retried_validations.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Most Retried Validations</h4>
                  <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-100">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Dataset
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Validation Type
                          </th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Retry Count
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {metrics.most_retried_validations.map((item, idx) => (
                          <tr key={idx} className="hover:bg-gray-100">
                            <td className="px-4 py-3 text-sm text-gray-900">{item.dataset_name}</td>
                            <td className="px-4 py-3 text-sm text-gray-600">{item.validation_type}</td>
                            <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                              {item.retry_count}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Failure Patterns Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-blue-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-blue-900">
                      {insights.total_unique_patterns} unique failure patterns identified
                    </p>
                    <p className="text-xs text-blue-700 mt-1">
                      Analyzing {daysBack} days of data
                    </p>
                  </div>
                </div>
              </div>

              {/* Common Failure Patterns */}
              {insights.common_failure_patterns.length > 0 ? (
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-gray-900">Top Failure Patterns</h4>
                  {insights.common_failure_patterns.map((pattern, idx) => (
                    <div
                      key={idx}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 border border-red-200">
                              {pattern.count} occurrences
                            </span>
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                              {pattern.validation_type}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-gray-900 font-medium">{pattern.pattern}</p>
                          
                          {pattern.example_errors && pattern.example_errors.length > 0 && (
                            <div className="mt-3 bg-gray-50 rounded p-3">
                              <p className="text-xs font-medium text-gray-500 uppercase mb-2">
                                Example Errors
                              </p>
                              <ul className="space-y-1">
                                {pattern.example_errors.slice(0, 3).map((error, errIdx) => (
                                  <li key={errIdx} className="text-xs text-gray-700">
                                    • {error}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>

                        <div className="ml-4 flex-shrink-0">
                          <div className="text-right">
                            <p className="text-2xl font-bold text-gray-900">{idx + 1}</p>
                            <p className="text-xs text-gray-500">Rank</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Failure Patterns</h3>
                  <p className="text-gray-600">No common failure patterns detected in the selected period.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FailureInsightsPanel;
