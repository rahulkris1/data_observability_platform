import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import ProfilingSummaryCards from '../components/ProfilingSummaryCards';
import ColumnDistributionChart from '../components/ColumnDistributionChart';
import LoadingSpinner from '../components/LoadingSpinner';
import {
  ProfilingResult,
  executeProfileing,
  getLatestProfiling,
  getProfilingHistory,
  getTaskStatus,
  ProfilingExecutionRequest,
} from '../services/profilingService';

export default function ProfilingDashboard() {
  const [profiling, setProfiling] = useState<ProfilingResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string>('');
  const [history, setHistory] = useState<ProfilingResult[]>([]);
  
  // Form state
  const [datasetName, setDatasetName] = useState('sample_customers');
  const [bucketName, setBucketName] = useState('data-lake');
  const [objectName, setObjectName] = useState('sample_customers.csv');

  // Poll task status
  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTaskStatus(status.status);

        if (status.status === 'SUCCESS' && status.result) {
          // Task completed successfully
          clearInterval(interval);
          setTaskId(null);
          
          // Fetch the profiling result
          if (status.result.profiling_id) {
            await fetchLatestProfiling(datasetName);
          }
          
          setLoading(false);
        } else if (status.status === 'FAILURE') {
          // Task failed
          clearInterval(interval);
          setTaskId(null);
          setError(status.error || 'Profiling task failed');
          setLoading(false);
        }
      } catch (err) {
        console.error('Error polling task status:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [taskId, datasetName]);

  // Fetch latest profiling
  const fetchLatestProfiling = async (dataset: string) => {
    try {
      const result = await getLatestProfiling(dataset);
      setProfiling(result);
    } catch (err) {
      console.error('Error fetching profiling:', err);
      // Don't set error here, as it's okay if there's no profiling yet
    }
  };

  // Fetch profiling history
  const fetchHistory = async () => {
    try {
      const response = await getProfilingHistory(datasetName || undefined, 10);
      setHistory(response.results);
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  // Initial load
  useEffect(() => {
    if (datasetName) {
      fetchLatestProfiling(datasetName);
      fetchHistory();
    }
  }, []);

  // Handle profile execution
  const handleRunProfiling = async () => {
    setLoading(true);
    setError(null);
    setTaskStatus('');

    try {
      const request: ProfilingExecutionRequest = {
        dataset_name: datasetName,
        bucket_name: bucketName,
        object_name: objectName,
        profiled_by: 'user',
      };

      const response = await executeProfileing(request);
      setTaskId(response.task_id);
      setTaskStatus('PENDING');
    } catch (err: any) {
      console.error('Error starting profiling:', err);
      setError(err.response?.data?.detail || 'Failed to start profiling. Please try again.');
      setLoading(false);
    }
  };

  // Render loading state
  if (loading && !profiling) {
    return (
      <DashboardLayout
        title="Dataset Profiling"
        subtitle="Profile datasets and view statistics"
      >
        <div className="flex flex-col items-center justify-center h-64">
          <LoadingSpinner size="lg" />
          {taskStatus && (
            <p className="mt-4 text-gray-600">
              Status: <span className="font-medium">{taskStatus}</span>
            </p>
          )}
        </div>
      </DashboardLayout>
    );
  }

  // Render error state (only if no profiling data)
  if (error && !profiling) {
    return (
      <DashboardLayout
        title="Dataset Profiling"
        subtitle="Profile datasets and view statistics"
      >
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <p className="text-red-800 font-medium mb-2">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Dismiss
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout
      title="Dataset Profiling"
      subtitle="Profile datasets and view statistics"
    >
      {/* Profiling Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Run Dataset Profiling</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dataset Name
            </label>
            <input
              type="text"
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., sample_customers"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Bucket Name
            </label>
            <input
              type="text"
              value={bucketName}
              onChange={(e) => setBucketName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., data-lake"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Object Name
            </label>
            <input
              type="text"
              value={objectName}
              onChange={(e) => setObjectName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., data.csv"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={handleRunProfiling}
            disabled={loading || !datasetName || !bucketName || !objectName}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <LoadingSpinner size="sm" />
                <span>Profiling...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>Run Profiling</span>
              </>
            )}
          </button>

          {taskStatus && (
            <span className="text-sm text-gray-600">
              Status: <span className="font-medium">{taskStatus}</span>
            </span>
          )}
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md text-red-800 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Profiling Results */}
      {profiling ? (
        <>
          {/* Summary Cards */}
          <ProfilingSummaryCards profiling={profiling} />

          {/* Column Statistics */}
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Column Distributions</h2>
            
            {profiling.column_distributions && Object.keys(profiling.column_distributions).length > 0 ? (
              <div className="space-y-4">
                {Object.entries(profiling.column_distributions).map(([colName, distribution]) => (
                  <ColumnDistributionChart
                    key={colName}
                    columnName={colName}
                    distribution={distribution}
                    statistics={profiling.column_statistics?.[colName]}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Distribution Data</h3>
                <p className="text-gray-600">
                  Column distributions are not available for this profiling result.
                </p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Profiling Data</h3>
          <p className="text-gray-600 mb-6">
            Run a profiling task to see dataset statistics and distributions.
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
