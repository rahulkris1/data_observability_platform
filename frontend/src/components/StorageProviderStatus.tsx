import React, { useEffect, useState } from 'react';
import { storageService, StorageProviderStatus } from '../services/storageService';

/**
 * StorageProviderStatus Component
 * Displays the active storage provider (MinIO or S3) with connection status
 */
const StorageProviderStatusComponent: React.FC = () => {
  const [status, setStatus] = useState<StorageProviderStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await storageService.getStorageProviderStatus();
        setStatus(data);
      } catch (err) {
        console.error('Failed to fetch storage provider status:', err);
        setError('Failed to load storage provider status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    
    // Refresh status every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-sm text-gray-600">Loading storage status...</span>
        </div>
      </div>
    );
  }

  if (error || !status) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-red-200 p-6">
        <div className="flex items-center space-x-3">
          <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-sm text-red-700">{error || 'Storage status unavailable'}</span>
        </div>
      </div>
    );
  }

  const isS3 = status.provider === 's3';
  const isMinio = status.provider === 'minio';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
        Storage Provider Status
      </h3>

      {/* Provider Type */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Active Provider:</span>
          <div className="flex items-center space-x-2">
            {isS3 && (
              <>
                <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                <span className="text-sm font-bold text-orange-600">AWS S3</span>
              </>
            )}
            {isMinio && (
              <>
                <svg className="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                <span className="text-sm font-bold text-purple-600">MinIO</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="mb-4 pb-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Connection:</span>
          <div className="flex items-center space-x-2">
            {status.connected ? (
              <>
                <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-700">Connected</span>
              </>
            ) : (
              <>
                <div className="h-2 w-2 bg-red-500 rounded-full"></div>
                <span className="text-sm font-medium text-red-700">Disconnected</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Region/Endpoint */}
      {status.region && (
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">AWS Region:</span>
            <span className="text-sm text-gray-900 font-mono">{status.region}</span>
          </div>
        </div>
      )}
      
      {status.endpoint && (
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Endpoint:</span>
            <span className="text-sm text-gray-900 font-mono text-right truncate ml-2" title={status.endpoint}>
              {status.endpoint}
            </span>
          </div>
        </div>
      )}

      {/* Bucket Status */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Buckets:</h4>
        <div className="space-y-2">
          {Object.entries(status.buckets).map(([type, bucket]) => (
            <div key={type} className="flex items-center justify-between text-sm">
              <span className="text-gray-600 capitalize">{type}:</span>
              <div className="flex items-center space-x-2">
                <span className="text-gray-900 font-mono text-xs">{bucket.name}</span>
                {bucket.exists ? (
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Info Footer */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          {isS3 && 'Using AWS S3 for object storage in production'}
          {isMinio && 'Using MinIO for local object storage development'}
        </p>
      </div>
    </div>
  );
};

export default StorageProviderStatusComponent;
