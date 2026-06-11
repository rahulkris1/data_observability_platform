import React from 'react';
import { FreshnessTimeSeriesPoint } from '../services/freshnessService';

export interface LatencyChartProps {
  dataPoints: FreshnessTimeSeriesPoint[];
  datasetName?: string;
  loading?: boolean;
}

export default function LatencyChart({
  dataPoints,
  datasetName,
  loading = false
}: LatencyChartProps) {
  // Calculate average latencies
  const stats = React.useMemo(() => {
    const ingestionLatencies = dataPoints
      .filter(p => p.ingestion_latency_seconds !== undefined && p.ingestion_latency_seconds !== null)
      .map(p => p.ingestion_latency_seconds!);
    
    const validationLatencies = dataPoints
      .filter(p => p.validation_latency_seconds !== undefined && p.validation_latency_seconds !== null)
      .map(p => p.validation_latency_seconds!);

    const avgIngestion = ingestionLatencies.length > 0
      ? ingestionLatencies.reduce((a, b) => a + b, 0) / ingestionLatencies.length
      : 0;

    const avgValidation = validationLatencies.length > 0
      ? validationLatencies.reduce((a, b) => a + b, 0) / validationLatencies.length
      : 0;

    const maxIngestion = ingestionLatencies.length > 0
      ? Math.max(...ingestionLatencies)
      : 0;

    const maxValidation = validationLatencies.length > 0
      ? Math.max(...validationLatencies)
      : 0;

    return {
      avgIngestion,
      avgValidation,
      maxIngestion,
      maxValidation,
      totalIngestion: ingestionLatencies.length,
      totalValidation: validationLatencies.length
    };
  }, [dataPoints]);

  // Format latency in seconds or minutes
  const formatLatency = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(2)}s`;
    } else {
      return `${(seconds / 60).toFixed(2)}m`;
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
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
          Latency Trends {datasetName && `- ${datasetName}`}
        </h3>
        <div className="flex flex-col items-center justify-center h-64 text-gray-400">
          <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm">No latency data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Latency Metrics {datasetName && `- ${datasetName}`}
      </h3>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Avg Ingestion Latency */}
        <div className="bg-blue-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <svg className="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
            <span className="text-xs font-medium text-blue-900">Avg Ingestion</span>
          </div>
          <div className="text-2xl font-bold text-blue-900">
            {formatLatency(stats.avgIngestion)}
          </div>
        </div>

        {/* Max Ingestion Latency */}
        <div className="bg-indigo-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <svg className="w-5 h-5 text-indigo-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            <span className="text-xs font-medium text-indigo-900">Max Ingestion</span>
          </div>
          <div className="text-2xl font-bold text-indigo-900">
            {formatLatency(stats.maxIngestion)}
          </div>
        </div>

        {/* Avg Validation Latency */}
        <div className="bg-purple-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <svg className="w-5 h-5 text-purple-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs font-medium text-purple-900">Avg Validation</span>
          </div>
          <div className="text-2xl font-bold text-purple-900">
            {formatLatency(stats.avgValidation)}
          </div>
        </div>

        {/* Max Validation Latency */}
        <div className="bg-pink-50 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <svg className="w-5 h-5 text-pink-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-xs font-medium text-pink-900">Max Validation</span>
          </div>
          <div className="text-2xl font-bold text-pink-900">
            {formatLatency(stats.maxValidation)}
          </div>
        </div>
      </div>

      {/* Recent Latency Data */}
      <div className="pt-6 border-t border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Recent Latency Measurements</h4>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                {!datasetName && (
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dataset
                  </th>
                )}
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Ingestion
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Validation
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dataPoints.slice(-10).reverse().map((point, idx) => {
                const total = (point.ingestion_latency_seconds || 0) + (point.validation_latency_seconds || 0);
                return (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {formatTimestamp(point.timestamp)}
                    </td>
                    {!datasetName && (
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">
                        {point.dataset_name}
                      </td>
                    )}
                    <td className="px-4 py-3 text-sm text-blue-600 font-medium">
                      {point.ingestion_latency_seconds ? formatLatency(point.ingestion_latency_seconds) : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-purple-600 font-medium">
                      {point.validation_latency_seconds ? formatLatency(point.validation_latency_seconds) : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 font-semibold">
                      {total > 0 ? formatLatency(total) : 'N/A'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
