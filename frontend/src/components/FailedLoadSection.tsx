/**
 * Failed Load Section Component
 * Displays failed loads with failure reasons and retry validation
 */
import React, { useState } from 'react';

export interface FailedLoad {
  id: number;
  batch_id: string;
  dataset_name: string;
  failure_reason: string;
  retry_count: number;
  load_failed_at: string | null;
  retry_validated_at: string | null;
  retry_validated_by: string | null;
}

export interface FailedLoadWithDetails extends FailedLoad {
  error_message?: string | null;
  source_record_count?: number | null;
  warehouse_record_count?: number | null;
  failed_record_count?: number | null;
  can_retry?: boolean;
}

interface FailedLoadSectionProps {
  failedLoads: FailedLoadWithDetails[];
  loading?: boolean;
  onValidateRetry?: (batchId: string) => void;
  onRevokeRetry?: (batchId: string) => void;
  onViewDetails?: (load: FailedLoadWithDetails) => void;
}

const FailedLoadSection: React.FC<FailedLoadSectionProps> = ({
  failedLoads,
  loading = false,
  onValidateRetry,
  onRevokeRetry,
  onViewDetails,
}) => {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const toggleExpand = (id: number) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
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

  const getRetryBadge = (load: FailedLoadWithDetails) => {
    if (load.can_retry) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
          ✓ Ready for Retry
        </span>
      );
    } else if (load.retry_validated_at) {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">
          ⚠ Validation Required
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-200">
          ⏸ Not Validated
        </span>
      );
    }
  };

  const getRetryCounts = () => {
    const readyForRetry = failedLoads.filter(load => load.can_retry).length;
    const needsValidation = failedLoads.filter(
      load => !load.can_retry && !load.retry_validated_at
    ).length;
    const maxRetries = failedLoads.filter(load => load.retry_count >= 3).length;

    return { readyForRetry, needsValidation, maxRetries };
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-24 bg-gray-200 rounded"></div>
        <div className="h-24 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (failedLoads.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <svg
          className="mx-auto h-12 w-12 text-green-400"
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
        <h3 className="mt-2 text-sm font-medium text-gray-900">No failed loads</h3>
        <p className="mt-1 text-sm text-gray-500">
          All loads are completing successfully!
        </p>
      </div>
    );
  }

  const { readyForRetry, needsValidation, maxRetries } = getRetryCounts();

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="text-sm text-red-600 font-medium">Total Failed</div>
          <div className="text-2xl font-bold text-red-900 mt-1">
            {failedLoads.length}
          </div>
        </div>
        
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm text-green-600 font-medium">Ready for Retry</div>
          <div className="text-2xl font-bold text-green-900 mt-1">
            {readyForRetry}
          </div>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="text-sm text-yellow-600 font-medium">Needs Validation</div>
          <div className="text-2xl font-bold text-yellow-900 mt-1">
            {needsValidation}
          </div>
        </div>
        
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <div className="text-sm text-gray-600 font-medium">Max Retries Reached</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {maxRetries}
          </div>
        </div>
      </div>

      {/* Failed Loads List */}
      <div className="space-y-3">
        {failedLoads.map((load) => (
          <div
            key={load.id}
            className="bg-white rounded-lg border border-gray-200 overflow-hidden"
          >
            {/* Header */}
            <div className="p-4 flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h4 className="text-sm font-medium text-gray-900">
                    {load.dataset_name}
                  </h4>
                  {getRetryBadge(load)}
                  {load.retry_count > 0 && (
                    <span className="text-xs text-gray-500">
                      Retries: {load.retry_count}
                    </span>
                  )}
                </div>
                
                <div className="mt-1 text-sm text-gray-600">
                  Batch ID: <span className="font-mono">{load.batch_id}</span>
                </div>
                
                <div className="mt-2 flex items-start gap-2">
                  <span className="text-xs text-red-600 font-medium">
                    Failure Reason:
                  </span>
                  <span className="text-xs text-red-900">
                    {load.failure_reason}
                  </span>
                </div>
                
                <div className="mt-1 text-xs text-gray-500">
                  Failed at: {formatDateTime(load.load_failed_at)}
                </div>
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => toggleExpand(load.id)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  {expandedIds.has(load.id) ? 'Hide Details' : 'Show Details'}
                </button>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedIds.has(load.id) && (
              <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-3">
                {/* Error Message */}
                {load.error_message && (
                  <div>
                    <div className="text-xs font-medium text-gray-700 mb-1">
                      Error Message:
                    </div>
                    <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                      {load.error_message}
                    </pre>
                  </div>
                )}

                {/* Record Counts */}
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-xs text-gray-600">Source Records</div>
                    <div className="text-sm font-medium text-gray-900">
                      {load.source_record_count?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Warehouse Records</div>
                    <div className="text-sm font-medium text-gray-900">
                      {load.warehouse_record_count?.toLocaleString() || '-'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-600">Failed Records</div>
                    <div className="text-sm font-medium text-red-600">
                      {load.failed_record_count?.toLocaleString() || '-'}
                    </div>
                  </div>
                </div>

                {/* Validation Info */}
                {load.retry_validated_at && (
                  <div className="text-xs text-gray-600">
                    Validated by {load.retry_validated_by} at{' '}
                    {formatDateTime(load.retry_validated_at)}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-gray-200">
                  {!load.can_retry && onValidateRetry && (
                    <button
                      onClick={() => onValidateRetry(load.batch_id)}
                      className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                      disabled={load.retry_count >= 3}
                    >
                      Validate for Retry
                    </button>
                  )}
                  
                  {load.can_retry && onRevokeRetry && (
                    <button
                      onClick={() => onRevokeRetry(load.batch_id)}
                      className="px-3 py-1.5 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700"
                    >
                      Revoke Retry Approval
                    </button>
                  )}
                  
                  {onViewDetails && (
                    <button
                      onClick={() => onViewDetails(load)}
                      className="px-3 py-1.5 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      View Full Details
                    </button>
                  )}
                  
                  {load.retry_count >= 3 && (
                    <div className="flex items-center px-3 py-1.5 text-xs text-red-600 bg-red-50 rounded">
                      ⚠ Maximum retry attempts reached
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FailedLoadSection;
