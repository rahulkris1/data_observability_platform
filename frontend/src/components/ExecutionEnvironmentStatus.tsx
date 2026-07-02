/**
 * ExecutionEnvironmentStatus Component
 * 
 * Displays the current execution environment (Local or AWS Glue)
 * with configuration status and health indicators.
 */

import React, { useState, useEffect } from 'react';
import { glueService, ExecutionEnvironment, GlueConfigValidation } from '../services/glueService';

export default function ExecutionEnvironmentStatus() {
  const [environment, setEnvironment] = useState<ExecutionEnvironment | null>(null);
  const [validation, setValidation] = useState<GlueConfigValidation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadEnvironmentInfo();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadEnvironmentInfo, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadEnvironmentInfo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [envData, validationData] = await Promise.all([
        glueService.getExecutionEnvironment(),
        glueService.validateGlueConfiguration(),
      ]);
      
      setEnvironment(envData);
      setValidation(validationData);
    } catch (err) {
      console.error('Failed to load environment info:', err);
      setError('Failed to load execution environment');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !environment) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">Loading execution environment...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-red-200">
        <div className="flex items-center space-x-3 text-red-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!environment) return null;

  const isGlueMode = environment.execution_mode.toLowerCase() === 'glue';
  const isHealthy = validation?.is_valid ?? false;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`w-3 h-3 rounded-full ${isHealthy ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
            <h3 className="text-lg font-semibold text-gray-900">Execution Environment</h3>
          </div>
          <button
            onClick={loadEnvironmentInfo}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      <div className="p-6 space-y-4">
        {/* Execution Mode */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600 font-medium">Execution Mode</span>
          <div className="flex items-center space-x-2">
            {isGlueMode ? (
              <>
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                </svg>
                <span className="text-blue-600 font-semibold">AWS Glue</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span className="text-gray-600 font-semibold">Local</span>
              </>
            )}
          </div>
        </div>

        {/* Storage Provider */}
        <div className="flex items-center justify-between">
          <span className="text-gray-600 font-medium">Storage Provider</span>
          <span className="text-gray-900 font-semibold capitalize">{environment.storage_provider}</span>
        </div>

        {/* AWS Region (if Glue mode) */}
        {isGlueMode && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">AWS Region</span>
            <span className="text-gray-900 font-semibold">{environment.aws_region}</span>
          </div>
        )}

        {/* Glue Job Name (if Glue mode) */}
        {isGlueMode && environment.glue_job_name && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Glue Job Name</span>
            <span className="text-gray-900 font-semibold text-sm">{environment.glue_job_name}</span>
          </div>
        )}

        {/* Glue Availability Status */}
        {isGlueMode && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Glue Service</span>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${environment.glue_available ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className={`text-sm font-semibold ${environment.glue_available ? 'text-green-600' : 'text-red-600'}`}>
                {environment.glue_available ? 'Available' : 'Unavailable'}
              </span>
            </div>
          </div>
        )}

        {/* Configuration Status */}
        {validation && (
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-start justify-between mb-2">
              <span className="text-gray-600 font-medium">Configuration</span>
              <span className={`text-sm font-semibold ${isHealthy ? 'text-green-600' : 'text-yellow-600'}`}>
                {isHealthy ? '✓ Valid' : '⚠ Issues Found'}
              </span>
            </div>

            {/* Issues */}
            {validation.issues.length > 0 && (
              <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm font-semibold text-red-800 mb-1">Issues:</p>
                <ul className="list-disc list-inside space-y-1">
                  {validation.issues.map((issue, index) => (
                    <li key={index} className="text-sm text-red-700">{issue}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Warnings */}
            {validation.warnings.length > 0 && (
              <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <p className="text-sm font-semibold text-yellow-800 mb-1">Warnings:</p>
                <ul className="list-disc list-inside space-y-1">
                  {validation.warnings.map((warning, index) => (
                    <li key={index} className="text-sm text-yellow-700">{warning}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
