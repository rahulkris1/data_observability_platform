import React from 'react';
import { ProfilingResult } from '../services/profilingService';

interface ProfilingSummaryCardsProps {
  profiling: ProfilingResult;
}

const ProfilingSummaryCards: React.FC<ProfilingSummaryCardsProps> = ({ profiling }) => {
  // Calculate summary statistics
  const totalColumns = profiling.column_count || 0;
  const totalRows = profiling.row_count || 0;
  
  // Calculate average null percentage across all columns
  let avgNullPercentage = 0;
  let numericColumnsCount = 0;
  
  if (profiling.column_statistics) {
    const stats = Object.values(profiling.column_statistics);
    avgNullPercentage = stats.reduce((sum, col) => sum + col.null_percentage, 0) / stats.length;
    numericColumnsCount = stats.filter(col => col.min !== undefined).length;
  }
  
  const executionTime = profiling.execution_time_ms 
    ? (profiling.execution_time_ms / 1000).toFixed(2) 
    : '0';

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      {/* Total Rows */}
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Total Rows</p>
            <p className="text-3xl font-bold text-gray-900">
              {totalRows.toLocaleString()}
            </p>
          </div>
          <div className="bg-blue-100 rounded-full p-3">
            <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
          </div>
        </div>
      </div>

      {/* Total Columns */}
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Total Columns</p>
            <p className="text-3xl font-bold text-gray-900">{totalColumns}</p>
            <p className="text-xs text-gray-500 mt-1">
              {numericColumnsCount} numeric
            </p>
          </div>
          <div className="bg-green-100 rounded-full p-3">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
            </svg>
          </div>
        </div>
      </div>

      {/* Data Completeness */}
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Data Completeness</p>
            <p className="text-3xl font-bold text-gray-900">
              {(100 - avgNullPercentage).toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Avg null: {avgNullPercentage.toFixed(1)}%
            </p>
          </div>
          <div className="bg-purple-100 rounded-full p-3">
            <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

      {/* Execution Time */}
      <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">Execution Time</p>
            <p className="text-3xl font-bold text-gray-900">{executionTime}s</p>
            <p className="text-xs text-gray-500 mt-1">
              {new Date(profiling.created_at).toLocaleTimeString()}
            </p>
          </div>
          <div className="bg-orange-100 rounded-full p-3">
            <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilingSummaryCards;
