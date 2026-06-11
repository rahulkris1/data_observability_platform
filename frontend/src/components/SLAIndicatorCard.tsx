import React from 'react';

export interface SLAIndicatorCardProps {
  compliancePercentage: number;
  breachCount: number;
  compliantCount: number;
  totalOperations: number;
  loading?: boolean;
}

export default function SLAIndicatorCard({
  compliancePercentage,
  breachCount,
  compliantCount,
  totalOperations,
  loading = false
}: SLAIndicatorCardProps) {
  // Determine status color based on compliance percentage
  const getStatusColor = (percentage: number) => {
    if (percentage >= 95) return 'text-green-600';
    if (percentage >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const statusColor = getStatusColor(compliancePercentage);

  // Determine status label
  const getStatusLabel = (percentage: number) => {
    if (percentage >= 95) return 'Excellent';
    if (percentage >= 80) return 'Good';
    if (percentage >= 60) return 'Fair';
    return 'Poor';
  };

  const statusLabel = getStatusLabel(compliancePercentage);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">SLA Compliance</h3>
        <div className={`text-sm font-medium px-3 py-1 rounded-full ${
          compliancePercentage >= 95 ? 'bg-green-100 text-green-800' :
          compliancePercentage >= 80 ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {statusLabel}
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          <div className="h-24 bg-gray-200 animate-pulse rounded"></div>
          <div className="h-16 bg-gray-200 animate-pulse rounded"></div>
        </div>
      ) : (
        <>
          {/* Compliance Percentage */}
          <div className="text-center mb-6">
            <div className={`text-5xl font-bold ${statusColor} mb-2`}>
              {compliancePercentage.toFixed(1)}%
            </div>
            <p className="text-sm text-gray-600">Overall Compliance</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6">
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  compliancePercentage >= 95 ? 'bg-green-600' :
                  compliancePercentage >= 80 ? 'bg-yellow-600' :
                  'bg-red-600'
                }`}
                style={{ width: `${compliancePercentage}%` }}
              />
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            {/* Total Operations */}
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{totalOperations}</div>
              <div className="text-xs text-gray-500 mt-1">Total</div>
            </div>

            {/* Compliant */}
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{compliantCount}</div>
              <div className="text-xs text-gray-500 mt-1">Compliant</div>
            </div>

            {/* Breached */}
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{breachCount}</div>
              <div className="text-xs text-gray-500 mt-1">Breached</div>
            </div>
          </div>

          {/* Status Message */}
          {breachCount > 0 && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                <span className="font-semibold">{breachCount}</span> dataset{breachCount !== 1 ? 's' : ''} breached SLA threshold
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
