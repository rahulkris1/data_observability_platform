/**
 * API Response types
 */
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
}

export interface ApiError {
  message: string;
  status: number;
  errors?: Record<string, string[]>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Common API parameters
 */
export interface PaginationParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface FilterParams {
  search?: string;
  [key: string]: any;
}

/**
 * Validation types
 */
export interface ValidationMetrics {
  total_validations: number;
  passed_validations: number;
  failed_validations: number;
  warning_validations: number;
  average_pass_rate: number;
}

export interface DatasetStatistics {
  dataset_name: string;
  row_count: number;
  column_count: number;
  validation_score: number;
  last_validated?: string | null;
}

export interface ValidationHistoryItem {
  id: number;
  dataset_name: string;
  validation_type: string;
  status: string;
  executed_at: string;
  execution_time_ms?: number;
  total_records: number;
  failed_records: number;
  pass_rate: number;
}

export interface ValidationFilters {
  datasetName?: string;
  validationType?: string;
  status?: string;
}

export type ValidationStatus = 'passed' | 'failed' | 'warning' | 'error';
