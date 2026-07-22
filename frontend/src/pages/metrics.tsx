import { useEffect, useState } from 'react';
import MetricCard from '@/components/MetricCard';
import Link from 'next/link';
import DashboardLayout from '@/layouts/DashboardLayout';

export default function MetricsPage() {
  const [metrics, setMetrics] = useState({
    totalValidations: 1250,
    successRate: 94.5,
    avgLatency: 245,
    errorRate: 5.5,
  });

  return (
    <DashboardLayout
      title="Metrics Dashboard"
      subtitle="Monitor system performance and data quality metrics"
    >
      <div className="max-w-7xl mx-auto">

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Validations"
            value={metrics.totalValidations.toLocaleString()}
            subtitle="Last 24 hours"
            trend={{ value: 12, isPositive: true }}
            icon="📊"
          />
          <MetricCard
            title="Success Rate"
            value={`${metrics.successRate}%`}
            subtitle="Quality score"
            trend={{ value: 2.5, isPositive: true }}
            icon="✓"
          />
          <MetricCard
            title="Avg Latency"
            value={`${metrics.avgLatency}ms`}
            subtitle="Processing time"
            trend={{ value: 5, isPositive: false }}
            icon="⚡"
          />
          <MetricCard
            title="Error Rate"
            value={`${metrics.errorRate}%`}
            subtitle="Failed validations"
            trend={{ value: 1.2, isPositive: false }}
            icon="⚠️"
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Validation Trend */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Validation Trend
            </h2>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <p className="text-gray-500">Chart: Validations over time</p>
            </div>
          </div>

          {/* Data Quality Score */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Data Quality Score
            </h2>
            <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
              <div className="text-center">
                <div className="text-6xl font-bold text-blue-600">
                  {metrics.successRate}%
                </div>
                <p className="text-gray-500 mt-2">Overall Quality</p>
              </div>
            </div>
          </div>
        </div>

        {/* Performance Metrics */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Performance Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl font-bold text-blue-600">2.4M</div>
              <p className="text-sm text-gray-600 mt-2">Records Processed</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-3xl font-bold text-green-600">99.2%</div>
              <p className="text-sm text-gray-600 mt-2">Uptime</p>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl font-bold text-purple-600">12</div>
              <p className="text-sm text-gray-600 mt-2">Active Pipelines</p>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">
            Detailed Metrics
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Link
              href="/metrics-dashboard"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Full Dashboard</h3>
              <p className="text-sm text-gray-600 mt-1">
                Comprehensive metrics view
              </p>
            </Link>
            <Link
              href="/cache-monitoring"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Cache Metrics</h3>
              <p className="text-sm text-gray-600 mt-1">Redis performance</p>
            </Link>
            <Link
              href="/freshness-monitoring"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Freshness</h3>
              <p className="text-sm text-gray-600 mt-1">Data timeliness</p>
            </Link>
            <Link
              href="/logs"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Logs</h3>
              <p className="text-sm text-gray-600 mt-1">System logs</p>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
