/**
 * Schema Drift API Service
 * 
 * Handles all API calls related to schema drift detection and management
 */

import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Column Definition
 */
export interface ColumnDefinition {
  name: string;
  data_type: string;
  nullable?: boolean;
  position?: number;
}

/**
 * Schema Definition
 */
export interface SchemaDefinition {
  columns: ColumnDefinition[];
}

/**
 * Schema Version
 */
export interface SchemaVersion {
  id: number;
  dataset_name: string;
  version_number: number;
  version_hash: string;
  schema_definition: SchemaDefinition;
  detected_at: string;
  source?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

/**
 * Schema Drift Changes
 */
export interface SchemaDriftChanges {
  added_columns: Array<{ name: string; data_type: string; nullable?: boolean; position?: number }>;
  removed_columns: Array<{ name: string; data_type: string; nullable?: boolean; position?: number }>;
  type_changes: Array<{ name: string; previous_type: string; current_type: string }>;
  nullability_changes: Array<{ name: string; previous_nullable: boolean; current_nullable: boolean }>;
  position_changes: Array<{ name: string; previous_position: number; current_position: number }>;
}

/**
 * Schema Drift Record
 */
export interface SchemaDrift {
  id: number;
  dataset_name: string;
  previous_version_id?: number;
  current_version_id: number;
  drift_type: string;
  severity: 'info' | 'warning' | 'critical';
  changes: SchemaDriftChanges;
  detected_at: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Drift Alert Response
 */
export interface DriftAlert {
  dataset_name: string;
  total_drifts: number;
  unacknowledged_count: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  latest_drift?: SchemaDrift;
}

/**
 * Schema Timeline Item
 */
export interface SchemaTimelineItem {
  version_number: number;
  detected_at: string;
  source?: string;
  drift_occurred: boolean;
  drift_type?: string;
  severity?: string;
}

/**
 * Register Schema Request
 */
export interface RegisterSchemaRequest {
  dataset_name: string;
  schema_definition: SchemaDefinition;
  source?: string;
  metadata?: Record<string, any>;
}

/**
 * Register Schema Response
 */
export interface RegisterSchemaResponse {
  schema_version: SchemaVersion;
  drift_detected: boolean;
  drift_record?: SchemaDrift;
}

/**
 * Acknowledge Drift Request
 */
export interface AcknowledgeDriftRequest {
  acknowledged_by: string;
  notes?: string;
}

/**
 * Schema Comparison Request
 */
export interface SchemaComparisonRequest {
  dataset_name: string;
  version1: number;
  version2: number;
}

/**
 * Schema Comparison Response
 */
export interface SchemaComparisonResponse {
  dataset_name: string;
  version1: number;
  version2: number;
  version1_detected_at: string;
  version2_detected_at: string;
  has_drift: boolean;
  drift_type?: string;
  severity?: string;
  changes: SchemaDriftChanges;
}

const schemaDriftService = {
  /**
   * Register a new schema version
   */
  async registerSchema(request: RegisterSchemaRequest): Promise<RegisterSchemaResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/schema-drift/register`, request);
    return response.data;
  },

  /**
   * Get all schema versions for a dataset
   */
  async getSchemaVersions(datasetName: string, limit: number = 100): Promise<SchemaVersion[]> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/versions/${datasetName}`, {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Get the latest schema version for a dataset
   */
  async getLatestVersion(datasetName: string): Promise<SchemaVersion> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/versions/${datasetName}/latest`);
    return response.data;
  },

  /**
   * Get a specific schema version
   */
  async getSchemaVersion(datasetName: string, versionNumber: number): Promise<SchemaVersion> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/versions/${datasetName}/${versionNumber}`);
    return response.data;
  },

  /**
   * Get drift history with optional filters
   */
  async getDriftHistory(params?: {
    dataset_name?: string;
    severity?: 'info' | 'warning' | 'critical';
    acknowledged?: boolean;
    limit?: number;
  }): Promise<SchemaDrift[]> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/drift-history`, { params });
    return response.data;
  },

  /**
   * Get drift history for a specific dataset
   */
  async getDatasetDriftHistory(datasetName: string, limit: number = 100): Promise<SchemaDrift[]> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/drift-history/${datasetName}`, {
      params: { limit }
    });
    return response.data;
  },

  /**
   * Acknowledge a drift event
   */
  async acknowledgeDrift(driftId: number, request: AcknowledgeDriftRequest): Promise<SchemaDrift> {
    const response = await axios.post(
      `${API_BASE_URL}/api/schema-drift/drift-history/${driftId}/acknowledge`,
      request
    );
    return response.data;
  },

  /**
   * Compare two schema versions
   */
  async compareSchemas(request: SchemaComparisonRequest): Promise<SchemaComparisonResponse> {
    const response = await axios.post(`${API_BASE_URL}/api/schema-drift/compare`, request);
    return response.data;
  },

  /**
   * Get drift alerts for a dataset
   */
  async getDriftAlerts(datasetName: string): Promise<DriftAlert> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/alerts/${datasetName}`);
    return response.data;
  },

  /**
   * Get schema timeline for a dataset
   */
  async getSchemaTimeline(datasetName: string, limit: number = 50): Promise<SchemaTimelineItem[]> {
    const response = await axios.get(`${API_BASE_URL}/api/schema-drift/timeline/${datasetName}`, {
      params: { limit }
    });
    return response.data;
  }
};

export default schemaDriftService;
