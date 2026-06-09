/**
 * LogsTable Component
 * 
 * Displays application logs in a table with filtering and search capabilities
 */

import React, { useState } from 'react';
import { LogEntry } from '../services/observabilityService';

interface LogsTableProps {
  logs: LogEntry[];
  loading: boolean;
  onFilterChange: (filters: LogFilters) => void;
  onRefresh: () => void;
  autoRefresh: boolean;
  onAutoRefreshToggle: () => void;
}

export interface LogFilters {
  level?: string;
  logger?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
}

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

const LogsTable: React.FC<LogsTableProps> = ({
  logs,
  loading,
  onFilterChange,
  onRefresh,
  autoRefresh,
  onAutoRefreshToggle,
}) => {
  const [filters, setFilters] = useState<LogFilters>({
    level: '',
    logger: '',
    search: '',
    start_date: '',
    end_date: '',
  });

  const handleFilterChange = (field: keyof LogFilters, value: string) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const emptyFilters: LogFilters = {
      level: '',
      logger: '',
      search: '',
      start_date: '',
      end_date: '',
    };
    setFilters(emptyFilters);
    onFilterChange(emptyFilters);
  };

  const getLevelColor = (level: string): string => {
    switch (level.toUpperCase()) {
      case 'DEBUG':
        return 'text-gray-600 bg-gray-100';
      case 'INFO':
        return 'text-blue-600 bg-blue-100';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-100';
      case 'ERROR':
        return 'text-red-600 bg-red-100';
      case 'CRITICAL':
        return 'text-red-800 bg-red-200';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  // Get unique loggers from current logs
  const uniqueLoggers = Array.from(new Set(logs.map((log) => log.logger))).sort();

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-4">
          {/* Log Level Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Log Level
            </label>
            <select
              value={filters.level || ''}
              onChange={(e) => handleFilterChange('level', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Levels</option>
              {LOG_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>

          {/* Service/Logger Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Service
            </label>
            <select
              value={filters.logger || ''}
              onChange={(e) => handleFilterChange('logger', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Services</option>
              {uniqueLoggers.map((logger) => (
                <option key={logger} value={logger}>
                  {logger}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              type="datetime-local"
              value={filters.start_date || ''}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* End Date Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              type="datetime-local"
              value={filters.end_date || ''}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Search Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Message
            </label>
            <input
              type="text"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              placeholder="Search in messages..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Reset Filters
          </button>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button
            onClick={onAutoRefreshToggle}
            className={`px-4 py-2 rounded-md transition-colors ${
              autoRefresh
                ? 'bg-green-600 text-white hover:bg-green-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Auto-Refresh: {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          {loading && logs.length === 0 ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col justify-center items-center h-64 text-gray-500">
              <svg
                className="h-16 w-16 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <p className="text-lg font-medium">No logs found</p>
              <p className="text-sm">Try adjusting your filters or check back later</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Service
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Message
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${getLevelColor(
                          log.level
                        )}`}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.logger}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-3xl">
                        <p className="break-words">{log.message}</p>
                        {log.extra_fields && Object.keys(log.extra_fields).length > 0 && (
                          <details className="mt-2">
                            <summary className="cursor-pointer text-xs text-blue-600 hover:text-blue-800">
                              View Details
                            </summary>
                            <pre className="mt-2 p-2 bg-gray-50 rounded text-xs overflow-auto max-h-40">
                              {JSON.stringify(log.extra_fields, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsTable;
