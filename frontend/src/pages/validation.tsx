import React, { useState } from 'react';
import DashboardLayout from '@/layouts/DashboardLayout';
import {
  ValidationSummaryCards,
  ValidationResultsTable,
  Alert,
  LoadingSpinner
} from '@/components';
import type { ValidationSummary, ValidationResult } from '@/components';
import { validationService, ValidationExecutionResponse } from '@/services/validationService';

export default function ValidationPage() {
  const [loading, setLoading] = useState(false);
  const [showAlert, setShowAlert] = useState(true);
  const [validationResults, setValidationResults] = useState<ValidationExecutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string>('');
  
  // Convert API response to component format
  const summaries: ValidationSummary[] = validationResults
    ? validationResults.validators.map((v) => ({
        validatorName: v.validator_name,
        status: v.status as any,
        totalRecords: v.total_records,
        failedRecords: v.failed_records,
        passRate: v.pass_rate,
        executionTimeMs: v.execution_time_ms || 0,
        message: v.message,
      }))
    : [];
  
  const results: ValidationResult[] = validationResults
    ? validationResults.validators.map((v) => ({
        validatorName: v.validator_name,
        status: v.status as any,
        passed: v.passed,
        totalRecords: v.total_records,
        failedRecords: v.failed_records,
        passRate: v.pass_rate,
        message: v.message,
        timestamp: validationResults.validation_timestamp,
        executionTimeMs: v.execution_time_ms || 0,
        errors: v.errors,
      }))
    : [];
  
  const handleRunValidation = async () => {
    if (!selectedDataset) {
      setError('Please select a dataset first');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await validationService.executeValidation({
        dataset_name: selectedDataset,
        null_threshold: 5.0,
      });
      
      setValidationResults(response);
      setShowAlert(false);
    } catch (err: any) {
      console.error('Validation error:', err);
      setError(err.message || 'Failed to execute validation');
    } finally {
      setLoading(false);
    }
  };
  
  const handleCardClick = (summary: ValidationSummary) => {
    console.log('Card clicked:', summary);
  };
  
  const handleRowClick = (result: ValidationResult) => {
    console.log('Row clicked:', result);
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
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 flex items-center"
            onClick={handleRunValidation}
            disabled={loading || !selectedDataset}
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
              </>
            ) : (
              'Run Validations'
            )}
          </button>
        </div>
        
        {/* Info Alert */}
        {showAlert && (
          <Alert
            variant="info"
            onDismiss={() => setShowAlert(false)}
          >
            <p className="text-sm text-gray-700">
              <span className="font-medium">Ready:</span> Select a dataset from MinIO and click "Run Validations" to execute PySpark validators.
              Results will be stored in PostgreSQL and displayed here.
            </p>
          </Alert>
        )}
        
        {/* Error Alert */}
        {error && (
          <Alert
            variant="error"
            onDismiss={() => setError(null)}
          >
            <p className="text-sm text-red-700">{error}</p>
          </Alert>
        )}
        
        {/* Success Alert */}
        {validationResults && (
          <Alert
            variant={validationResults.overall_passed ? 'success' : 'warning'}
            onDismiss={() => setValidationResults(null)}
          >
            <p className="text-sm">
              {validationResults.overall_passed 
                ? `All validations passed for ${validationResults.dataset_name}`
                : `Some validations failed for ${validationResults.dataset_name}`
              }
            </p>
          </Alert>
        )}
        
        {/* Dataset Selection */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Dataset</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="dataset" className="block text-sm font-medium text-gray-700 mb-2">
                Dataset
              </label>
              <select
                id="dataset"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
              >
                <option value="">Select a dataset...</option>
                <option value="customers.csv">customers.csv</option>
                <option value="orders.csv">orders.csv</option>
                <option value="products.json">products.json</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="validator" className="block text-sm font-medium text-gray-700 mb-2">
                Validator
              </label>
              <select
                id="validator"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option>All Validators</option>
                <option>Schema Validator</option>
                <option>Null Validator</option>
                <option>Checksum Validator</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="schedule" className="block text-sm font-medium text-gray-700 mb-2">
                Schedule
              </label>
              <select
                id="schedule"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option>Manual</option>
                <option>Hourly</option>
                <option>Daily</option>
                <option>Weekly</option>
              </select>
            </div>
          </div>
        </section>
        
        {/* Validation Summary Cards */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Validation Summary</h2>
          {results.length > 0 ? (
            <ValidationSummaryCards
              summaries={summaries}
              onCardClick={handleCardClick}
              loading={loading}
            />
          ) : (
            <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No validation results</h3>
              <p className="mt-1 text-sm text-gray-500">Select a dataset and run validations to see results</p>
            </div>
          )}
        </section>
        
        {/* Validation Results Table */}
        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Validation Results</h2>
          {results.length > 0 ? (
            <ValidationResultsTable
              results={results}
              onRowClick={handleRowClick}
              loading={loading}
            />
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No results yet</h3>
              <p className="mt-1 text-sm text-gray-500">Run validations to see detailed results</p>
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}
