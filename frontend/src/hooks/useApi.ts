import { useState, useCallback } from 'react';
import { useToast } from '../contexts/ToastContext';
import { handleApiError, isNetworkError, getErrorMessage, getTraceId } from '../services/apiClient';

export interface UseApiOptions {
  /**
   * Show success toast on successful request
   */
  showSuccessToast?: boolean;
  
  /**
   * Success message to display
   */
  successMessage?: string;
  
  /**
   * Show error toast on failed request
   */
  showErrorToast?: boolean;
  
  /**
   * Custom error message
   */
  errorMessage?: string;
  
  /**
   * Enable retry prompt for failed requests
   */
  enableRetry?: boolean;
  
  /**
   * Callback on success
   */
  onSuccess?: (data: any) => void;
  
  /**
   * Callback on error
   */
  onError?: (error: any) => void;
}

export interface UseApiState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  retry: () => Promise<void>;
}

/**
 * Custom hook for handling API requests with loading, error states, and retry logic
 */
export function useApi<T = any>(
  apiFunction: (...args: any[]) => Promise<T>,
  options: UseApiOptions = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);
  const { showSuccess, showError } = useToast();
  
  // Store the last arguments for retry functionality
  const [lastArgs, setLastArgs] = useState<any[]>([]);

  const execute = useCallback(
    async (...args: any[]) => {
      setLoading(true);
      setError(null);
      setLastArgs(args);

      try {
        const result = await apiFunction(...args);
        setData(result);
        
        // Show success toast if enabled
        if (options.showSuccessToast) {
          showSuccess(options.successMessage || 'Operation completed successfully');
        }
        
        // Call success callback
        options.onSuccess?.(result);
        
        return result;
      } catch (err: any) {
        const errorObj = err instanceof Error ? err : new Error('An error occurred');
        setError(errorObj);
        
        // Handle error toast
        if (options.showErrorToast !== false) {
          const errorMsg = options.errorMessage || getErrorMessage(err);
          const traceId = getTraceId(err);
          const description = traceId ? `Trace ID: ${traceId}` : undefined;
          
          // Show retry prompt if enabled
          if (options.enableRetry) {
            showError(
              errorMsg,
              description,
              {
                label: 'Retry',
                onClick: () => retry(),
              }
            );
          } else {
            showError(errorMsg, description);
          }
        }
        
        // Call error callback
        options.onError?.(err);
        
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [apiFunction, options, showSuccess, showError]
  );

  const retry = useCallback(async () => {
    if (lastArgs.length > 0) {
      return execute(...lastArgs);
    }
    return execute();
  }, [execute, lastArgs]);

  return {
    data,
    error,
    loading,
    execute,
    retry,
  };
}

/**
 * Hook for managing async data fetching with loading, error, and empty states
 */
export function useAsyncData<T = any>(
  fetchFunction: () => Promise<T>,
  dependencies: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [isEmpty, setIsEmpty] = useState(false);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchFunction();
      setData(result);
      
      // Check if result is empty
      if (Array.isArray(result)) {
        setIsEmpty(result.length === 0);
      } else if (typeof result === 'object' && result !== null) {
        setIsEmpty(Object.keys(result).length === 0);
      } else {
        setIsEmpty(!result);
      }
    } catch (err: any) {
      const errorObj = err instanceof Error ? err : new Error('Failed to fetch data');
      setError(errorObj);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction]);

  return {
    data,
    error,
    loading,
    isEmpty,
    refetch,
  };
}

/**
 * Hook for form submission with loading and error handling
 */
export function useFormSubmit<T = any>(
  submitFunction: (formData: any) => Promise<T>,
  options: UseApiOptions = {}
) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const { showSuccess, showError } = useToast();

  const submit = useCallback(
    async (formData: any) => {
      setSubmitting(true);
      setError(null);

      try {
        const result = await submitFunction(formData);
        
        // Show success toast
        if (options.showSuccessToast !== false) {
          showSuccess(options.successMessage || 'Form submitted successfully');
        }
        
        // Call success callback
        options.onSuccess?.(result);
        
        return result;
      } catch (err: any) {
        const errorObj = err instanceof Error ? err : new Error('Submission failed');
        setError(errorObj);
        
        // Show error toast
        if (options.showErrorToast !== false) {
          const errorMsg = options.errorMessage || getErrorMessage(err);
          const traceId = getTraceId(err);
          const description = traceId ? `Trace ID: ${traceId}` : undefined;
          
          showError(errorMsg, description);
        }
        
        // Call error callback
        options.onError?.(err);
        
        throw err;
      } finally {
        setSubmitting(false);
      }
    },
    [submitFunction, options, showSuccess, showError]
  );

  return {
    submit,
    submitting,
    error,
  };
}
