import React from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import CacheStatusIndicator from '../components/CacheStatusIndicator';
import PipelinePerformanceSection from '../components/PipelinePerformanceSection';
import CacheMetricsCard from '../components/CacheMetricsCard';

export default function CacheMonitoring() {
  return (
    <DashboardLayout
      title="Cache Monitoring"
      subtitle="Monitor Redis cache performance and health"
    >
      {/* Cache Status */}
      <div className="mb-6">
        <CacheStatusIndicator refreshInterval={10000} />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Section - Takes 2 columns */}
        <div className="lg:col-span-2">
          <PipelinePerformanceSection refreshInterval={5000} />
        </div>

        {/* Metrics Card - Takes 1 column */}
        <div>
          <CacheMetricsCard refreshInterval={5000} />
        </div>
      </div>

      {/* Additional Information */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">About Cache Monitoring</h2>
        <div className="space-y-4 text-sm text-gray-600">
          <div>
            <h3 className="font-medium text-gray-900 mb-2">What is cached?</h3>
            <ul className="list-disc list-inside space-y-1">
              <li>Schema contracts for tables and datasets</li>
              <li>Validation metadata and results</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Cache Performance Metrics</h3>
            <ul className="list-disc list-inside space-y-1">
              <li><strong>Hit Rate:</strong> Percentage of requests served from cache</li>
              <li><strong>Hits:</strong> Number of successful cache retrievals</li>
              <li><strong>Misses:</strong> Number of cache lookups that failed</li>
              <li><strong>Sets:</strong> Number of write operations to cache</li>
              <li><strong>Deletes:</strong> Number of cache invalidations</li>
            </ul>
          </div>
          <div>
            <h3 className="font-medium text-gray-900 mb-2">Cache Refresh</h3>
            <p>
              Use the "Refresh Cache" button to invalidate all cached data and reset statistics.
              This forces fresh data to be loaded from the database on the next request.
            </p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
