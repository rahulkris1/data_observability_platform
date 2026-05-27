import React from 'react';
import ValidationStatusBadge, { ValidationStatus } from './ValidationStatusBadge';

export interface ValidationResult {
  validatorName: string;
  status: ValidationStatus;
  passed: boolean;
  totalRecords: number;
  failedRecords: number;
  passRate: number;
  message: string;
  timestamp: string;
  executionTimeMs?: number;
  errors: string[];
}

export interface ValidationResultsTableProps {
  results: ValidationResult[];
  onRowClick?: (result: ValidationResult) => void;
  loading?: boolean;
}

export default function ValidationResultsTable({
  results,
  onRowClick,
  loading = false
}: ValidationResultsTableProps) {
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
  
  if (results.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No validation results</h3>
          <p className="mt-1 text-sm text-gray-500">Run validations to see detailed results here.</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Validator
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Failed
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Pass Rate
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time (ms)
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Timestamp
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {results.map((result, index) => {
              const isClickable = !!onRowClick;
              
              return (
                <tr
                  key={`${result.validatorName}-${index}`}
                  className={`
                    ${isClickable ? 'cursor-pointer hover:bg-gray-50' : ''}
                    transition-colors duration-150
                  `}
                  onClick={isClickable ? () => onRowClick(result) : undefined}
                >
                  {/* Validator Name */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {result.validatorName}
                      </div>
                      {result.errors.length > 0 && (
                        <div className="text-xs text-red-600 mt-1">
                          {result.errors.length} error(s)
                        </div>
                      )}
                    </div>
                  </td>
                  
                  {/* Status */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <ValidationStatusBadge status={result.status} size="sm" />
                  </td>
                  
                  {/* Total Records */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {result.totalRecords.toLocaleString()}
                  </td>
                  
                  {/* Failed Records */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <span className={result.failedRecords > 0 ? 'text-red-600 font-medium' : 'text-gray-900'}>
                      {result.failedRecords.toLocaleString()}
                    </span>
                  </td>
                  
                  {/* Pass Rate */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <div className="flex items-center justify-end">
                      <span className={`
                        font-medium
                        ${result.passRate >= 95 ? 'text-green-600' : result.passRate >= 80 ? 'text-yellow-600' : 'text-red-600'}
                      `}>
                        {result.passRate.toFixed(1)}%
                      </span>
                      <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className={`
                            h-2 rounded-full
                            ${result.passRate >= 95 ? 'bg-green-500' : result.passRate >= 80 ? 'bg-yellow-500' : 'bg-red-500'}
                          `}
                          style={{ width: `${Math.min(result.passRate, 100)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  
                  {/* Execution Time */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {result.executionTimeMs !== undefined ? result.executionTimeMs.toFixed(2) : '-'}
                  </td>
                  
                  {/* Timestamp */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(result.timestamp).toLocaleString()}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      {/* Summary Footer */}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-700">
            <span className="font-medium">{results.length}</span> validation result(s)
          </span>
          <div className="flex items-center space-x-4 text-gray-600">
            <span>
              Passed: <span className="font-medium text-green-600">
                {results.filter(r => r.passed).length}
              </span>
            </span>
            <span>
              Failed: <span className="font-medium text-red-600">
                {results.filter(r => !r.passed).length}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
