/**
 * Retry History Table Component
 * Displays retry execution history with timeline and status
 */
import React, { useState, useEffect } from 'react';
import { retryService, type RetryHistoryItem } from '../services/retryService';
import { LoadingSpinner } from './LoadingSpinner';
import { Alert } from './Alert';

interface RetryHistoryTableProps {
  validationLogId?: number;
  datasetName?: string;
  daysBack?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const RetryHistoryTable: React.FC<RetryHistoryTableProps> = ({
  validationLogId,
  datasetName,
  daysBack = 30,
  autoRefresh = false,
  refreshInterval = 30000,
}) => {
  const [history, setHistory] = useState<RetryHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(20);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  useEffect(() => {
    loadHistory();

    if (autoRefresh) {
      const interval = setInterval(loadHistory, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [validationLogId, datasetName, daysBack, currentPage]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await retryService.getRetryHistory({
        validation_log_id: validationLogId,
        dataset_name: datasetName,
        days_back: daysBack,
        limit: pageSize,
        offset: currentPage * pageSize,
      });

      setHistory(response.retries);
      setTotalCount(response.total_count);
    } catch (err: any) {
      setError(err.message || 'Failed to load retry history');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const formatDateTime = (dateString?: string): string => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      in_progress: 'bg-blue-100 text-blue-800 border-blue-200',
      completed: 'bg-green-100 text-green-800 border-green-200',
      failed: 'bg-red-100 text-red-800 border-red-200',
      cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
    };

    const color = statusColors[status] || 'bg-gray-100 text-gray-800 border-gray-200';

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${color}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  if (loading && history.length === 0) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert variant="error" message={error} onClose={() => setError(null)} />;
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow border border-gray-200">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 mb-4">
          <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Retry History</h3>
        <p className="text-gray-600">No retry attempts found for the specified criteria.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Retry History</h3>
            <p className="text-sm text-gray-600 mt-1">
              Showing {history.length} of {totalCount} retry attempts
            </p>
          </div>
          <button
            onClick={loadHistory}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white shadow rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Validation ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Attempts
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Initiated By
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Retry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {history.map((retry) => {
                const isExpanded = expandedIds.has(retry.retry_id);

                return (
                  <React.Fragment key={retry.retry_id}>
                    <tr className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        #{retry.validation_log_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(retry.retry_status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {retry.retry_count} / {retry.max_retries}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {retry.initiated_by}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDateTime(retry.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                        {formatDateTime(retry.last_retry_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => toggleExpand(retry.retry_id)}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          {isExpanded ? 'Hide' : 'Details'}
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Row */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-3">
                            {/* Info */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-xs font-medium text-gray-500 uppercase">Retry Reason</p>
                                <p className="mt-1 text-sm text-gray-900">
                                  {retry.retry_reason || 'No reason provided'}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs font-medium text-gray-500 uppercase">Completed At</p>
                                <p className="mt-1 text-sm text-gray-900">
                                  {formatDateTime(retry.completed_at)}
                                </p>
                              </div>
                            </div>

                            {/* Error Message */}
                            {retry.error_message && (
                              <div>
                                <p className="text-xs font-medium text-gray-500 uppercase">Error Message</p>
                                <p className="mt-1 text-sm text-red-600">{retry.error_message}</p>
                              </div>
                            )}

                            {/* Retry Results */}
                            {retry.retry_results && retry.retry_results.length > 0 && (
                              <div>
                                <p className="text-xs font-medium text-gray-500 uppercase mb-2">Attempt History</p>
                                <div className="space-y-2">
                                  {retry.retry_results.map((result: any, idx: number) => (
                                    <div
                                      key={idx}
                                      className="bg-white border border-gray-200 rounded p-3 text-sm"
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="font-medium">Attempt {result.attempt}</span>
                                        <span className="text-xs text-gray-500">{result.timestamp}</span>
                                      </div>
                                      {result.status && (
                                        <div className="mt-1">
                                          Status: {getStatusBadge(result.status)}
                                        </div>
                                      )}
                                      {result.message && (
                                        <p className="mt-1 text-gray-600">{result.message}</p>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Retryable Status */}
                            <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                              <span className="text-sm text-gray-600">
                                {retry.is_retryable ? (
                                  <span className="text-green-600 font-medium">✓ Can be retried</span>
                                ) : (
                                  <span className="text-gray-500">Cannot be retried</span>
                                )}
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white px-4 py-3 border border-gray-200 rounded-lg flex items-center justify-between">
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
              disabled={currentPage === 0}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
              disabled={currentPage >= totalPages - 1}
              className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing page <span className="font-medium">{currentPage + 1}</span> of{' '}
                <span className="font-medium">{totalPages}</span>
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                  disabled={currentPage === 0}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
                  disabled={currentPage >= totalPages - 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RetryHistoryTable;
