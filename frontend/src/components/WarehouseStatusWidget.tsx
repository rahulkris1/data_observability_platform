import React from 'react';

interface WarehouseStatusWidgetProps {
  stats: any;
  loading: boolean;
  error: string | null;
}

export default function WarehouseStatusWidget({ stats, loading, error }: WarehouseStatusWidgetProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <svg className="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="text-sm font-medium text-red-800">Error Loading Warehouse Status</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const calculateHealthStatus = () => {
    if (!stats.total_loads) return { status: 'Unknown', color: 'bg-gray-500' };
    
    const successRate = (stats.successful_loads / stats.total_loads) * 100;
    
    if (successRate >= 95) return { status: 'Healthy', color: 'bg-green-500' };
    if (successRate >= 80) return { status: 'Warning', color: 'bg-yellow-500' };
    return { status: 'Critical', color: 'bg-red-500' };
  };

  const healthStatus = calculateHealthStatus();

  const formatTimestamp = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return `${Math.floor(diffMins / 1440)} days ago`;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Warehouse Health Status */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-600">Warehouse Health</h3>
          <div className={`w-3 h-3 rounded-full ${healthStatus.color}`}></div>
        </div>
        <div className="flex items-baseline space-x-2">
          <p className="text-3xl font-bold text-gray-900">{healthStatus.status}</p>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          {stats.successful_loads} / {stats.total_loads} loads successful
        </p>
      </div>

      {/* Total Records Loaded */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-600">Total Records</h3>
          <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
          </svg>
        </div>
        <div className="flex items-baseline space-x-2">
          <p className="text-3xl font-bold text-gray-900">
            {formatNumber(stats.total_records || 0)}
          </p>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          Across {Object.keys(stats.records_by_dataset || {}).length} dataset(s)
        </p>
      </div>

      {/* Failed Load Count */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-600">Failed Loads</h3>
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex items-baseline space-x-2">
          <p className="text-3xl font-bold text-gray-900">
            {stats.failed_loads || 0}
          </p>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          {stats.total_loads ? ((stats.failed_loads / stats.total_loads) * 100).toFixed(1) : 0}% failure rate
        </p>
      </div>

      {/* Latest Load Timestamp */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-600">Latest Load</h3>
          <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex items-baseline space-x-2">
          <p className="text-2xl font-bold text-gray-900">
            {formatTimestamp(stats.latest_load_timestamp)}
          </p>
        </div>
        <div className="flex items-center space-x-2 mt-2">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
            stats.latest_load_status === 'completed' 
              ? 'bg-green-100 text-green-800' 
              : stats.latest_load_status === 'failed'
              ? 'bg-red-100 text-red-800'
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {stats.latest_load_status || 'Unknown'}
          </span>
        </div>
      </div>
    </div>
  );
}
