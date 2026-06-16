/**
 * Validation Retry Management Page
 * Displays failed validations with retry functionality and insights
 */
import React, { useState } from 'react';
import MainLayout from '../layouts/MainLayout';
import {
  FailedPipelineSection,
  RetryHistoryTable,
  FailureInsightsPanel,
} from '../components';

const ValidationRetryPage: React.FC = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedDataset, setSelectedDataset] = useState<string | undefined>();
  const [selectedValidationType, setSelectedValidationType] = useState<string | undefined>();

  const handleRetryCreated = (validationId: number) => {
    // Trigger refresh of retry history
    setRefreshKey((prev) => prev + 1);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Validation Retry Management</h1>
              <p className="mt-2 text-sm text-gray-600">
                Monitor and manage failed validation retries across all datasets
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Filters */}
              <select
                value={selectedDataset || ''}
                onChange={(e) => setSelectedDataset(e.target.value || undefined)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Datasets</option>
                <option value="customers">Customers</option>
                <option value="orders">Orders</option>
                <option value="products">Products</option>
              </select>
              <select
                value={selectedValidationType || ''}
                onChange={(e) => setSelectedValidationType(e.target.value || undefined)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Validation Types</option>
                <option value="schema">Schema</option>
                <option value="null">Null Check</option>
                <option value="datatype">Data Type</option>
                <option value="checksum">Checksum</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quick Stats & Insights */}
        <FailureInsightsPanel
          datasetName={selectedDataset}
          daysBack={7}
          autoRefresh={true}
        />

        {/* Failed Validations Section */}
        <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Failed Validations</h2>
          <FailedPipelineSection
            datasetName={selectedDataset}
            validationType={selectedValidationType}
            onRetryCreated={handleRetryCreated}
          />
        </div>

        {/* Retry History */}
        <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Retry History</h2>
          <RetryHistoryTable
            key={refreshKey}
            datasetName={selectedDataset}
            daysBack={30}
            autoRefresh={true}
          />
        </div>

        {/* Info Box */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-blue-900 mb-1">
                Manual Retry System
              </h3>
              <div className="text-sm text-blue-800 space-y-1">
                <p>• All retries are <strong>manual</strong> - click the "Retry" button to re-run a failed validation</p>
                <p>• Maximum of 3 retry attempts per validation</p>
                <p>• Retry history is tracked in PostgreSQL for audit purposes</p>
                <p>• No automatic retries, Celery, or Airflow tasks are used</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default ValidationRetryPage;
