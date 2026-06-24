/**
 * Schema Timeline View Component
 * 
 * Displays a timeline of schema changes for a dataset
 */

import React from 'react';
import { SchemaTimelineItem } from '@/services/schemaDriftService';

interface SchemaTimelineViewProps {
  timeline: SchemaTimelineItem[];
  datasetName: string;
}

const SchemaTimelineView: React.FC<SchemaTimelineViewProps> = ({ timeline, datasetName }) => {
  const getSeverityColor = (severity?: string): string => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50';
      case 'warning':
        return 'border-yellow-500 bg-yellow-50';
      case 'info':
        return 'border-blue-500 bg-blue-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const getDriftTypeLabel = (type?: string): string => {
    if (!type) return '';
    const labels: Record<string, string> = {
      column_added: 'Column Added',
      column_removed: 'Column Removed',
      type_changed: 'Type Changed',
      nullability_changed: 'Nullability Changed',
      position_changed: 'Position Changed'
    };
    return labels[type] || type;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Schema Evolution Timeline
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          Dataset: <span className="font-medium">{datasetName}</span>
        </p>
      </div>

      <div className="p-6">
        {timeline.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No schema versions found for this dataset</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline vertical line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>

            {/* Timeline items */}
            <div className="space-y-6">
              {timeline.map((item, index) => (
                <div key={`timeline-${item.version_number}`} className="relative pl-16">
                  {/* Timeline dot */}
                  <div
                    className={`absolute left-6 w-4 h-4 rounded-full border-2 ${
                      item.drift_occurred
                        ? getSeverityColor(item.severity).split(' ')[0]
                        : 'border-gray-300'
                    } bg-white`}
                    style={{ top: '6px' }}
                  ></div>

                  {/* Timeline content */}
                  <div
                    className={`rounded-lg border-2 p-4 ${
                      item.drift_occurred
                        ? getSeverityColor(item.severity)
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                            v{item.version_number}
                          </span>
                          {item.drift_occurred && item.drift_type && (
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                item.severity === 'critical'
                                  ? 'bg-red-100 text-red-800'
                                  : item.severity === 'warning'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {getDriftTypeLabel(item.drift_type)}
                            </span>
                          )}
                          {item.source && (
                            <span className="text-xs text-gray-500">
                              Source: {item.source}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mt-2">
                          {formatDate(item.detected_at)}
                        </p>
                        {!item.drift_occurred && index === 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            Current version - No drift
                          </p>
                        )}
                        {!item.drift_occurred && index > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            No drift detected
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SchemaTimelineView;
