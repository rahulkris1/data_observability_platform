import React from 'react';
import ValidationStatusBadge, { ValidationStatus } from './ValidationStatusBadge';

export interface ValidationSummary {
  validatorName: string;
  status: ValidationStatus;
  totalRecords: number;
  failedRecords: number;
  passRate: number;
  executionTimeMs?: number;
  message: string;
}

export interface ValidationSummaryCardProps {
  summary: ValidationSummary;
  onClick?: () => void;
}

export default function ValidationSummaryCard({
  summary,
  onClick
}: ValidationSummaryCardProps) {
  const isClickable = !!onClick;
  
  return (
    <div
      className={`
        bg-white rounded-lg shadow-sm border border-gray-200 p-5
        transition-all duration-200
        ${isClickable ? 'cursor-pointer hover:shadow-md hover:border-blue-300' : ''}
      `}
      onClick={onClick}
      role={isClickable ? 'button' : undefined}
      tabIndex={isClickable ? 0 : undefined}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-base font-semibold text-gray-900 mb-1">
            {summary.validatorName}
          </h3>
          <p className="text-sm text-gray-600 line-clamp-2">
            {summary.message}
          </p>
        </div>
        <div className="ml-3">
          <ValidationStatusBadge status={summary.status} size="sm" />
        </div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-gray-100">
        {/* Total Records */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Total Records</p>
          <p className="text-lg font-semibold text-gray-900">
            {summary.totalRecords.toLocaleString()}
          </p>
        </div>
        
        {/* Failed Records */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Failed</p>
          <p className={`text-lg font-semibold ${summary.failedRecords > 0 ? 'text-red-600' : 'text-gray-900'}`}>
            {summary.failedRecords.toLocaleString()}
          </p>
        </div>
        
        {/* Pass Rate */}
        <div>
          <p className="text-xs text-gray-500 mb-1">Pass Rate</p>
          <p className={`text-lg font-semibold ${summary.passRate >= 95 ? 'text-green-600' : summary.passRate >= 80 ? 'text-yellow-600' : 'text-red-600'}`}>
            {summary.passRate.toFixed(1)}%
          </p>
        </div>
      </div>
      
      {/* Execution Time */}
      {summary.executionTimeMs !== undefined && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            Execution time: <span className="font-medium text-gray-700">{summary.executionTimeMs.toFixed(2)}ms</span>
          </p>
        </div>
      )}
    </div>
  );
}

export interface ValidationSummaryCardsProps {
  summaries: ValidationSummary[];
  onCardClick?: (summary: ValidationSummary) => void;
  loading?: boolean;
}

export function ValidationSummaryCards({
  summaries,
  onCardClick,
  loading = false
}: ValidationSummaryCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
            <div className="animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-4"></div>
              <div className="grid grid-cols-3 gap-3">
                <div className="h-12 bg-gray-200 rounded"></div>
                <div className="h-12 bg-gray-200 rounded"></div>
                <div className="h-12 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }
  
  if (summaries.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No validation results</h3>
        <p className="mt-1 text-sm text-gray-500">Run validations to see results here.</p>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {summaries.map((summary, index) => (
        <ValidationSummaryCard
          key={`${summary.validatorName}-${index}`}
          summary={summary}
          onClick={onCardClick ? () => onCardClick(summary) : undefined}
        />
      ))}
    </div>
  );
}
