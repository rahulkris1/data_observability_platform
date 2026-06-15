import React, { useState, useEffect } from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import WarehouseStatusWidget from '../components/WarehouseStatusWidget';
import WarehouseLoadExecutionTable from '../components/WarehouseLoadExecutionTable';
import ConnectionStatusIndicator from '../components/ConnectionStatusIndicator';

export default function WarehouseStatus() {
  const [warehouseStats, setWarehouseStats] = useState<any>(null);
  const [loadHistory, setLoadHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [datasetFilter, setDatasetFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateFilter, setDateFilter] = useState<string>('');

  const fetchWarehouseData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch warehouse statistics
      const statsResponse = await fetch('/api/v1/warehouse/statistics');
      if (!statsResponse.ok) {
        throw new Error('Failed to fetch warehouse statistics');
      }
      const stats = await statsResponse.json();
      setWarehouseStats(stats);

      // Fetch load history with filters
      const params = new URLSearchParams();
      if (datasetFilter) params.append('dataset_name', datasetFilter);
      if (statusFilter) params.append('status', statusFilter);
      params.append('limit', '50');
      
      const historyResponse = await fetch(`/api/v1/warehouse/load-history?${params.toString()}`);
      if (!historyResponse.ok) {
        throw new Error('Failed to fetch load history');
      }
      const history = await historyResponse.json();
      setLoadHistory(history);
      
    } catch (err: any) {
      console.error('Error fetching warehouse data:', err);
      setError(err.message || 'Failed to fetch warehouse data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouseData();
  }, [datasetFilter, statusFilter, dateFilter]);

  const handleRefresh = () => {
    fetchWarehouseData();
  };

  const handleClearFilters = () => {
    setDatasetFilter('');
    setStatusFilter('');
    setDateFilter('');
  };

  return (
    <DashboardLayout 
      title="Warehouse Status"
      subtitle="Monitor warehouse loads, health, and data quality"
    >
      {/* Connection Status */}
      <div className="mb-6">
        <ConnectionStatusIndicator />
      </div>

      {/* Warehouse Status Widget */}
      <div className="mb-8">
        <WarehouseStatusWidget 
          stats={warehouseStats} 
          loading={loading}
          error={error}
        />
      </div>

      {/* Filters Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Load Execution History
          </h2>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleClearFilters}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear Filters
            </button>
            <button
              onClick={handleRefresh}
              disabled={loading}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
            >
              <svg 
                className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dataset
            </label>
            <select
              value={datasetFilter}
              onChange={(e) => setDatasetFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Datasets</option>
              {warehouseStats?.records_by_dataset && 
                Object.keys(warehouseStats.records_by_dataset).map(dataset => (
                  <option key={dataset} value={dataset}>{dataset}</option>
                ))
              }
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
              <option value="running">Running</option>
              <option value="rolled_back">Rolled Back</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Time</option>
              <option value="today">Today</option>
              <option value="week">Last 7 Days</option>
              <option value="month">Last 30 Days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Load Execution Table */}
      <WarehouseLoadExecutionTable 
        loadHistory={loadHistory} 
        loading={loading}
        error={error}
      />

      {/* Empty State */}
      {!loading && !error && loadHistory.length === 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <svg 
            className="mx-auto h-12 w-12 text-gray-400 mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Load History
          </h3>
          <p className="text-gray-500">
            No warehouse loads found matching your filters.
          </p>
        </div>
      )}
    </DashboardLayout>
  );
}
