/**
 * Drift Alert Indicator Component
 * 
 * Displays drift alert badges with severity indicators
 */

import React from 'react';
import { SchemaDrift } from '@/services/schemaDriftService';

interface DriftAlertIndicatorProps {
  drift: SchemaDrift;
  compact?: boolean;
}

const DriftAlertIndicator: React.FC<DriftAlertIndicatorProps> = ({ drift, compact = false }) => {
  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getDriftTypeLabel = (type: string): string => {
    const labels: Record<string, string> = {
      column_added: 'Column Added',
      column_removed: 'Column Removed',
      type_changed: 'Type Changed',
      nullability_changed: 'Nullability Changed',
      position_changed: 'Position Changed'
    };
    return labels[type] || type;
  };

  const getSeverityIcon = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '•';
    }
  };

  if (compact) {
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getSeverityColor(
          drift.severity
        )}`}
      >
        <span className="mr-1">{getSeverityIcon(drift.severity)}</span>
        {getDriftTypeLabel(drift.drift_type)}
      </span>
    );
  }

  return (
    <div
      className={`p-3 rounded-lg border-l-4 ${getSeverityColor(drift.severity)}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{getSeverityIcon(drift.severity)}</span>
            <span className="font-semibold text-sm uppercase tracking-wide">
              {drift.severity}
            </span>
          </div>
          <p className="text-sm font-medium">{getDriftTypeLabel(drift.drift_type)}</p>
          <p className="text-xs text-gray-600 mt-1">
            Detected: {new Date(drift.detected_at).toLocaleString()}
          </p>
        </div>
        {drift.acknowledged && (
          <div className="ml-2">
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
              ✓ Acknowledged
            </span>
          </div>
        )}
      </div>
      
      {/* Changes Summary */}
      <div className="mt-2 space-y-1 text-xs">
        {drift.changes.added_columns.length > 0 && (
          <div className="text-green-700">
            + {drift.changes.added_columns.length} column(s) added
          </div>
        )}
        {drift.changes.removed_columns.length > 0 && (
          <div className="text-red-700">
            - {drift.changes.removed_columns.length} column(s) removed
          </div>
        )}
        {drift.changes.type_changes.length > 0 && (
          <div className="text-orange-700">
            ⚡ {drift.changes.type_changes.length} type change(s)
          </div>
        )}
        {drift.changes.nullability_changes.length > 0 && (
          <div className="text-blue-700">
            ◇ {drift.changes.nullability_changes.length} nullability change(s)
          </div>
        )}
      </div>
    </div>
  );
};

export default DriftAlertIndicator;
