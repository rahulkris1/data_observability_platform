import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export interface HealthTrendData {
  timestamp: string;
  overall_score: number;
  validation_score: number;
  freshness_score: number;
  latency_score: number;
}

export interface HealthTrendChartProps {
  data: HealthTrendData[];
  loading?: boolean;
  height?: number;
}

export default function HealthTrendChart({
  data,
  loading = false,
  height = 300
}: HealthTrendChartProps) {
  // Show loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading health trend...</span>
        </div>
      </div>
    );
  }

  // Show empty state
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
        <div className="text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No trend data</h3>
          <p className="mt-1 text-sm text-gray-500">
            Health score history will appear here once data is available
          </p>
        </div>
      </div>
    );
  }

  // Format chart data
  const chartData = data.map((item) => ({
    time: new Date(item.timestamp).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    'Overall Score': item.overall_score,
    'Validation': item.validation_score,
    'Freshness': item.freshness_score,
    'Latency': item.latency_score,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Health Score Trend</h3>
        <p className="text-sm text-gray-600 mt-1">
          Historical view of pipeline health metrics
        </p>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            stroke="#6b7280"
            label={{
              value: 'Score',
              angle: -90,
              position: 'insideLeft',
              style: { fontSize: 12, fill: '#6b7280' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: 12 }}
            iconType="line"
          />
          <Line
            type="monotone"
            dataKey="Overall Score"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="Validation"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="Freshness"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="Latency"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            strokeDasharray="5 5"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-4 gap-4 border-t border-gray-100 pt-4">
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Data Points</p>
          <p className="text-lg font-semibold text-gray-900">{data.length}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Avg Overall</p>
          <p className="text-lg font-semibold text-blue-600">
            {(data.reduce((sum, d) => sum + d.overall_score, 0) / data.length).toFixed(1)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Best Score</p>
          <p className="text-lg font-semibold text-green-600">
            {Math.max(...data.map(d => d.overall_score)).toFixed(1)}
          </p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-1">Lowest Score</p>
          <p className="text-lg font-semibold text-red-600">
            {Math.min(...data.map(d => d.overall_score)).toFixed(1)}
          </p>
        </div>
      </div>
    </div>
  );
}
