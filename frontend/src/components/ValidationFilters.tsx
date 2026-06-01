import React, { useState } from 'react';

export interface ValidationFilters {
  datasetName?: string;
  validationType?: string;
  status?: string;
}

export interface ValidationFiltersProps {
  filters: ValidationFilters;
  onFiltersChange: (filters: ValidationFilters) => void;
  availableDatasets?: string[];
  availableTypes?: string[];
  availableStatuses?: string[];
}

const DEFAULT_TYPES = ['schema', 'null', 'datatype', 'checksum', 'column_existence', 'aggregated'];
const DEFAULT_STATUSES = ['passed', 'failed', 'warning', 'error'];

export default function ValidationFiltersComponent({
  filters,
  onFiltersChange,
  availableDatasets = [],
  availableTypes = DEFAULT_TYPES,
  availableStatuses = DEFAULT_STATUSES
}: ValidationFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key: keyof ValidationFilters, value: string) => {
    const newFilters = {
      ...filters,
      [key]: value || undefined
    };
    onFiltersChange(newFilters);
  };

  const handleClearFilters = () => {
    onFiltersChange({});
  };

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      {/* Header with toggle */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <svg
            className="w-5 h-5 text-gray-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          <h3 className="text-sm font-semibold text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {activeFilterCount} active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {activeFilterCount > 0 && (
            <button
              onClick={handleClearFilters}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Clear all
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            <svg
              className={`w-5 h-5 transform transition-transform ${
                isExpanded ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Filter inputs */}
      {isExpanded && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
          {/* Dataset Name Filter */}
          <div>
            <label
              htmlFor="filter-dataset"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Dataset Name
            </label>
            {availableDatasets.length > 0 ? (
              <select
                id="filter-dataset"
                value={filters.datasetName || ''}
                onChange={(e) => handleFilterChange('datasetName', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
              >
                <option value="">All datasets</option>
                {availableDatasets.map((dataset) => (
                  <option key={dataset} value={dataset}>
                    {dataset}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                id="filter-dataset"
                value={filters.datasetName || ''}
                onChange={(e) => handleFilterChange('datasetName', e.target.value)}
                placeholder="Enter dataset name"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
              />
            )}
          </div>

          {/* Validation Type Filter */}
          <div>
            <label
              htmlFor="filter-type"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Validation Type
            </label>
            <select
              id="filter-type"
              value={filters.validationType || ''}
              onChange={(e) => handleFilterChange('validationType', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">All types</option>
              {availableTypes.map((type) => (
                <option key={type} value={type}>
                  {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label
              htmlFor="filter-status"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Status
            </label>
            <select
              id="filter-status"
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
            >
              <option value="">All statuses</option>
              {availableStatuses.map((status) => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
