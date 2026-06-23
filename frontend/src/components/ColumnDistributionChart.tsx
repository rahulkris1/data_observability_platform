import React from 'react';
import { ColumnDistribution, ColumnStatistics } from '../services/profilingService';

interface ColumnDistributionChartProps {
  columnName: string;
  distribution: ColumnDistribution;
  statistics?: ColumnStatistics;
}

const ColumnDistributionChart: React.FC<ColumnDistributionChartProps> = ({
  columnName,
  distribution,
  statistics,
}) => {
  const maxCount = Math.max(...distribution.top_values.map(v => v.count), 1);

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{columnName}</h3>
        {statistics && (
          <div className="flex gap-4 mt-2 text-sm text-gray-600">
            <span className="bg-gray-100 px-2 py-1 rounded">
              Type: <span className="font-medium">{statistics.data_type}</span>
            </span>
            <span className="bg-gray-100 px-2 py-1 rounded">
              Unique: <span className="font-medium">{distribution.unique_count}</span>
            </span>
            <span className="bg-gray-100 px-2 py-1 rounded">
              Nulls: <span className="font-medium">{statistics.null_percentage.toFixed(1)}%</span>
            </span>
          </div>
        )}
      </div>

      {/* Numeric Statistics */}
      {statistics && statistics.min !== undefined && (
        <div className="mb-4 grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-xs text-gray-600 mb-1">Min</p>
            <p className="text-sm font-semibold text-gray-900">{statistics.min.toFixed(2)}</p>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-xs text-gray-600 mb-1">Max</p>
            <p className="text-sm font-semibold text-gray-900">{statistics.max?.toFixed(2)}</p>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-xs text-gray-600 mb-1">Mean</p>
            <p className="text-sm font-semibold text-gray-900">{statistics.mean?.toFixed(2)}</p>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-xs text-gray-600 mb-1">Median</p>
            <p className="text-sm font-semibold text-gray-900">{statistics.median?.toFixed(2)}</p>
          </div>
          <div className="bg-blue-50 p-3 rounded">
            <p className="text-xs text-gray-600 mb-1">Std Dev</p>
            <p className="text-sm font-semibold text-gray-900">{statistics.std?.toFixed(2)}</p>
          </div>
        </div>
      )}

      {/* Value Distribution */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Top Values Distribution</h4>
        {distribution.top_values.length > 0 ? (
          <div className="space-y-2">
            {distribution.top_values.map((item, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-32 text-sm text-gray-700 truncate" title={item.value}>
                  {item.value}
                </div>
                <div className="flex-1 bg-gray-200 rounded-full h-6 relative overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-full rounded-full flex items-center justify-end px-2 transition-all duration-300"
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  >
                    <span className="text-xs font-semibold text-white">
                      {item.percentage.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="w-20 text-sm text-gray-600 text-right">
                  {item.count.toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p>No distribution data available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ColumnDistributionChart;
