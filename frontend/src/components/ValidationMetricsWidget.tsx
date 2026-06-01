import React from 'react';
import MetricCard from './MetricCard';

export interface ValidationMetrics {
  total_validations: number;
  passed_validations: number;
  failed_validations: number;
  warning_validations: number;
  average_pass_rate: number;
}

export interface ValidationMetricsWidgetProps {
  metrics: ValidationMetrics | null;
  loading?: boolean;
  emptyMessage?: string;
}

export default function ValidationMetricsWidget({
  metrics,
  loading = false,
  emptyMessage = 'No validation data available'
}: ValidationMetricsWidgetProps) {
  // Show empty state if no metrics
  if (!loading && !metrics) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No validation data</h3>
        <p className="mt-1 text-sm text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  const passRate = metrics?.average_pass_rate ?? 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Validations */}
      <MetricCard
        title="Total Validations"
        value={metrics?.total_validations ?? 0}
        subtitle="Validations executed"
        loading={loading}
        icon={
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        }
      />

      {/* Passed Validations */}
      <MetricCard
        title="Passed"
        value={metrics?.passed_validations ?? 0}
        subtitle={`${passRate.toFixed(1)}% average pass rate`}
        loading={loading}
        icon={
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        }
      />

      {/* Failed Validations */}
      <MetricCard
        title="Failed"
        value={metrics?.failed_validations ?? 0}
        subtitle="Validations failed"
        loading={loading}
        icon={
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        }
      />

      {/* Warning Validations */}
      <MetricCard
        title="Warnings"
        value={metrics?.warning_validations ?? 0}
        subtitle="Validations with warnings"
        loading={loading}
        icon={
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        }
      />
    </div>
  );
}
