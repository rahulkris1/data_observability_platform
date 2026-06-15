/**
 * Load History Table Component
 * Displays warehouse load history with filters and status indicators
 */
import React, { useState } from 'react';
import LoadStatusIndicator, { LoadStatus } from './LoadStatusIndicator';

export interface LoadHistoryRecord {
  id: number;
  batch_id: string;
  dataset_name: string;
  load_status: LoadStatus;
  load_started_at: string | null;
  load_completed_at: string | null;
  source_record_count: number | null;
  warehouse_record_count: number | null;
  records_inserted: number | null;
  records_updated: number | null;
  records_failed: number | null;
  execution_time_seconds: number | null;
  triggered_by: string | null;
  notes: string | null;
}

interface LoadHistoryTableProps {
  history: LoadHistoryRecord[];
  loading?: boolean;
  onRowClick?: (record: LoadHistoryRecord) => void;
}

const LoadHistoryTable: React.FC<LoadHistoryTableProps> = ({
  history,
  loading = false,
  onRowClick,
}) => {
  const [statusFilter, setStatusFilter] = useState<LoadStatus | 'all'>('all');
  const [datasetFilter, setDatasetFilter] = useState<string>('all');

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '-';
    
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  };

  const formatDateTime = (dateString: string | null): string => {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatNumber = (num: number | null): string => {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
  };

  // Get unique datasets for filter
  const uniqueDatasets = Array.from(
    new Set(history.map(record => record.dataset_name))
  );

  // Apply filters
  const filteredHistory = history.filter(record => {
    if (statusFilter !== 'all' && record.load_status !== statusFilter) {
      return false;
    }
    if (datasetFilter !== 'all' && record.dataset_name !== datasetFilter) {
      return false;
    }
    return true;
  });

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-12 bg-gray-200 rounded mb-2"></div>
        <div className="h-12 bg-gray-200 rounded mb-2"></div>
        <div className="h-12 bg-gray-200 rounded mb-2"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 items-center bg-gray-50 p-4 rounded-lg">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as LoadStatus | 'all')}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="started">Started</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="retrying">Retrying</option>
          </select>
        </div>
        
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dataset
          </label>
          <select
            value={datasetFilter}
            onChange={(e) => setDatasetFilter(e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="all">All Datasets</option>
            {uniqueDatasets.map(dataset => (
              <option key={dataset} value={dataset}>{dataset}</option>
            ))}
          </select>
        </div>

        <div className="pt-6">
          <button
            onClick={() => {
              setStatusFilter('all');
              setDatasetFilter('all');
            }}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Table */}
      {filteredHistory.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No load history found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter !== 'all' || datasetFilter !== 'all' 
              ? 'Try adjusting your filters.'
              : 'Load history will appear here once loads are executed.'}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Batch ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dataset
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Records
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredHistory.map((record) => {
                const sourceCount = record.source_record_count || 0;
                const warehouseCount = record.warehouse_record_count || 0;
                const successRate = sourceCount > 0 
                  ? ((warehouseCount / sourceCount) * 100).toFixed(1)
                  : '-';

                return (
                  <tr
                    key={record.id}
                    onClick={() => onRowClick?.(record)}
                    className={`${
                      onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''
                    } transition-colors`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {record.batch_id.substring(0, 12)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {record.dataset_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <LoadStatusIndicator status={record.load_status} size="sm" />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {formatDateTime(record.load_started_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {formatDuration(record.execution_time_seconds)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      <div className="flex flex-col">
                        <span>Source: {formatNumber(record.source_record_count)}</span>
                        <span>Warehouse: {formatNumber(record.warehouse_record_count)}</span>
                        {(record.records_failed || 0) > 0 && (
                          <span className="text-red-600">
                            Failed: {formatNumber(record.records_failed)}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {successRate !== '-' ? (
                        <span
                          className={`font-medium ${
                            parseFloat(successRate) >= 95
                              ? 'text-green-600'
                              : parseFloat(successRate) >= 80
                              ? 'text-yellow-600'
                              : 'text-red-600'
                          }`}
                        >
                          {successRate}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary */}
      <div className="text-sm text-gray-500 text-right">
        Showing {filteredHistory.length} of {history.length} records
      </div>
    </div>
  );
};

export default LoadHistoryTable;
