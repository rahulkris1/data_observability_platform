/**
 * Failed Pipeline Section Component
 * Displays failed validations with retry functionality
 */
import React, { useState, useEffect } from 'react';
import { retryService, type FailedValidation } from '../services/retryService';
import { LoadingSpinner } from './LoadingSpinner';
import { Alert } from './Alert';
import { useAuth } from '@/hooks/useAuth';

interface FailedPipelineSectionProps {
  datasetName?: string;
  validationType?: string;
  onRetryCreated?: (validationId: number) => void;
}

const FailedPipelineSection: React.FC<FailedPipelineSectionProps> = ({
  datasetName,
  validationType,
  onRetryCreated,
}) => {
  const [failedValidations, setFailedValidations] = useState<FailedValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryingIds, setRetryingIds] = useState<Set<number>>(new Set());
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const { userEmail } = useAuth();
  const currentUser = userEmail || 'anonymous';

  useEffect(() => {
    loadFailedValidations();
  }, [datasetName, validationType]);

  const loadFailedValidations = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await retryService.getFailedValidations(
        datasetName,
        validationType,
        100
      );
      setFailedValidations(response.validations);
    } catch (err: any) {
      setError(err.message || 'Failed to load failed validations');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (validation: FailedValidation) => {
    try {
      setRetryingIds(new Set(retryingIds).add(validation.validation_log_id));
      
      const retryRequest = await retryService.createRetryRequest({
        validation_log_id: validation.validation_log_id,
        initiated_by: currentUser,
        retry_reason: 'Manual retry from UI',
        max_retries: 3,
      });

      // Execute the retry immediately
      await retryService.executeRetry(retryRequest.retry_id, {
        executor: currentUser,
      });

      if (onRetryCreated) {
        onRetryCreated(validation.validation_log_id);
      }

      // Reload the list
      await loadFailedValidations();
    } catch (err: any) {
      setError(err.message || 'Failed to create retry');
    } finally {
      setRetryingIds((prev) => {
        const next = new Set(prev);
        next.delete(validation.validation_log_id);
        return next;
      });
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

  const formatDateTime = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'error':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return <Alert variant="error" message={error} onClose={() => setError(null)} />;
  }

  if (failedValidations.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Failed Validations</h3>
        <p className="text-gray-600">All validations are passing successfully!</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Failed Validations</h3>
            <p className="text-sm text-gray-600 mt-1">
              {failedValidations.length} validation{failedValidations.length !== 1 ? 's' : ''} requiring attention
            </p>
          </div>
          <button
            onClick={loadFailedValidations}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Failed Validations List */}
      <div className="space-y-3">
        {failedValidations.map((validation) => {
          const isExpanded = expandedIds.has(validation.validation_log_id);
          const isRetrying = retryingIds.has(validation.validation_log_id);

          return (
            <div
              key={validation.validation_log_id}
              className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden"
            >
              {/* Header */}
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <h4 className="text-lg font-medium text-gray-900 truncate">
                        {validation.dataset_name}
                      </h4>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(
                          validation.status
                        )}`}
                      >
                        {validation.status.toUpperCase()}
                      </span>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                        {validation.validation_type}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-600">{validation.message}</p>
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                      <span>Validator: {validation.validator_name}</span>
                      <span>•</span>
                      <span>Failed: {validation.failed_records} / {validation.total_records} records</span>
                      <span>•</span>
                      <span>Pass Rate: {validation.pass_rate.toFixed(2)}%</span>
                      <span>•</span>
                      <span>{formatDateTime(validation.created_at)}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleRetry(validation)}
                      disabled={isRetrying}
                      className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                        isRetrying
                          ? 'bg-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      {isRetrying ? (
                        <>
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Retrying...
                        </>
                      ) : (
                        <>
                          <svg className="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Retry
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => toggleExpand(validation.validation_log_id)}
                      className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {isExpanded ? 'Hide Details' : 'Show Details'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t border-gray-200 bg-gray-50 px-4 py-3">
                  <h5 className="text-sm font-medium text-gray-900 mb-2">Error Details</h5>
                  {validation.errors && validation.errors.length > 0 ? (
                    <ul className="space-y-1">
                      {validation.errors.map((error, idx) => (
                        <li key={idx} className="text-sm text-red-600">
                          • {error}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-600">No specific error details available.</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default FailedPipelineSection;
