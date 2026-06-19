import React, { useState, useEffect } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import { LoadingSpinner, Alert } from '@/components';
import RulesEditor from '@/components/RulesEditor';
import RuleActivationToggle from '@/components/RuleActivationToggle';
import RulePreview from '@/components/RulePreview';
import RulesService, {
  Rule,
  RuleListResponse,
  RuleCreateRequest,
  RuleUpdateRequest
} from '@/services/rulesService';

type ViewMode = 'list' | 'create' | 'edit' | 'preview';

export default function RulesManagementPage() {
  // Data state
  const [rulesData, setRulesData] = useState<RuleListResponse | null>(null);
  const [ruleTypes, setRuleTypes] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  
  // UI state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [filterEnabled, setFilterEnabled] = useState<'all' | 'enabled' | 'disabled'>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterTag, setFilterTag] = useState<string>('all');
  
  // Load initial data
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [rules, types, tags] = await Promise.all([
        RulesService.getAllRules(),
        RulesService.getRuleTypes(),
        RulesService.getAllTags(),
      ]);
      
      setRulesData(rules);
      setRuleTypes(types);
      setAvailableTags(tags);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load rules');
    } finally {
      setLoading(false);
    }
  };
  
  const handleCreateRule = async (ruleRequest: RuleCreateRequest | RuleUpdateRequest) => {
    try {
      await RulesService.createRule(ruleRequest as RuleCreateRequest);
      setSuccess('Rule created successfully');
      setViewMode('list');
      await loadData();
    } catch (err) {
      throw err; // Let the editor handle the error display
    }
  };
  
  const handleUpdateRule = async (ruleRequest: RuleCreateRequest | RuleUpdateRequest) => {
    if (!selectedRule) return;
    
    try {
      await RulesService.updateRule(selectedRule.rule_id, ruleRequest as RuleUpdateRequest);
      setSuccess('Rule updated successfully');
      setViewMode('list');
      setSelectedRule(null);
      await loadData();
    } catch (err) {
      throw err; // Let the editor handle the error display
    }
  };
  
  const handleDeleteRule = async (ruleId: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) {
      return;
    }
    
    try {
      await RulesService.deleteRule(ruleId);
      setSuccess('Rule deleted successfully');
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };
  
  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      await RulesService.toggleRule(ruleId, enabled);
      setSuccess(`Rule ${enabled ? 'enabled' : 'disabled'} successfully`);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle rule');
      throw err; // Re-throw to let toggle component handle state revert
    }
  };
  
  const handleEditRule = (rule: Rule) => {
    setSelectedRule(rule);
    setViewMode('edit');
  };
  
  const handlePreviewRule = (rule: Rule) => {
    setSelectedRule(rule);
    setViewMode('preview');
  };
  
  const handleCancelEdit = () => {
    setSelectedRule(null);
    setViewMode('list');
  };
  
  // Filter rules based on current filters
  const filteredRules = rulesData?.rules.filter(rule => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        rule.name.toLowerCase().includes(query) ||
        rule.rule_id.toLowerCase().includes(query) ||
        rule.description?.toLowerCase().includes(query) ||
        rule.tags.some(tag => tag.toLowerCase().includes(query));
      
      if (!matchesSearch) return false;
    }
    
    // Enabled filter
    if (filterEnabled === 'enabled' && !rule.enabled) return false;
    if (filterEnabled === 'disabled' && rule.enabled) return false;
    
    // Type filter
    if (filterType !== 'all' && rule.rule_type !== filterType) return false;
    
    // Tag filter
    if (filterTag !== 'all' && !rule.tags.includes(filterTag)) return false;
    
    return true;
  }) || [];
  
  // Clear success message after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);
  
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Validation Rules Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Configure and manage validation rules for data quality checks
          </p>
        </div>
        
        {/* Alerts */}
        {error && (
          <Alert
            type="error"
            message={error}
            onDismiss={() => setError(null)}
            className="mb-4"
          />
        )}
        
        {success && (
          <Alert
            type="success"
            message={success}
            onDismiss={() => setSuccess(null)}
            className="mb-4"
          />
        )}
        
        {/* Loading State */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        )}
        
        {/* Content */}
        {!loading && (
          <>
            {viewMode === 'list' && (
              <>
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-medium text-gray-500">Total Rules</h3>
                    <p className="mt-2 text-3xl font-semibold text-gray-900">
                      {rulesData?.total_rules || 0}
                    </p>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-medium text-gray-500">Enabled</h3>
                    <p className="mt-2 text-3xl font-semibold text-green-600">
                      {rulesData?.enabled_rules || 0}
                    </p>
                  </div>
                  
                  <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-sm font-medium text-gray-500">Disabled</h3>
                    <p className="mt-2 text-3xl font-semibold text-gray-500">
                      {rulesData?.disabled_rules || 0}
                    </p>
                  </div>
                </div>
                
                {/* Filters and Actions */}
                <div className="bg-white rounded-lg shadow p-4 mb-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                    {/* Search */}
                    <div className="flex-1 max-w-lg">
                      <input
                        type="text"
                        placeholder="Search rules..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      />
                    </div>
                    
                    {/* Filters */}
                    <div className="flex items-center space-x-2">
                      <select
                        value={filterEnabled}
                        onChange={(e) => setFilterEnabled(e.target.value as any)}
                        className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        <option value="all">All Status</option>
                        <option value="enabled">Enabled</option>
                        <option value="disabled">Disabled</option>
                      </select>
                      
                      <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        <option value="all">All Types</option>
                        {ruleTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                      
                      <select
                        value={filterTag}
                        onChange={(e) => setFilterTag(e.target.value)}
                        className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        <option value="all">All Tags</option>
                        {availableTags.map(tag => (
                          <option key={tag} value={tag}>{tag}</option>
                        ))}
                      </select>
                      
                      <button
                        onClick={() => setViewMode('create')}
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        + Create Rule
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Rules Table */}
                <div className="bg-white shadow rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Rule
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Type
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Severity
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Thresholds
                        </th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredRules.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-6 py-12 text-center text-sm text-gray-500">
                            No rules found matching your criteria
                          </td>
                        </tr>
                      ) : (
                        filteredRules.map((rule) => (
                          <tr key={rule.rule_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4">
                              <div className="text-sm font-medium text-gray-900">
                                {rule.name}
                              </div>
                              <div className="text-sm text-gray-500">{rule.rule_id}</div>
                            </td>
                            <td className="px-6 py-4">
                              <span className="text-sm font-mono text-gray-700">
                                {rule.rule_type}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`
                                px-2 py-1 text-xs font-medium rounded-full
                                ${rule.severity === 'error' ? 'bg-red-100 text-red-800' : ''}
                                ${rule.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' : ''}
                                ${rule.severity === 'info' ? 'bg-blue-100 text-blue-800' : ''}
                              `}>
                                {rule.severity}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <RuleActivationToggle
                                ruleId={rule.rule_id}
                                enabled={rule.enabled}
                                ruleName={rule.name}
                                onToggle={handleToggleRule}
                              />
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500">
                              {rule.thresholds.length > 0 ? (
                                <span>{rule.thresholds.length} configured</span>
                              ) : (
                                <span className="text-gray-400">None</span>
                              )}
                            </td>
                            <td className="px-6 py-4 text-right text-sm font-medium space-x-2">
                              <button
                                onClick={() => handlePreviewRule(rule)}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                View
                              </button>
                              <button
                                onClick={() => handleEditRule(rule)}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteRule(rule.rule_id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            
            {viewMode === 'create' && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Create New Rule</h2>
                <RulesEditor
                  ruleTypes={ruleTypes}
                  availableTags={availableTags}
                  onSave={handleCreateRule}
                  onCancel={handleCancelEdit}
                />
              </div>
            )}
            
            {viewMode === 'edit' && selectedRule && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">Edit Rule</h2>
                <RulesEditor
                  rule={selectedRule}
                  ruleTypes={ruleTypes}
                  availableTags={availableTags}
                  onSave={handleUpdateRule}
                  onCancel={handleCancelEdit}
                />
              </div>
            )}
            
            {viewMode === 'preview' && selectedRule && (
              <div>
                <button
                  onClick={() => setViewMode('list')}
                  className="mb-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  ← Back to Rules List
                </button>
                <RulePreview rule={selectedRule} />
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
