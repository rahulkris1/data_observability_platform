/**
 * Schema Comparison Table Component
 * 
 * Displays a side-by-side comparison of two schema versions
 */

import React from 'react';
import { SchemaComparisonResponse, ColumnDefinition } from '@/services/schemaDriftService';

interface SchemaComparisonTableProps {
  comparison: SchemaComparisonResponse;
}

const SchemaComparisonTable: React.FC<SchemaComparisonTableProps> = ({ comparison }) => {
  // Extract all unique column names
  const getAllColumns = () => {
    const columns = new Set<string>();
    
    comparison.changes.added_columns.forEach(col => columns.add(col.name));
    comparison.changes.removed_columns.forEach(col => columns.add(col.name));
    comparison.changes.type_changes.forEach(col => columns.add(col.name));
    comparison.changes.nullability_changes.forEach(col => columns.add(col.name));
    
    return Array.from(columns).sort();
  };

  const getChangeType = (columnName: string): string | null => {
    if (comparison.changes.added_columns.some(col => col.name === columnName)) {
      return 'added';
    }
    if (comparison.changes.removed_columns.some(col => col.name === columnName)) {
      return 'removed';
    }
    if (comparison.changes.type_changes.some(col => col.name === columnName)) {
      return 'type_changed';
    }
    if (comparison.changes.nullability_changes.some(col => col.name === columnName)) {
      return 'nullability_changed';
    }
    return null;
  };

  const getRowStyle = (changeType: string | null): string => {
    switch (changeType) {
      case 'added':
        return 'bg-green-50 border-l-4 border-green-500';
      case 'removed':
        return 'bg-red-50 border-l-4 border-red-500';
      case 'type_changed':
        return 'bg-orange-50 border-l-4 border-orange-500';
      case 'nullability_changed':
        return 'bg-blue-50 border-l-4 border-blue-500';
      default:
        return '';
    }
  };

  const getChangeIcon = (changeType: string | null): string => {
    switch (changeType) {
      case 'added':
        return '➕';
      case 'removed':
        return '➖';
      case 'type_changed':
        return '⚡';
      case 'nullability_changed':
        return '◇';
      default:
        return '';
    }
  };

  const allColumns = getAllColumns();

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">
          Schema Comparison: Version {comparison.version1} vs Version {comparison.version2}
        </h3>
        <p className="text-sm text-gray-600 mt-1">
          {comparison.has_drift ? (
            <span className="text-orange-600 font-medium">
              {comparison.drift_type} detected ({comparison.severity} severity)
            </span>
          ) : (
            <span className="text-green-600 font-medium">No drift detected</span>
          )}
        </p>
      </div>

      {/* Legend */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-1">
            <span>➕</span>
            <span>Added</span>
          </div>
          <div className="flex items-center gap-1">
            <span>➖</span>
            <span>Removed</span>
          </div>
          <div className="flex items-center gap-1">
            <span>⚡</span>
            <span>Type Changed</span>
          </div>
          <div className="flex items-center gap-1">
            <span>◇</span>
            <span>Nullability Changed</span>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Column Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Version {comparison.version1}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Version {comparison.version2}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Change
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {allColumns.length === 0 && !comparison.has_drift && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  No changes detected - schemas are identical
                </td>
              </tr>
            )}
            
            {comparison.changes.added_columns.map((col, idx) => {
              const changeType = getChangeType(col.name);
              return (
                <tr key={`added-${idx}`} className={getRowStyle(changeType)}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {getChangeIcon(changeType)} {col.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex flex-col">
                      <span className="font-medium">{col.data_type}</span>
                      <span className="text-xs text-gray-500">
                        {col.nullable ? 'Nullable' : 'Not Null'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Added
                    </span>
                  </td>
                </tr>
              );
            })}

            {comparison.changes.removed_columns.map((col, idx) => {
              const changeType = getChangeType(col.name);
              return (
                <tr key={`removed-${idx}`} className={getRowStyle(changeType)}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {getChangeIcon(changeType)} {col.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex flex-col">
                      <span className="font-medium">{col.data_type}</span>
                      <span className="text-xs text-gray-500">
                        {col.nullable ? 'Nullable' : 'Not Null'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="text-gray-400">—</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Removed
                    </span>
                  </td>
                </tr>
              );
            })}

            {comparison.changes.type_changes.map((col, idx) => {
              const changeType = getChangeType(col.name);
              return (
                <tr key={`type-${idx}`} className={getRowStyle(changeType)}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {getChangeIcon(changeType)} {col.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-medium">{col.previous_type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="font-medium">{col.current_type}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                      Type Changed
                    </span>
                  </td>
                </tr>
              );
            })}

            {comparison.changes.nullability_changes.map((col, idx) => {
              const changeType = getChangeType(col.name);
              return (
                <tr key={`null-${idx}`} className={getRowStyle(changeType)}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {getChangeIcon(changeType)} {col.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="text-xs">
                      {col.previous_nullable ? 'Nullable' : 'Not Null'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="text-xs">
                      {col.current_nullable ? 'Nullable' : 'Not Null'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      Nullability Changed
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default SchemaComparisonTable;
