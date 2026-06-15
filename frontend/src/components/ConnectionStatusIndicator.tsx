import React, { useState, useEffect } from 'react';

export default function ConnectionStatusIndicator() {
  const [postgresStatus, setPostgresStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [warehouseServiceStatus, setWarehouseServiceStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');

  useEffect(() => {
    checkConnectionStatus();
    
    // Check status every 30 seconds
    const interval = setInterval(checkConnectionStatus, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const checkConnectionStatus = async () => {
    // Check PostgreSQL connection via health endpoint
    try {
      const healthResponse = await fetch('/health');
      if (healthResponse.ok) {
        setPostgresStatus('connected');
      } else {
        setPostgresStatus('disconnected');
      }
    } catch (error) {
      setPostgresStatus('disconnected');
    }

    // Check warehouse service status
    try {
      const warehouseResponse = await fetch('/api/v1/warehouse/statistics');
      if (warehouseResponse.ok) {
        setWarehouseServiceStatus('healthy');
      } else {
        setWarehouseServiceStatus('unhealthy');
      }
    } catch (error) {
      setWarehouseServiceStatus('unhealthy');
    }
  };

  const getStatusIcon = (status: 'connected' | 'disconnected' | 'checking' | 'healthy' | 'unhealthy') => {
    if (status === 'checking') {
      return (
        <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
      );
    }
    
    if (status === 'connected' || status === 'healthy') {
      return (
        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
      );
    }
    
    return (
      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
    );
  };

  const getStatusText = (status: 'connected' | 'disconnected' | 'checking' | 'healthy' | 'unhealthy') => {
    if (status === 'checking') return 'Checking...';
    if (status === 'connected' || status === 'healthy') return 'Connected';
    if (status === 'disconnected' || status === 'unhealthy') return 'Disconnected';
    return 'Unknown';
  };

  const getStatusColor = (status: 'connected' | 'disconnected' | 'checking' | 'healthy' | 'unhealthy') => {
    if (status === 'checking') return 'text-yellow-700';
    if (status === 'connected' || status === 'healthy') return 'text-green-700';
    return 'text-red-700';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-6">
          {/* PostgreSQL Status */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              {getStatusIcon(postgresStatus)}
              <div>
                <div className="text-sm font-medium text-gray-900">PostgreSQL</div>
                <div className={`text-xs ${getStatusColor(postgresStatus)}`}>
                  {getStatusText(postgresStatus)}
                </div>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="h-8 w-px bg-gray-200"></div>

          {/* Warehouse Service Status */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              {getStatusIcon(warehouseServiceStatus)}
              <div>
                <div className="text-sm font-medium text-gray-900">Warehouse Service</div>
                <div className={`text-xs ${getStatusColor(warehouseServiceStatus)}`}>
                  {getStatusText(warehouseServiceStatus)}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Overall Status Badge */}
        <div>
          {postgresStatus === 'connected' && warehouseServiceStatus === 'healthy' ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              All Systems Operational
            </span>
          ) : postgresStatus === 'checking' || warehouseServiceStatus === 'checking' ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
              <svg className="w-4 h-4 mr-1 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Checking Status
            </span>
          ) : (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Service Issues Detected
            </span>
          )}
        </div>
      </div>

      {/* Warning message if any service is down */}
      {(postgresStatus === 'disconnected' || warehouseServiceStatus === 'unhealthy') && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h4 className="text-sm font-medium text-red-800">Connection Issues</h4>
              <p className="text-xs text-red-700 mt-1">
                Some services are not responding. Warehouse operations may be unavailable.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
