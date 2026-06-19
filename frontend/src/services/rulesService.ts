/**
 * Rules Management Service
 * 
 * API client for validation rules management
 */

export interface ValidationThreshold {
  metric: string;
  operator: string;
  value: number;
}

export interface Rule {
  rule_id: string;
  name: string;
  description?: string;
  rule_type: string;
  enabled: boolean;
  target_columns: string[];
  parameters: Record<string, any>;
  thresholds: ValidationThreshold[];
  severity: string;
  tags: string[];
}

export interface RuleListResponse {
  version: string;
  total_rules: number;
  enabled_rules: number;
  disabled_rules: number;
  rules: Rule[];
}

export interface RuleCreateRequest {
  rule_id: string;
  name: string;
  description?: string;
  rule_type: string;
  enabled?: boolean;
  target_columns?: string[];
  parameters?: Record<string, any>;
  thresholds?: ValidationThreshold[];
  severity?: string;
  tags?: string[];
}

export interface RuleUpdateRequest {
  name?: string;
  description?: string;
  rule_type?: string;
  enabled?: boolean;
  target_columns?: string[];
  parameters?: Record<string, any>;
  thresholds?: ValidationThreshold[];
  severity?: string;
  tags?: string[];
}

export interface RuleToggleResponse {
  rule_id: string;
  enabled: boolean;
  message: string;
}

const API_BASE_URL = '/api/v1/rules';

export class RulesService {
  /**
   * Fetch all validation rules
   */
  static async getAllRules(enabledOnly: boolean = false): Promise<RuleListResponse> {
    const params = new URLSearchParams();
    if (enabledOnly) {
      params.append('enabled_only', 'true');
    }
    
    const response = await fetch(`${API_BASE_URL}?${params}`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch rules');
    }
    
    return response.json();
  }
  
  /**
   * Fetch a specific rule by ID
   */
  static async getRule(ruleId: string): Promise<Rule> {
    const response = await fetch(`${API_BASE_URL}/${ruleId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Rule '${ruleId}' not found`);
      }
      throw new Error('Failed to fetch rule');
    }
    
    return response.json();
  }
  
  /**
   * Create a new validation rule
   */
  static async createRule(rule: RuleCreateRequest): Promise<Rule> {
    const response = await fetch(API_BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(rule),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to create rule');
    }
    
    return response.json();
  }
  
  /**
   * Update an existing rule
   */
  static async updateRule(ruleId: string, updates: RuleUpdateRequest): Promise<Rule> {
    const response = await fetch(`${API_BASE_URL}/${ruleId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to update rule');
    }
    
    return response.json();
  }
  
  /**
   * Delete a rule
   */
  static async deleteRule(ruleId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/${ruleId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to delete rule');
    }
  }
  
  /**
   * Toggle rule enabled/disabled status
   */
  static async toggleRule(ruleId: string, enabled: boolean): Promise<RuleToggleResponse> {
    const response = await fetch(`${API_BASE_URL}/${ruleId}/toggle`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ enabled }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to toggle rule');
    }
    
    return response.json();
  }
  
  /**
   * Get available rule types
   */
  static async getRuleTypes(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/types/list`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch rule types');
    }
    
    return response.json();
  }
  
  /**
   * Get all unique tags
   */
  static async getAllTags(): Promise<string[]> {
    const response = await fetch(`${API_BASE_URL}/tags/list`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch tags');
    }
    
    return response.json();
  }
}

export default RulesService;
