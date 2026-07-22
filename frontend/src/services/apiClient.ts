import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import type { ApiResponse, ApiError } from './types';

// API base URL from environment variables
// Empty string uses Next.js proxy (relative URLs), otherwise uses direct URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || '/api/v1';

// Log configuration in development
if (process.env.NODE_ENV === 'development') {
  console.log('API Configuration:', {
    baseURL: API_BASE_URL ? `${API_BASE_URL}${API_VERSION}` : API_VERSION,
    mode: API_BASE_URL ? 'Direct connection' : 'Next.js proxy',
    environment: process.env.NODE_ENV,
  });
}

/**
 * Standard API response from backend
 */
interface StandardResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  timestamp?: string;
  // Error fields
  error?: string;
  error_code?: string;
  details?: Array<{
    field?: string;
    message: string;
    type?: string;
  }>;
  trace_id?: string;
  path?: string;
}

/**
 * Axios client instance with default configuration
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL ? `${API_BASE_URL}${API_VERSION}` : API_VERSION,
  timeout: 30000, // Increased timeout to 30 seconds for slower connections
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor
 * Add any auth tokens or custom headers here
 */
apiClient.interceptors.request.use(
  (config) => {
    // Add JWT token to requests if available
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor
 * Handle standardized API responses and common error cases
 */
apiClient.interceptors.response.use(
  (response) => {
    // Extract data from standardized response
    const standardResponse = response.data as StandardResponse;
    
    // Debug logging
    if (process.env.NODE_ENV === 'development') {
      console.log('API Response:', {
        url: response.config.url,
        status: response.status,
        success: standardResponse.success,
        hasData: standardResponse.data !== undefined
      });
    }
    
    if (standardResponse.success === false) {
      // Backend returned an error in successful HTTP response
      return Promise.reject({
        response: {
          data: standardResponse,
          status: response.status,
        },
        message: standardResponse.error || 'An error occurred',
      });
    }
    
    // Return the data field from standardized response
    if (standardResponse.data !== undefined) {
      response.data = standardResponse.data;
    }
    
    return response;
  },
  (error: AxiosError<StandardResponse>) => {
    // Handle errors
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;
      
      // Log errors with trace_id if available
      const traceId = data?.trace_id;
      const errorMsg = data?.error || error.message;
      
      if (traceId) {
        console.error(`[${traceId}] API error (${status}):`, errorMsg);
      } else {
        console.error(`API error (${status}):`, errorMsg);
      }
      
      // Handle specific status codes
      switch (status) {
        case 401:
          // Handle unauthorized - clear token and redirect to login
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            // Optional: redirect to login page
            // window.location.href = '/login';
          }
          break;
        case 403:
          console.error('Forbidden access');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 422:
          // Validation errors
          console.error('Validation error:', data?.details);
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          console.error('Server error');
          break;
      }
    } else if (error.request) {
      // Network error - no response received
      console.error('Network error - no response received');
    } else {
      // Other errors
      console.error('Error setting up request:', error.message);
    }
    
    return Promise.reject(error);
  }
);

/**
 * Retry configuration
 */
interface RetryConfig {
  maxRetries?: number;
  retryDelay?: number;
  retryableStatuses?: number[];
}

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  retryDelay: 1000,
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Helper function to delay execution
 */
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Generic API request wrapper with retry logic
 */
async function apiRequestWithRetry<T = any>(
  requestFn: () => Promise<any>,
  retryConfig: RetryConfig = {}
): Promise<T> {
  const config = { ...DEFAULT_RETRY_CONFIG, ...retryConfig };
  let lastError: any;

  for (let attempt = 0; attempt <= (config.maxRetries || 0); attempt++) {
    try {
      const response = await requestFn();
      return response.data as T;
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        const isRetryable = status && config.retryableStatuses?.includes(status);
        const hasRetriesLeft = attempt < (config.maxRetries || 0);

        if (isRetryable && hasRetriesLeft) {
          console.log(`Retrying request (attempt ${attempt + 1}/${config.maxRetries})...`);
          await delay((config.retryDelay || 1000) * (attempt + 1)); // Exponential backoff
          continue;
        }
      }

      // Not retryable or no retries left
      break;
    }
  }

  throw lastError;
}

/**
 * Generic API request wrapper
 */
export const apiRequest = {
  get: <T = any>(url: string, config?: AxiosRequestConfig & { retry?: RetryConfig }) =>
    apiRequestWithRetry<T>(
      () => apiClient.get(url, config),
      config?.retry
    ),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig & { retry?: RetryConfig }) =>
    apiRequestWithRetry<T>(
      () => apiClient.post(url, data, config),
      config?.retry
    ),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig & { retry?: RetryConfig }) =>
    apiRequestWithRetry<T>(
      () => apiClient.put(url, data, config),
      config?.retry
    ),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig & { retry?: RetryConfig }) =>
    apiRequestWithRetry<T>(
      () => apiClient.patch(url, data, config),
      config?.retry
    ),

  delete: <T = any>(url: string, config?: AxiosRequestConfig & { retry?: RetryConfig }) =>
    apiRequestWithRetry<T>(
      () => apiClient.delete(url, config),
      config?.retry
    ),
};

/**
 * Helper function to handle API errors
 */
export function handleApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<StandardResponse>;
    const data = axiosError.response?.data;
    
    return {
      message: data?.error || axiosError.message || 'An error occurred',
      status: axiosError.response?.status || 500,
      errors: data?.details?.reduce((acc, detail) => {
        if (detail.field) {
          acc[detail.field] = [detail.message];
        }
        return acc;
      }, {} as Record<string, string[]>),
    };
  }

  return {
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
    status: 500,
  };
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    return !error.response && !!error.request;
  }
  return false;
}

/**
 * Get error message from any error type
 */
export function getErrorMessage(error: unknown): string {
  const apiError = handleApiError(error);
  return apiError.message;
}

/**
 * Get trace ID from error response
 */
export function getTraceId(error: unknown): string | undefined {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as StandardResponse;
    return data?.trace_id;
  }
  return undefined;
}

export default apiClient;
