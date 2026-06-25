import React from 'react';

export interface HealthScoreWidgetProps {
  pipelineName: string;
  overallScore: number;
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp?: string;
  loading?: boolean;
}

export default function HealthScoreWidget({
  pipelineName,
  overallScore,
  status,
  timestamp,
  loading = false
}: HealthScoreWidgetProps) {
  // Determine color based on status
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'degraded':
        return 'bg-yellow-500';
      case 'unhealthy':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusTextColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-700';
      case 'degraded':
        return 'text-yellow-700';
      case 'unhealthy':
        return 'text-red-700';
      default:
        return 'text-gray-700';
    }
  };

  const getStatusBgColor = () => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50';
      case 'degraded':
        return 'bg-yellow-50';
      case 'unhealthy':
        return 'bg-red-50';
      default:
        return 'bg-gray-50';
    }
  };

  // Show loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading health score...</span>
        </div>
      </div>
    );
  }

  // Format timestamp
  const formatTimestamp = (ts?: string) => {
    if (!ts) return 'Just now';
    const date = new Date(ts);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Pipeline Health</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBgColor()} ${getStatusTextColor()}`}>
          {status.toUpperCase()}
        </span>
      </div>

      {/* Score Display */}
      <div className="flex items-center justify-center mb-6">
        <div className="relative">
          {/* Circular Progress */}
          <svg className="w-40 h-40 transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="#e5e7eb"
              strokeWidth="12"
              fill="none"
            />
            {/* Progress circle */}
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="12"
              fill="none"
              strokeDasharray={`${(overallScore / 100) * 439.6} 439.6`}
              strokeLinecap="round"
              className={
                status === 'healthy'
                  ? 'text-green-500'
                  : status === 'degraded'
                  ? 'text-yellow-500'
                  : 'text-red-500'
              }
            />
          </svg>

          {/* Score Text */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900">
                {overallScore.toFixed(0)}
              </div>
              <div className="text-sm text-gray-500">/ 100</div>
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Info */}
      <div className="border-t border-gray-100 pt-4">
        <div className="text-center">
          <p className="text-sm font-medium text-gray-900 mb-1">
            {pipelineName}
          </p>
          <p className="text-xs text-gray-500">
            Updated {formatTimestamp(timestamp)}
          </p>
        </div>
      </div>

      {/* Status Indicator */}
      <div className="mt-4 flex items-center justify-center">
        <div className={`w-2 h-2 rounded-full ${getStatusColor()} mr-2`}></div>
        <span className="text-sm text-gray-600">
          {status === 'healthy' && 'All systems operational'}
          {status === 'degraded' && 'Performance degraded'}
          {status === 'unhealthy' && 'Attention required'}
        </span>
      </div>
    </div>
  );
}
