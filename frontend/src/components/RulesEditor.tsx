import React, { useState, useEffect } from 'react';
import { Rule, RuleCreateRequest, RuleUpdateRequest, ValidationThreshold } from '@/services/rulesService';

export interface RulesEditorProps {
  rule?: Rule; // If provided, edit mode; otherwise, create mode
  ruleTypes: string[];
  availableTags: string[];
  onSave: (rule: RuleCreateRequest | RuleUpdateRequest) => Promise<void>;
  onCancel: () => void;
}

const SEVERITY_OPTIONS = ['error', 'warning', 'info'];

const OPERATORS = [
  { value: '>', label: '> (greater than)' },
  { value: '>=', label: '>= (greater than or equal)' },
  { value: '<', label: '< (less than)' },
  { value: '<=', label: '<= (less than or equal)' },
  { value: '==', label: '== (equal)' },
  { value: '!=', label: '!= (not equal)' },
];

const THRESHOLD_METRICS = ['pass_rate', 'failed_records', 'total_records'];

export default function RulesEditor({
  rule,
  ruleTypes,
  availableTags,
  onSave,
  onCancel
}: RulesEditorProps) {
  const isEditMode = !!rule;
  
  // Form state
  const [ruleId, setRuleId] = useState(rule?.rule_id || '');
  const [name, setName] = useState(rule?.name || '');
  const [description, setDescription] = useState(rule?.description || '');
  const [ruleType, setRuleType] = useState(rule?.rule_type || ruleTypes[0] || '');
  const [enabled, setEnabled] = useState(rule?.enabled ?? true);
  const [targetColumns, setTargetColumns] = useState(rule?.target_columns?.join(', ') || '');
  const [severity, setSeverity] = useState(rule?.severity || 'error');
  const [tags, setTags] = useState(rule?.tags?.join(', ') || '');
  
  // Thresholds state
  const [thresholds, setThresholds] = useState<ValidationThreshold[]>(
    rule?.thresholds || []
  );
  
  // Parameters state (JSON)
  const [parametersJson, setParametersJson] = useState(
    rule?.parameters ? JSON.stringify(rule.parameters, null, 2) : '{}'
  );
  
  // Validation errors
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    
    if (!isEditMode && !ruleId.trim()) {
      newErrors.ruleId = 'Rule ID is required';
    }
    
    if (!name.trim()) {
      newErrors.name = 'Name is required';
    }
    
    if (!ruleType) {
      newErrors.ruleType = 'Rule type is required';
    }
    
    // Validate JSON parameters
    try {
      JSON.parse(parametersJson);
    } catch (e) {
      newErrors.parametersJson = 'Invalid JSON format';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleAddThreshold = () => {
    setThresholds([
      ...thresholds,
      { metric: 'pass_rate', operator: '>=', value: 95.0 }
    ]);
  };
  
  const handleRemoveThreshold = (index: number) => {
    setThresholds(thresholds.filter((_, i) => i !== index));
  };
  
  const handleThresholdChange = (
    index: number,
    field: keyof ValidationThreshold,
    value: string | number
  ) => {
    const updated = [...thresholds];
    updated[index] = { ...updated[index], [field]: value };
    setThresholds(updated);
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSaving(true);
    
    try {
      const parsedParameters = JSON.parse(parametersJson);
      const parsedTargetColumns = targetColumns
        .split(',')
        .map(c => c.trim())
        .filter(c => c.length > 0);
      const parsedTags = tags
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0);
      
      if (isEditMode) {
        // Update mode - only send changed fields
        const updates: RuleUpdateRequest = {
          name,
          description: description || undefined,
          rule_type: ruleType,
          enabled,
          target_columns: parsedTargetColumns,
          parameters: parsedParameters,
          thresholds,
          severity,
          tags: parsedTags,
        };
        
        await onSave(updates);
      } else {
        // Create mode
        const newRule: RuleCreateRequest = {
          rule_id: ruleId,
          name,
          description: description || undefined,
          rule_type: ruleType,
          enabled,
          target_columns: parsedTargetColumns,
          parameters: parsedParameters,
          thresholds,
          severity,
          tags: parsedTags,
        };
        
        await onSave(newRule);
      }
    } catch (error) {
      console.error('Failed to save rule:', error);
      setErrors({ submit: error instanceof Error ? error.message : 'Failed to save rule' });
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Rule ID (only in create mode) */}
      {!isEditMode && (
        <div>
          <label htmlFor="ruleId" className="block text-sm font-medium text-gray-700">
            Rule ID *
          </label>
          <input
            type="text"
            id="ruleId"
            value={ruleId}
            onChange={(e) => setRuleId(e.target.value)}
            className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
              errors.ruleId
                ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }`}
            placeholder="e.g., null_check_customers"
          />
          {errors.ruleId && (
            <p className="mt-1 text-sm text-red-600">{errors.ruleId}</p>
          )}
        </div>
      )}
      
      {/* Name */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Name *
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
            errors.name
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder="e.g., Customer Null Check"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name}</p>
        )}
      </div>
      
      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Describe what this rule validates..."
        />
      </div>
      
      {/* Rule Type and Severity */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="ruleType" className="block text-sm font-medium text-gray-700">
            Rule Type *
          </label>
          <select
            id="ruleType"
            value={ruleType}
            onChange={(e) => setRuleType(e.target.value)}
            className={`mt-1 block w-full rounded-md shadow-sm sm:text-sm ${
              errors.ruleType
                ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
            }`}
          >
            {ruleTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          {errors.ruleType && (
            <p className="mt-1 text-sm text-red-600">{errors.ruleType}</p>
          )}
        </div>
        
        <div>
          <label htmlFor="severity" className="block text-sm font-medium text-gray-700">
            Severity
          </label>
          <select
            id="severity"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            {SEVERITY_OPTIONS.map(sev => (
              <option key={sev} value={sev}>{sev}</option>
            ))}
          </select>
        </div>
      </div>
      
      {/* Enabled */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="enabled"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <label htmlFor="enabled" className="ml-2 block text-sm text-gray-700">
          Enable this rule
        </label>
      </div>
      
      {/* Target Columns */}
      <div>
        <label htmlFor="targetColumns" className="block text-sm font-medium text-gray-700">
          Target Columns
        </label>
        <input
          type="text"
          id="targetColumns"
          value={targetColumns}
          onChange={(e) => setTargetColumns(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="column1, column2, column3 (comma-separated)"
        />
        <p className="mt-1 text-xs text-gray-500">
          Comma-separated list of columns. Leave empty to apply to all columns.
        </p>
      </div>
      
      {/* Thresholds */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-gray-700">
            Validation Thresholds
          </label>
          <button
            type="button"
            onClick={handleAddThreshold}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            + Add Threshold
          </button>
        </div>
        
        {thresholds.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No thresholds configured</p>
        ) : (
          <div className="space-y-3">
            {thresholds.map((threshold, index) => (
              <div key={index} className="flex items-center space-x-2 p-3 bg-gray-50 rounded border border-gray-200">
                <select
                  value={threshold.metric}
                  onChange={(e) => handleThresholdChange(index, 'metric', e.target.value)}
                  className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  {THRESHOLD_METRICS.map(metric => (
                    <option key={metric} value={metric}>{metric}</option>
                  ))}
                </select>
                
                <select
                  value={threshold.operator}
                  onChange={(e) => handleThresholdChange(index, 'operator', e.target.value)}
                  className="w-40 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  {OPERATORS.map(op => (
                    <option key={op.value} value={op.value}>{op.label}</option>
                  ))}
                </select>
                
                <input
                  type="number"
                  step="0.01"
                  value={threshold.value}
                  onChange={(e) => handleThresholdChange(index, 'value', parseFloat(e.target.value))}
                  className="w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
                
                <button
                  type="button"
                  onClick={() => handleRemoveThreshold(index)}
                  className="text-red-600 hover:text-red-700"
                  title="Remove threshold"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Parameters (JSON) */}
      <div>
        <label htmlFor="parameters" className="block text-sm font-medium text-gray-700">
          Parameters (JSON)
        </label>
        <textarea
          id="parameters"
          value={parametersJson}
          onChange={(e) => setParametersJson(e.target.value)}
          rows={6}
          className={`mt-1 block w-full rounded-md shadow-sm font-mono text-xs ${
            errors.parametersJson
              ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
              : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500'
          }`}
          placeholder='{\n  "key": "value"\n}'
        />
        {errors.parametersJson && (
          <p className="mt-1 text-sm text-red-600">{errors.parametersJson}</p>
        )}
      </div>
      
      {/* Tags */}
      <div>
        <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
          Tags
        </label>
        <input
          type="text"
          id="tags"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="tag1, tag2, tag3 (comma-separated)"
        />
        {availableTags.length > 0 && (
          <p className="mt-1 text-xs text-gray-500">
            Existing tags: {availableTags.join(', ')}
          </p>
        )}
      </div>
      
      {/* Submit Error */}
      {errors.submit && (
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{errors.submit}</p>
        </div>
      )}
      
      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSaving}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSaving ? 'Saving...' : isEditMode ? 'Update Rule' : 'Create Rule'}
        </button>
      </div>
    </form>
  );
}
