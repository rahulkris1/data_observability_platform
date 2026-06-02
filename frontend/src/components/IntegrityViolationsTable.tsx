import React, { useState, useMemo } from 'react';
import ValidationStatusBadge, { ValidationStatus } from './ValidationStatusBadge';

export interface IntegrityViolation {
  id: number;
  datasetName: string;
  validationType: string;
  violationType: string;
  status: ValidationStatus;
  failedRecords: number;
  failureReason: string;
  failureDetails: Record<string, any>;
  executedAt: string;
  executionTimeMs?: number;
}

export interface FailedRow {
  rowData: Record<string, any>;
  failureType: string;
  failureDetails: Record<string, any>;
}

export interface IntegrityViolationsTableProps {
  violations: IntegrityViolation[];
  failedRows?: FailedRow[];
  onRowClick?: (violation: IntegrityViolation) => void;
  loading?: boolean;
}

type SortField = 'validationType' | 'executedAt' | 'failedRecords' | 'datasetName';
type SortDirection = 'asc' | 'desc';

export default function IntegrityViolationsTable({
  violations,
  failedRows = [],
  onRowClick,
  loading = false
}: IntegrityViolationsTableProps) {
  const [expandedRowId, setExpandedRowId] = useState<number | null>(null);
  const [sortField, setSortField] = useState<SortField>('executedAt');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  
  // Filters
  const [datasetFilter, setDatasetFilter] = useState<string>('');
  const [validationTypeFilter, setValidationTypeFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<string>('');

  // Get unique values for filter dropdowns
  const uniqueDatasets = useMemo(() => {
    return Array.from(new Set(violations.map(v => v.datasetName))).sort();
  }, [violations]);

  const uniqueValidationTypes = useMemo(() => {
    return Array.from(new Set(violations.map(v => v.validationType))).sort();
  }, [violations]);

  const uniqueStatuses = useMemo(() => {
    return Array.from(new Set(violations.map(v => v.status))).sort();
  }, [violations]);

  // Apply filters
  const filteredViolations = useMemo(() => {
    return violations.filter(violation => {
      if (datasetFilter && violation.datasetName !== datasetFilter) return false;
      if (validationTypeFilter && violation.validationType !== validationTypeFilter) return false;
      if (statusFilter && violation.status !== statusFilter) return false;
      if (dateFilter) {
        const violationDate = new Date(violation.executedAt).toISOString().split('T')[0];
        if (violationDate !== dateFilter) return false;
      }
      return true;
    });
  }, [violations, datasetFilter, validationTypeFilter, statusFilter, dateFilter]);

  // Apply sorting
  const sortedViolations = useMemo(() => {
    const sorted = [...filteredViolations];
    sorted.sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];

      if (sortField === 'executedAt') {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [filteredViolations, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleRowExpansion = (id: number) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  const clearFilters = () => {
    setDatasetFilter('');
    setValidationTypeFilter('');
    setStatusFilter('');
    setDateFilter('');
  };

  const hasActiveFilters = datasetFilter || validationTypeFilter || statusFilter || dateFilter;

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="animate-pulse p-4">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-100 rounded mb-2"></div>
          ))}
        </div>
      </div>
    );
  }

  if (violations.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No integrity violations found</h3>
          <p className="mt-1 text-sm text-gray-500">All referential integrity checks are passing.</p>
        </div>
      </div>
    );
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return (
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }
    return sortDirection === 'asc' ? (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filters Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-700">Filters</h3>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear All
            </button>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Dataset Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Dataset</label>
            <select
              value={datasetFilter}
              onChange={(e) => setDatasetFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Datasets</option>
              {uniqueDatasets.map(dataset => (
                <option key={dataset} value={dataset}>{dataset}</option>
              ))}
            </select>
          </div>

          {/* Validation Type Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Validation Type</label>
            <select
              value={validationTypeFilter}
              onChange={(e) => setValidationTypeFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              {uniqueValidationTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Date Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Execution Date</label>
            <input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('datasetName')}
                    className="flex items-center space-x-1 hover:text-gray-700"
                  >
                    <span>Dataset</span>
                    <SortIcon field="datasetName" />
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('validationType')}
                    className="flex items-center space-x-1 hover:text-gray-700"
                  >
                    <span>Validation Type</span>
                    <SortIcon field="validationType" />
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('failedRecords')}
                    className="flex items-center justify-end space-x-1 hover:text-gray-700 ml-auto"
                  >
                    <span>Failed Records</span>
                    <SortIcon field="failedRecords" />
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Failure Reason
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <button
                    onClick={() => handleSort('executedAt')}
                    className="flex items-center space-x-1 hover:text-gray-700"
                  >
                    <span>Executed At</span>
                    <SortIcon field="executedAt" />
                  </button>
                </th>
                <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Details
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedViolations.map((violation) => {
                const isExpanded = expandedRowId === violation.id;
                const isClickable = !!onRowClick;

                return (
                  <React.Fragment key={violation.id}>
                    <tr
                      className={`
                        ${isClickable ? 'cursor-pointer hover:bg-gray-50' : ''}
                        transition-colors duration-150
                      `}
                      onClick={isClickable ? () => onRowClick(violation) : undefined}
                    >
                      {/* Dataset Name */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {violation.datasetName}
                        </div>
                        <div className="text-xs text-gray-500">
                          {violation.violationType}
                        </div>
                      </td>

                      {/* Validation Type */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                          {violation.validationType}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <ValidationStatusBadge status={violation.status} size="sm" />
                      </td>

                      {/* Failed Records */}
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <span className="text-sm font-semibold text-red-600">
                          {violation.failedRecords.toLocaleString()}
                        </span>
                      </td>

                      {/* Failure Reason */}
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 max-w-md truncate">
                          {violation.failureReason}
                        </div>
                      </td>

                      {/* Executed At */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(violation.executedAt).toLocaleDateString()}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(violation.executedAt).toLocaleTimeString()}
                        </div>
                      </td>

                      {/* Expand Button */}
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleRowExpansion(violation.id);
                          }}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          {isExpanded ? (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Expanded Row Details */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={7} className="px-6 py-4 bg-gray-50">
                          <div className="space-y-4">
                            <div>
                              <h4 className="text-sm font-semibold text-gray-900 mb-2">Failure Details</h4>
                              <pre className="text-xs bg-white p-3 rounded border border-gray-200 overflow-x-auto">
                                {JSON.stringify(violation.failureDetails, null, 2)}
                              </pre>
                            </div>
                            
                            {violation.executionTimeMs && (
                              <div>
                                <span className="text-xs text-gray-600">
                                  Execution Time: <span className="font-medium">{violation.executionTimeMs.toFixed(2)}ms</span>
                                </span>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Summary Footer */}
        <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-700">
              <span className="font-medium">{sortedViolations.length}</span> violation(s)
              {hasActiveFilters && ` (filtered from ${violations.length} total)`}
            </span>
            <div className="flex items-center space-x-4 text-gray-600">
              <span>
                Total Failed Records: <span className="font-medium text-red-600">
                  {sortedViolations.reduce((sum, v) => sum + v.failedRecords, 0).toLocaleString()}
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Failed Records Section */}
      {failedRows.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="px-6 py-4 bg-red-50 border-b border-red-200">
            <h3 className="text-sm font-semibold text-red-900">
              Failed Records ({failedRows.length})
            </h3>
            <p className="text-xs text-red-700 mt-1">
              Rows that failed integrity validation
            </p>
          </div>
          <div className="overflow-x-auto max-h-96">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Failure Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Row Data
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {failedRows.map((row, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {row.failureType}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <pre className="text-xs text-gray-700 overflow-x-auto max-w-2xl">
                        {JSON.stringify(row.rowData, null, 2)}
                      </pre>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
