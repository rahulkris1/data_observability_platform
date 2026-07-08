import React from 'react';

export interface FallbackUIProps {
  /**
   * Type of error state to display
   */
  type?: 'error' | 'empty' | 'loading' | 'network' | 'notfound';
  
  /**
   * Title of the error message
   */
  title?: string;
  
  /**
   * Description or additional context
   */
  description?: string;
  
  /**
   * Error object for detailed error information
   */
  error?: Error | null;
  
  /**
   * Show retry button
   */
  showRetry?: boolean;
  
  /**
   * Retry action callback
   */
  onRetry?: () => void;
  
  /**
   * Custom action button
   */
  action?: {
    label: string;
    onClick: () => void;
  };
  
  /**
   * Show technical details (for debugging)
   */
  showDetails?: boolean;
}

/**
 * FallbackUI Component
 * 
 * Displays user-friendly error messages, empty states, and loading states
 */
export default function FallbackUI({
  type = 'error',
  title,
  description,
  error,
  showRetry = false,
  onRetry,
  action,
  showDetails = false,
}: FallbackUIProps) {
  // Default messages for each type
  const defaults = {
    error: {
      title: 'Something went wrong',
      description: 'An unexpected error occurred. Please try again later.',
      icon: (
        <svg className="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
    empty: {
      title: 'No data available',
      description: 'There is no data to display at the moment.',
      icon: (
        <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      ),
    },
    loading: {
      title: 'Loading...',
      description: 'Please wait while we fetch your data.',
      icon: (
        <svg
          className="animate-spin w-12 h-12 text-blue-500"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ),
    },
    network: {
      title: 'Connection error',
      description: 'Unable to connect to the server. Please check your internet connection.',
      icon: (
        <svg className="w-12 h-12 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
          />
        </svg>
      ),
    },
    notfound: {
      title: 'Page not found',
      description: 'The page you are looking for does not exist.',
      icon: (
        <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
  };

  const config = defaults[type];
  const displayTitle = title || config.title;
  const displayDescription = description || config.description;

  return (
    <div className="flex items-center justify-center min-h-[400px] p-8">
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="flex justify-center mb-4">{config.icon}</div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{displayTitle}</h3>

        {/* Description */}
        <p className="text-gray-600 mb-6">{displayDescription}</p>

        {/* Error details (for debugging) */}
        {showDetails && error && (
          <div className="mb-6 p-4 bg-gray-100 rounded-lg text-left">
            <p className="text-sm font-mono text-gray-700 break-all">
              {error.message}
            </p>
            {error.stack && (
              <details className="mt-2">
                <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                  Stack trace
                </summary>
                <pre className="text-xs text-gray-600 mt-2 overflow-auto max-h-40">
                  {error.stack}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-center gap-3">
          {showRetry && onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Try again
            </button>
          )}

          {action && (
            <button
              onClick={action.onClick}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {action.label}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * LoadingState Component
 * Simple loading indicator
 */
export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return <FallbackUI type="loading" description={message} />;
}

/**
 * EmptyState Component
 * Display when there's no data
 */
export function EmptyState({ 
  message = 'No data available',
  action
}: { 
  message?: string;
  action?: FallbackUIProps['action'];
}) {
  return <FallbackUI type="empty" description={message} action={action} />;
}

/**
 * ErrorState Component
 * Display error with retry option
 */
export function ErrorState({
  error,
  onRetry,
}: {
  error?: Error | null;
  onRetry?: () => void;
}) {
  return (
    <FallbackUI
      type="error"
      error={error}
      showRetry={!!onRetry}
      onRetry={onRetry}
      showDetails={process.env.NODE_ENV === 'development'}
    />
  );
}
