/**
 * Example: Using error handling with API requests
 * 
 * This file demonstrates how to use the error handling system
 * with API requests, including:
 * - Loading states
 * - Error states with retry
 * - Success notifications
 * - Empty states
 */

import React, { useEffect } from 'react';
import { useToast } from '../contexts/ToastContext';
import { useApi, useAsyncData, useFormSubmit } from '../hooks/useApi';
import { LoadingState, EmptyState, ErrorState } from '../components/FallbackUI';
import { apiRequest } from '../services/apiClient';

/**
 * Example 1: Simple API call with toast notifications
 */
export function ExampleWithToast() {
  const { showSuccess, showError, showInfo } = useToast();

  const handleAction = async () => {
    try {
      showInfo('Processing...');
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      showSuccess('Operation completed successfully!');
    } catch (error) {
      showError('Operation failed', 'Please try again later');
    }
  };

  return (
    <div>
      <button onClick={handleAction}>Execute Action</button>
    </div>
  );
}

/**
 * Example 2: Using useApi hook with automatic error handling
 */
export function ExampleWithUseApi() {
  const fetchData = async (id: string) => {
    return apiRequest.get(`/resource/${id}`);
  };

  const { data, loading, error, execute, retry } = useApi(fetchData, {
    showSuccessToast: true,
    successMessage: 'Data loaded successfully',
    enableRetry: true,
  });

  useEffect(() => {
    execute('123');
  }, []);

  if (loading) return <LoadingState message="Loading data..." />;
  if (error) return <ErrorState error={error} onRetry={retry} />;
  if (!data) return <EmptyState message="No data available" />;

  return <div>{JSON.stringify(data)}</div>;
}

/**
 * Example 3: Using useAsyncData for data fetching
 */
export function ExampleWithAsyncData() {
  const fetchItems = async () => {
    return apiRequest.get('/items');
  };

  const { data, loading, error, isEmpty, refetch } = useAsyncData(fetchItems);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (isEmpty) {
    return (
      <EmptyState
        message="No items found"
        action={{
          label: 'Create New Item',
          onClick: () => console.log('Create item'),
        }}
      />
    );
  }

  return (
    <div>
      {/* Render items */}
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}

/**
 * Example 4: Form submission with error handling
 */
export function ExampleFormSubmit() {
  const submitForm = async (formData: any) => {
    return apiRequest.post('/submit', formData);
  };

  const { submit, submitting, error } = useFormSubmit(submitForm, {
    showSuccessToast: true,
    successMessage: 'Form submitted successfully',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await submit({ name: 'Test' });
      // Handle success (e.g., redirect)
    } catch (error) {
      // Error is already handled by the hook
      console.error('Submission failed:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="name" />
      <button type="submit" disabled={submitting}>
        {submitting ? 'Submitting...' : 'Submit'}
      </button>
      {error && <p className="text-red-600">{error.message}</p>}
    </form>
  );
}

/**
 * Example 5: Manual retry with toast action
 */
export function ExampleManualRetry() {
  const { showError } = useToast();

  const fetchData = async () => {
    try {
      return await apiRequest.get('/data', {
        retry: {
          maxRetries: 3,
          retryDelay: 1000,
        },
      });
    } catch (error) {
      showError(
        'Failed to fetch data',
        'The server is not responding',
        {
          label: 'Try Again',
          onClick: () => fetchData(),
        }
      );
      throw error;
    }
  };

  return (
    <div>
      <button onClick={fetchData}>Fetch Data</button>
    </div>
  );
}
