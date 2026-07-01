/**
 * Storage Service
 * Handles communication with storage provider endpoints
 */

import apiClient from './apiClient';
import type { ApiResponse } from './types';

export interface BucketStatus {
  name: string;
  exists: boolean;
  error?: string;
}

export interface StorageProviderStatus {
  provider: 'minio' | 's3';
  connected: boolean;
  buckets: {
    raw: BucketStatus;
    processed: BucketStatus;
    audit: BucketStatus;
  };
  region?: string;
  endpoint?: string;
  secure?: boolean;
}

export interface StorageProviderInfo {
  provider: 'minio' | 's3';
  available_providers: string[];
  config: {
    region?: string;
    endpoint?: string;
    secure?: boolean;
    buckets: {
      raw: string;
      processed: string;
      audit: string;
    };
  };
}

/**
 * Get the current storage provider status
 * Includes connection status and bucket availability
 */
export const getStorageProviderStatus = async (): Promise<StorageProviderStatus> => {
  const response = await apiClient.get<StorageProviderStatus>('/storage/status');
  return response.data;
};

/**
 * Get storage provider information
 * Returns configuration without checking connection
 */
export const getStorageProviderInfo = async (): Promise<StorageProviderInfo> => {
  const response = await apiClient.get<StorageProviderInfo>('/storage/info');
  return response.data;
};

export const storageService = {
  getStorageProviderStatus,
  getStorageProviderInfo,
};

export default storageService;
