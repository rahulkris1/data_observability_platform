/**
 * GlueJobStatusCard Component
 * 
 * Displays real-time status of a specific AWS Glue job run
 * with execution details and progress indicators.
 */

import React, { useState, useEffect } from 'react';
import { glueService, GlueJobRun } from '../services/glueService';

interface GlueJobStatusCardProps {
  jobRunId: string;
  jobName?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
  onJobComplete?: (job: GlueJobRun) => void;
}

export default function GlueJobStatusCard({
  jobRunId,
  jobName,
  autoRefresh = true,
  refreshInterval = 10000, // 10 seconds
  onJobComplete,
}: GlueJobStatusCardProps) {
  const [jobRun, setJobRun] = useState<GlueJobRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadJobStatus();

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadJobStatus();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [jobRunId, jobName, autoRefresh, refreshInterval]);

  useEffect(() => {
    // Check if job completed and trigger callback
    if (jobRun && onJobComplete) {
      const isComplete = ['SUCCEEDED', 'FAILED', 'STOPPED', 'TIMEOUT'].includes(jobRun.state);
      if (isComplete) {
        onJobComplete(jobRun);
      }
    }
  }, [jobRun, onJobComplete]);

  const loadJobStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const status = await glueService.getGlueJobStatus(jobRunId, jobName);
      setJobRun(status);
    } catch (err) {
      console.error('Failed to load job status:', err);
      setError('Failed to load job status');
    } finally {
      setLoading(false);
    }
  };

  const getStateColor = (state: string): string => {
    switch (state) {
      case 'SUCCEEDED':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'FAILED':
      case 'TIMEOUT':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'RUNNING':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'STOPPED':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  const getStateIcon = (state: string) => {
    switch (state) {
      case 'SUCCEEDED':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'FAILED':
      case 'TIMEOUT':
        return (
          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'RUNNING':
        return (
          <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        );
      default:
        return (
          <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleString();
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading && !jobRun) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">Loading job status...</p>
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

  if (!jobRun) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStateIcon(jobRun.state)}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{jobRun.job_name}</h3>
              <p className="text-sm text-gray-500">Run ID: {jobRun.job_run_id.slice(0, 16)}...</p>
            </div>
          </div>
          <div className={`px-3 py-1 rounded-full border font-semibold text-sm ${getStateColor(jobRun.state)}`}>
            {jobRun.state}
          </div>
        </div>
      </div>

      {/* Job Details */}
      <div className="p-6 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-gray-600 font-medium">Started</span>
          <span className="text-gray-900 text-sm">{formatTimestamp(jobRun.started_on)}</span>
        </div>

        {jobRun.completed_on && (
          <div className="flex items-center justify-between">
            <span className="text-gray-600 font-medium">Completed</span>
            <span className="text-gray-900 text-sm">{formatTimestamp(jobRun.completed_on)}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <span className="text-gray-600 font-medium">Execution Time</span>
          <span className="text-gray-900 text-sm font-semibold">{formatDuration(jobRun.execution_time)}</span>
        </div>

        {/* Error Message */}
        {jobRun.error_message && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm font-semibold text-red-800 mb-1">Error:</p>
            <p className="text-sm text-red-700">{jobRun.error_message}</p>
          </div>
        )}
      </div>

      {/* Refresh Indicator */}
      {autoRefresh && jobRun.state === 'RUNNING' && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center justify-center space-x-2 text-blue-600 text-sm">
            <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Auto-refreshing every {refreshInterval / 1000}s</span>
          </div>
        </div>
      )}
    </div>
  );
}
