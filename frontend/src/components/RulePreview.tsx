import React from 'react';
import { Rule } from '@/services/rulesService';

export interface RulePreviewProps {
  rule: Rule;
}

export default function RulePreview({ rule }: RulePreviewProps) {
  const severityColors = {
    error: 'bg-red-100 text-red-800 border-red-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    info: 'bg-blue-100 text-blue-800 border-blue-200',
  };
  
  const statusColors = rule.enabled
    ? 'bg-green-100 text-green-800 border-green-200'
    : 'bg-gray-100 text-gray-800 border-gray-200';
  
  const operatorSymbols: Record<string, string> = {
    '>': '>',
    '>=': '≥',
    '<': '<',
    '<=': '≤',
    '==': '=',
    '!=': '≠',
  };
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{rule.name}</h3>
          <p className="text-sm text-gray-600 mt-1">ID: {rule.rule_id}</p>
        </div>
        
        <div className="flex items-center space-x-2">
          <span
            className={`
              px-2.5 py-1 text-xs font-medium rounded-full border
              ${statusColors}
            `}
          >
            {rule.enabled ? 'Enabled' : 'Disabled'}
          </span>
          
          <span
            className={`
              px-2.5 py-1 text-xs font-medium rounded-full border
              ${severityColors[rule.severity as keyof typeof severityColors] || severityColors.info}
            `}
          >
            {rule.severity.toUpperCase()}
          </span>
        </div>
      </div>
      
      {/* Description */}
      {rule.description && (
        <p className="text-sm text-gray-700 mb-4">{rule.description}</p>
      )}
      
      {/* Rule Type */}
      <div className="mb-4">
        <span className="text-sm font-medium text-gray-700">Type: </span>
        <span className="text-sm text-gray-900 font-mono bg-gray-100 px-2 py-0.5 rounded">
          {rule.rule_type}
        </span>
      </div>
      
      {/* Target Columns */}
      {rule.target_columns && rule.target_columns.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Target Columns:</p>
          <div className="flex flex-wrap gap-1">
            {rule.target_columns.map((column, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 text-xs font-mono bg-blue-50 text-blue-700 border border-blue-200 rounded"
              >
                {column}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Thresholds */}
      {rule.thresholds && rule.thresholds.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Thresholds:</p>
          <div className="space-y-1">
            {rule.thresholds.map((threshold, index) => (
              <div
                key={index}
                className="text-sm bg-gray-50 px-3 py-2 rounded border border-gray-200"
              >
                <span className="font-mono text-gray-900">{threshold.metric}</span>
                <span className="mx-2 text-gray-600">{operatorSymbols[threshold.operator] || threshold.operator}</span>
                <span className="font-semibold text-gray-900">{threshold.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Parameters */}
      {rule.parameters && Object.keys(rule.parameters).length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Parameters:</p>
          <div className="bg-gray-50 rounded border border-gray-200 p-3">
            <pre className="text-xs font-mono text-gray-800 overflow-x-auto">
              {JSON.stringify(rule.parameters, null, 2)}
            </pre>
          </div>
        </div>
      )}
      
      {/* Tags */}
      {rule.tags && rule.tags.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Tags:</p>
          <div className="flex flex-wrap gap-1">
            {rule.tags.map((tag, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 text-xs bg-purple-50 text-purple-700 border border-purple-200 rounded-full"
              >
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
