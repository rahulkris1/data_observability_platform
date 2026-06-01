import React from 'react';

export interface DatasetStatistics {
  dataset_name: string;
  row_count: number;
  column_count: number;
  validation_score: number;
  last_validated?: string | Date | null;
}

export interface DatasetStatisticsCardProps {
  statistics: DatasetStatistics | null;
  loading?: boolean;
  emptyMessage?: string;
}

export default function DatasetStatisticsCard({
  statistics,
  loading = false,
  emptyMessage = 'No dataset statistics available'
}: DatasetStatisticsCardProps) {
  // Show empty state if no statistics
  if (!loading && !statistics) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
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
            d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No dataset data</h3>
        <p className="mt-1 text-sm text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  const formatDate = (date: string | Date | null | undefined) => {
    if (!date) return 'Never';
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const score = statistics?.validation_score ?? 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Dataset Statistics
        </h3>
        <div className="flex items-center space-x-2">
          <svg
            className="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 animate-pulse rounded"></div>
          <div className="h-6 bg-gray-200 animate-pulse rounded"></div>
          <div className="h-6 bg-gray-200 animate-pulse rounded"></div>
          <div className="h-6 bg-gray-200 animate-pulse rounded"></div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Dataset Name */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Dataset</span>
            <span className="text-sm font-semibold text-gray-900">
              {statistics?.dataset_name || 'N/A'}
            </span>
          </div>

          <div className="border-t border-gray-100"></div>

          {/* Row Count */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Rows</span>
            <span className="text-sm font-semibold text-gray-900">
              {(statistics?.row_count ?? 0).toLocaleString()}
            </span>
          </div>

          {/* Column Count */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Columns</span>
            <span className="text-sm font-semibold text-gray-900">
              {statistics?.column_count ?? 0}
            </span>
          </div>

          <div className="border-t border-gray-100"></div>

          {/* Validation Score */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">
              Validation Score
            </span>
            <div className="flex items-center space-x-2">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(
                  score
                )}`}
              >
                {score.toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Last Validated */}
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">
              Last Validated
            </span>
            <span className="text-sm text-gray-900">
              {formatDate(statistics?.last_validated)}
            </span>
          </div>
        </div>
      )}

      {/* Footer with visual score indicator */}
      {!loading && statistics && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-600">
              Quality Score
            </span>
            <span className="text-xs font-semibold text-gray-900">
              {score.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                score >= 90
                  ? 'bg-green-500'
                  : score >= 70
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}
