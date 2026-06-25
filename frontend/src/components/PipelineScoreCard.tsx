import React from 'react';

export interface ScoreCardProps {
  title: string;
  score: number;
  description: string;
  icon: React.ReactNode;
  metrics?: {
    label: string;
    value: string | number;
  }[];
  loading?: boolean;
}

export default function PipelineScoreCard({
  title,
  score,
  description,
  icon,
  metrics,
  loading = false
}: ScoreCardProps) {
  // Determine score color
  const getScoreColor = () => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = () => {
    if (score >= 80) return 'bg-green-50';
    if (score >= 60) return 'bg-yellow-50';
    return 'bg-red-50';
  };

  const getProgressColor = () => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  // Show loading state
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
            <div className="ml-3 h-5 w-32 bg-gray-200 rounded"></div>
          </div>
          <div className="h-8 w-16 bg-gray-200 rounded mb-2"></div>
          <div className="h-4 w-24 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow duration-200">
      {/* Header with Icon */}
      <div className="flex items-center mb-4">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getScoreBgColor()} ${getScoreColor()}`}>
          {icon}
        </div>
        <h3 className="ml-3 text-sm font-semibold text-gray-900">{title}</h3>
      </div>

      {/* Score Display */}
      <div className="mb-3">
        <div className="flex items-baseline">
          <span className={`text-3xl font-bold ${getScoreColor()}`}>
            {score.toFixed(0)}
          </span>
          <span className="ml-1 text-sm text-gray-500">/ 100</span>
        </div>
        <p className="mt-1 text-xs text-gray-600">{description}</p>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${getProgressColor()}`}
            style={{ width: `${score}%` }}
          ></div>
        </div>
      </div>

      {/* Additional Metrics */}
      {metrics && metrics.length > 0 && (
        <div className="border-t border-gray-100 pt-4 mt-4">
          <div className="grid grid-cols-2 gap-3">
            {metrics.map((metric, idx) => (
              <div key={idx} className="text-center">
                <p className="text-xs text-gray-500 mb-1">{metric.label}</p>
                <p className="text-sm font-semibold text-gray-900">
                  {metric.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
