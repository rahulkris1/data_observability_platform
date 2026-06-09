/**
 * Application Logs Page
 * 
 * Displays application logs with filtering, search, and auto-refresh capabilities
 */

import React, { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import LogsTable, { LogFilters } from '../components/LogsTable';
import {
  getLogs,
  getLogStatistics,
  LogEntry,
  LogStatistics,
} from '../services/observabilityService';

export default function Logs() {
  // State management
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize] = useState<number>(100);
  const [statistics, setStatistics] = useState<LogStatistics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Filter state
  const [filters, setFilters] = useState<LogFilters>({
    level: '',
    logger: '',
    search: '',
    start_date: '',
    end_date: '',
  });

  // Fetch logs
  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
        level: filters.level || undefined,
        logger: filters.logger || undefined,
        search: filters.search || undefined,
        start_date: filters.start_date ? new Date(filters.start_date).toISOString() : undefined,
        end_date: filters.end_date ? new Date(filters.end_date).toISOString() : undefined,
      };

      // Remove undefined values
      Object.keys(params).forEach((key) => {
        if (params[key as keyof typeof params] === undefined) {
          delete params[key as keyof typeof params];
        }
      });

      const response = await getLogs(params);
      setLogs(response.logs);
      setTotalCount(response.total);
    } catch (err) {
      console.error('Error fetching logs:', err);
      setError('Failed to load logs. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters]);

  // Fetch statistics
  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await getLogStatistics();
      setStatistics(stats);
    } catch (err) {
      console.error('Error fetching statistics:', err);
    }
  }, []);

  // Fetch logs when filters or page changes
  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Fetch statistics on mount
  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchLogs();
        fetchStatistics();
      }, 10000); // Refresh every 10 seconds
      setRefreshInterval(interval);

      return () => {
        if (interval) clearInterval(interval);
      };
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }
  }, [autoRefresh, fetchLogs, fetchStatistics]);

  const handleFilterChange = (newFilters: LogFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleRefresh = () => {
    fetchLogs();
    fetchStatistics();
  };

  const handleAutoRefreshToggle = () => {
    setAutoRefresh(!autoRefresh);
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    const totalPages = Math.ceil(totalCount / pageSize);
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Application Logs</h1>
          <p className="mt-2 text-sm text-gray-600">
            View and search application logs with real-time monitoring
          </p>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Logs</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">
                {statistics.total_lines.toLocaleString()}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">File Size</h3>
              <p className="mt-2 text-3xl font-semibold text-gray-900">
                {formatFileSize(statistics.file_size_bytes)}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Error Count</h3>
              <p className="mt-2 text-3xl font-semibold text-red-600">
                {((statistics.levels.ERROR || 0) + (statistics.levels.CRITICAL || 0)).toLocaleString()}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Warning Count</h3>
              <p className="mt-2 text-3xl font-semibold text-yellow-600">
                {(statistics.levels.WARNING || 0).toLocaleString()}
              </p>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Logs Table */}
        <LogsTable
          logs={logs}
          loading={loading}
          onFilterChange={handleFilterChange}
          onRefresh={handleRefresh}
          autoRefresh={autoRefresh}
          onAutoRefreshToggle={handleAutoRefreshToggle}
        />

        {/* Pagination */}
        {totalCount > 0 && (
          <div className="bg-white px-4 py-3 rounded-lg shadow flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing page <span className="font-medium">{currentPage}</span> of{' '}
              <span className="font-medium">{totalPages}</span> ({totalCount} total logs)
            </div>
            <div className="flex gap-2">
              <button
                onClick={handlePreviousPage}
                disabled={currentPage === 1}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
