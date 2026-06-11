import React from 'react';
import { FreshnessTimeSeriesPoint } from '../services/freshnessService';
import ThresholdStatusBadge from './ThresholdStatusBadge';

export interface FreshnessMetricsChartProps {
  dataPoints: FreshnessTimeSeriesPoint[];
  datasetName?: string;
  loading?: boolean;
}

export default function FreshnessMetricsChart({
  dataPoints,
  datasetName,
  loading = false
}: FreshnessMetricsChartProps) {
  // Group data by dataset if showing all datasets
  const datasetGroups = React.useMemo(() => {
    const groups: Record<string, FreshnessTimeSeriesPoint[]> = {};
    dataPoints.forEach(point => {
      if (!groups[point.dataset_name]) {
        groups[point.dataset_name] = [];
      }
      groups[point.dataset_name].push(point);
    });
    return groups;
  }, [dataPoints]);

  // Get latest status for each dataset
  const latestStatuses = React.useMemo(() => {
    const statuses: Record<string, { status: string; age: number; timestamp: string }> = {};
    Object.entries(datasetGroups).forEach(([dataset, points]) => {
      if (points.length > 0) {
        const latest = points[points.length - 1];
        statuses[dataset] = {
          status: latest.freshness_status,
          age: latest.dataset_age_hours,
          timestamp: latest.timestamp
        };
      }
    });
    return statuses;
  }, [datasetGroups]);

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format age
  const formatAge = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}m`;
    } else if (hours < 24) {
      return `${hours.toFixed(1)}h`;
    } else {
      return `${(hours / 24).toFixed(1)}d`;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="h-8 w-48 bg-gray-200 animate-pulse rounded mb-4"></div>
        <div className="h-64 bg-gray-200 animate-pulse rounded"></div>
      </div>
    );
  }

  if (dataPoints.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Freshness Trends {datasetName && `- ${datasetName}`}
        </h3>
        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm">No freshness data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Freshness Status by Dataset
      </h3>

      {/* Dataset status cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(latestStatuses).map(([dataset, data]) => (
          <div
            key={dataset}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <h4 className="font-medium text-gray-900 truncate flex-1">{dataset}</h4>
              <ThresholdStatusBadge
                status={data.status as 'healthy' | 'warning' | 'critical'}
                size="sm"
                showIcon={true}
              />
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Dataset Age:</span>
                <span className="font-medium text-gray-900">{formatAge(data.age)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Last Updated:</span>
                <span className="font-medium text-gray-900 text-xs">
                  {new Date(data.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Time series visualization (simplified table view) */}
      {datasetName && dataPoints.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Recent History</h4>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Age
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {dataPoints.slice(-10).reverse().map((point, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatTimestamp(point.timestamp)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatAge(point.dataset_age_hours)}
                    </td>
                    <td className="px-4 py-3">
                      <ThresholdStatusBadge
                        status={point.freshness_status as 'healthy' | 'warning' | 'critical'}
                        size="sm"
                      />
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
