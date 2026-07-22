import React from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import MetricCard from '../components/MetricCard';
// Commented out to avoid timeouts in simplified mode (Redis/MinIO/CloudWatch not connected)
// import CacheStatusIndicator from '../components/CacheStatusIndicator';
// import PipelinePerformanceSection from '../components/PipelinePerformanceSection';
// import CacheMetricsCard from '../components/CacheMetricsCard';
// import StorageProviderStatus from '../components/StorageProviderStatus';
// import CloudWatchStatusCard from '../components/CloudWatchStatusCard';
// import MetricsProviderStatus from '../components/MetricsProviderStatus';
// import CloudObservabilitySection from '../components/CloudObservabilitySection';

export default function Dashboard() {
  // Placeholder metrics data
  const metrics = [
    {
      title: 'Total Data Sources',
      value: '12',
      subtitle: 'Active connections',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      ),
    },
    {
      title: 'Data Quality Score',
      value: '94%',
      trend: {
        value: 2.5,
        isPositive: true,
      },
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      title: 'Records Processed',
      value: '2.4M',
      subtitle: 'Last 24 hours',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
      ),
    },
    {
      title: 'Active Alerts',
      value: '3',
      trend: {
        value: 25,
        isPositive: false,
      },
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    },
  ];

  return (
    <DashboardLayout 
      title="Data Observability Dashboard"
      subtitle="Monitor your data quality, lineage, and health in real-time"
    >
      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {metrics.map((metric, index) => (
          <MetricCard
            key={index}
            title={metric.title}
            value={metric.value}
            subtitle={metric.subtitle}
            trend={metric.trend}
            icon={metric.icon}
          />
        ))}
      </div>

      {/* Disabled in simplified mode - these services aren't connected */}
      {/* <div className="mb-6"><CacheStatusIndicator /></div> */}
      {/* <div className="mb-6"><StorageProviderStatus /></div> */}
      {/* <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <CloudWatchStatusCard />
        <MetricsProviderStatus />
      </div> */}
      {/* <div className="mb-8"><CloudObservabilitySection /></div> */}
      {/* <div className="mb-8"><PipelinePerformanceSection /></div> */}

      {/* Simplified Mode Notice */}
      <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <svg className="w-6 h-6 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Simplified Local Mode</h3>
            <p className="text-sm text-blue-800 mb-2">
              Running in simplified mode with SQLite database. Some dashboard features are disabled:
            </p>
            <ul className="text-sm text-blue-700 space-y-1 ml-4 list-disc">
              <li>Redis cache monitoring (degraded mode - working without Redis)</li>
              <li>MinIO storage monitoring (using local file system)</li>
              <li>CloudWatch metrics (not configured)</li>
            </ul>
            <p className="text-sm text-blue-800 mt-3">
              To enable full features, run with Docker using <code className="bg-blue-100 px-2 py-0.5 rounded">docker-compose up</code>
            </p>
          </div>
        </div>
      </div>

      {/* Additional Dashboard Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Recent Activity
          </h2>
          <div className="space-y-3">
            {[1, 2, 3].map((item) => (
              <div key={item} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-700">Data pipeline completed successfully</p>
                  <p className="text-xs text-gray-500 mt-1">{item} hour(s) ago</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Data Health Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Data Health Status
          </h2>
          <div className="space-y-4">
            {[
              { name: 'Completeness', value: 96, color: 'bg-green-500' },
              { name: 'Accuracy', value: 92, color: 'bg-blue-500' },
              { name: 'Timeliness', value: 88, color: 'bg-yellow-500' },
            ].map((health) => (
              <div key={health.name}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-700">{health.name}</span>
                  <span className="text-gray-900 font-medium">{health.value}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`${health.color} h-2 rounded-full`}
                    style={{ width: `${health.value}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
