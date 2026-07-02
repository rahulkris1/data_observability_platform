/**
 * CloudExecutionStatus Component
 * 
 * Displays AWS Glue job execution history with status,
 * execution times, and detailed job information.
 */

import React, { useState, useEffect } from 'react';
import { glueService, GlueJobRun } from '../services/glueService';

interface CloudExecutionStatusProps {
  jobName?: string;
  maxResults?: number;
  autoRefresh?: boolean;
  refreshInterval?: number; // in milliseconds
}

export default function CloudExecutionStatus({
  jobName,
  maxResults = 10,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}: CloudExecutionStatusProps) {
  const [jobRuns, setJobRuns] = useState<GlueJobRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<GlueJobRun | null>(null);

  useEffect(() => {
    loadJobHistory();

    if (autoRefresh) {
      const interval = setInterval(loadJobHistory, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [jobName, maxResults, autoRefresh, refreshInterval]);

  const loadJobHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await glueService.getGlueJobHistory(jobName, maxResults);
      setJobRuns(response.job_runs);
    } catch (err) {
      console.error('Failed to load job history:', err);
      setError('Failed to load job history');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadJobHistory();
  };

  const getStateColor = (state: string): string => {
    switch (state) {
      case 'SUCCEEDED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
      case 'TIMEOUT':
        return 'bg-red-100 text-red-800';
      case 'RUNNING':
        return 'bg-blue-100 text-blue-800';
      case 'STOPPED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  if (loading && jobRuns.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center space-x-3">
          <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-600">Loading job history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">AWS Glue Job History</h3>
              <p className="text-sm text-gray-500">Recent executions and status</p>
            </div>
          </div>
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-6">
          <div className="flex items-center space-x-3 text-red-600 bg-red-50 border border-red-200 rounded-md p-4">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && jobRuns.length === 0 && (
        <div className="p-12 text-center">
          <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <p className="text-gray-500 text-lg font-medium">No job runs found</p>
          <p className="text-gray-400 text-sm mt-1">Job execution history will appear here</p>
        </div>
      )}

      {/* Job Runs Table */}
      {!error && jobRuns.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Job Run ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Started
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Duration
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {jobRuns.map((job) => (
                <tr key={job.job_run_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {job.job_run_id.slice(0, 16)}...
                        </div>
                        <div className="text-sm text-gray-500">{job.job_name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStateColor(job.state)}`}>
                      {job.state}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(job.started_on)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                    {formatDuration(job.execution_time)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => setSelectedJob(job)}
                      className="text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Loading Indicator */}
      {loading && jobRuns.length > 0 && (
        <div className="px-6 py-3 bg-blue-50 border-t border-blue-200">
          <div className="flex items-center justify-center space-x-2 text-blue-600 text-sm">
            <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <span>Refreshing...</span>
          </div>
        </div>
      )}

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Job Run Details</h3>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Job Run ID</label>
                <p className="text-sm text-gray-900 mt-1 font-mono">{selectedJob.job_run_id}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Job Name</label>
                <p className="text-sm text-gray-900 mt-1">{selectedJob.job_name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Status</label>
                <p className="mt-1">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStateColor(selectedJob.state)}`}>
                    {selectedJob.state}
                  </span>
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Started On</label>
                <p className="text-sm text-gray-900 mt-1">{formatTimestamp(selectedJob.started_on)}</p>
              </div>
              {selectedJob.completed_on && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Completed On</label>
                  <p className="text-sm text-gray-900 mt-1">{formatTimestamp(selectedJob.completed_on)}</p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium text-gray-600">Execution Time</label>
                <p className="text-sm text-gray-900 mt-1">{formatDuration(selectedJob.execution_time)}</p>
              </div>
              {selectedJob.error_message && (
                <div>
                  <label className="text-sm font-medium text-gray-600">Error Message</label>
                  <div className="mt-1 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm text-red-700">{selectedJob.error_message}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
