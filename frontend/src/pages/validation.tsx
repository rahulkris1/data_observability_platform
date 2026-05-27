import React, { useState } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import {
  ValidationSummaryCards,
  ValidationResultsTable,
  Alert,
  LoadingSpinner
} from '@/components';
import type { ValidationSummary, ValidationResult } from '@/components';

// Mock data for demonstration
const mockValidationSummaries: ValidationSummary[] = [
  {
    validatorName: 'SchemaValidator',
    status: 'passed',
    totalRecords: 10000,
    failedRecords: 0,
    passRate: 100,
    executionTimeMs: 245.67,
    message: 'All required columns present with correct data types'
  },
  {
    validatorName: 'NullValidator',
    status: 'warning',
    totalRecords: 10000,
    failedRecords: 150,
    passRate: 98.5,
    executionTimeMs: 189.23,
    message: 'Some null values detected in optional fields'
  },
  {
    validatorName: 'ChecksumValidator',
    status: 'passed',
    totalRecords: 10000,
    failedRecords: 0,
    passRate: 100,
    executionTimeMs: 312.45,
    message: 'Dataset checksum matches expected value, no duplicates found'
  }
];

const mockValidationResults: ValidationResult[] = [
  {
    validatorName: 'SchemaValidator',
    status: 'passed',
    passed: true,
    totalRecords: 10000,
    failedRecords: 0,
    passRate: 100,
    message: 'Schema validation passed',
    timestamp: new Date().toISOString(),
    executionTimeMs: 245.67,
    errors: []
  },
  {
    validatorName: 'NullValidator',
    status: 'warning',
    passed: true,
    totalRecords: 10000,
    failedRecords: 150,
    passRate: 98.5,
    message: 'Null validation completed with warnings',
    timestamp: new Date(Date.now() - 60000).toISOString(),
    executionTimeMs: 189.23,
    errors: []
  },
  {
    validatorName: 'ChecksumValidator',
    status: 'passed',
    passed: true,
    totalRecords: 10000,
    failedRecords: 0,
    passRate: 100,
    message: 'Checksum validation passed',
    timestamp: new Date(Date.now() - 120000).toISOString(),
    executionTimeMs: 312.45,
    errors: []
  }
];

export default function ValidationPage() {
  const [loading, setLoading] = useState(false);
  const [showAlert, setShowAlert] = useState(true);
  
  const handleCardClick = (summary: ValidationSummary) => {
    console.log('Card clicked:', summary);
    // Future: Navigate to detailed validation view
  };
  
  const handleRowClick = (result: ValidationResult) => {
    console.log('Row clicked:', result);
    // Future: Show detailed validation results modal
  };
  
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Data Validation</h1>
            <p className="mt-1 text-sm text-gray-500">
              Monitor and track data quality validations across datasets
            </p>
          </div>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center"
            onClick={() => {
              setLoading(true);
              setTimeout(() => setLoading(false), 1500);
            }}
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Run Validations
          </button>
        </div>
        
        {/* Info Alert */}
        {showAlert && (
          <Alert
            variant="info"
            title="Validation System Ready"
            message="PySpark-based validators are configured and ready to run. This is a placeholder interface for testing validation components."
            dismissible
            onClose={() => setShowAlert(false)}
          />
        )}
        
        {/* Validation Summary Cards */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Validation Summary</h2>
          <ValidationSummaryCards
            summaries={mockValidationSummaries}
            onCardClick={handleCardClick}
            loading={loading}
          />
        </section>
        
        {/* Dataset Selection Placeholder */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Dataset</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Dataset Selector */}
            <div>
              <label htmlFor="dataset" className="block text-sm font-medium text-gray-700 mb-2">
                Dataset
              </label>
              <select
                id="dataset"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled
              >
                <option>Select a dataset...</option>
                <option>user_activity.csv</option>
                <option>transactions.parquet</option>
                <option>customer_data.json</option>
              </select>
            </div>
            
            {/* Validator Selection */}
            <div>
              <label htmlFor="validator" className="block text-sm font-medium text-gray-700 mb-2">
                Validator
              </label>
              <select
                id="validator"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled
              >
                <option>All Validators</option>
                <option>Schema Validator</option>
                <option>Null Validator</option>
                <option>Checksum Validator</option>
              </select>
            </div>
            
            {/* Schedule */}
            <div>
              <label htmlFor="schedule" className="block text-sm font-medium text-gray-700 mb-2">
                Schedule
              </label>
              <select
                id="schedule"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled
              >
                <option>Manual</option>
                <option>Hourly</option>
                <option>Daily</option>
                <option>Weekly</option>
              </select>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Note:</span> Dataset selection and scheduling features are placeholders. 
              Validators are ready to use with PySpark DataFrames via the backend API.
            </p>
          </div>
        </section>
        
        {/* Validation Results Table */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Validation Results</h2>
          <ValidationResultsTable
            results={mockValidationResults}
            onRowClick={handleRowClick}
            loading={loading}
          />
        </section>
        
        {/* Getting Started */}
        <section className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">Getting Started</h2>
          <div className="space-y-3 text-sm text-gray-700">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span><strong>Backend:</strong> Install PySpark dependencies with <code className="px-1.5 py-0.5 bg-white rounded text-xs font-mono">pip install -r backend/requirements.txt</code></span>
            </div>
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span><strong>Verify Setup:</strong> Run <code className="px-1.5 py-0.5 bg-white rounded text-xs font-mono">python backend/verify_spark_session.py</code> to test SparkSession</span>
            </div>
            <div className="flex items-start">
              <svg className="w-5 h-5 text-blue-600 mr-2 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span><strong>Test Validators:</strong> Run <code className="px-1.5 py-0.5 bg-white rounded text-xs font-mono">python backend/verify_validators.py</code> to test all validators</span>
            </div>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
}
