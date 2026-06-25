/**
 * Pipeline Health Dashboard Page
 * 
 * Displays comprehensive health scores for data pipelines including:
 * - Overall health score widget
 * - Individual score cards for validation, freshness, and latency
 * - Historical health score trend chart
 */

import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import {
  getHealthScore,
  getHealthScoreHistory,
  calculateHealthScore,
  type HealthScore,
} from '@/services/healthScoreService';
import HealthScoreWidget from '@/components/HealthScoreWidget';
import PipelineScoreCard from '@/components/PipelineScoreCard';
import HealthTrendChart from '@/components/HealthTrendChart';
import LoadingSpinner from '@/components/LoadingSpinner';

export default function PipelineHealthPage() {
  const [pipelineName, setPipelineName] = useState<string>('customer_pipeline');
  const [healthScore, setHealthScore] = useState<HealthScore | null>(null);
  const [historyData, setHistoryData] = useState<HealthScore[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [calculating, setCalculating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lookbackHours, setLookbackHours] = useState<number>(168); // 7 days

  // Load health score data
  const loadHealthScore = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch latest health score
      const score = await getHealthScore(pipelineName);
      setHealthScore(score);

      // Fetch history
      const history = await getHealthScoreHistory(pipelineName, lookbackHours);
      setHistoryData(history);
    } catch (err: any) {
      console.error('Error loading health score:', err);
      setError(err.response?.data?.detail || 'Failed to load health score data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate new health score
  const handleCalculateScore = async () => {
    try {
      setCalculating(true);
      setError(null);

      await calculateHealthScore({
        pipeline_name: pipelineName,
        lookback_hours: 24,
        async_execution: false,
      });

      // Reload data after calculation
      await loadHealthScore();
    } catch (err: any) {
      console.error('Error calculating health score:', err);
      setError(err.response?.data?.detail || 'Failed to calculate health score');
    } finally {
      setCalculating(false);
    }
  };

  // Load data on mount and when pipeline changes
  useEffect(() => {
    loadHealthScore();
  }, [pipelineName]);

  return (
    <>
      <Head>
        <title>Pipeline Health Dashboard | Data Observability Platform</title>
        <meta name="description" content="Monitor pipeline health scores and trends" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Pipeline Health Dashboard</h1>
            <p className="mt-2 text-sm text-gray-600">
              Monitor overall pipeline health based on validation, freshness, and latency metrics
            </p>
          </div>

          {/* Controls */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div>
                <label htmlFor="pipeline" className="block text-sm font-medium text-gray-700 mb-2">
                  Pipeline Name
                </label>
                <input
                  type="text"
                  id="pipeline"
                  value={pipelineName}
                  onChange={(e) => setPipelineName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter pipeline name"
                />
              </div>

              <div>
                <label htmlFor="lookback" className="block text-sm font-medium text-gray-700 mb-2">
                  History (hours)
                </label>
                <select
                  id="lookback"
                  value={lookbackHours}
                  onChange={(e) => setLookbackHours(Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={24}>Last 24 hours</option>
                  <option value={72}>Last 3 days</option>
                  <option value={168}>Last 7 days</option>
                  <option value={336}>Last 14 days</option>
                  <option value={720}>Last 30 days</option>
                </select>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={loadHealthScore}
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Loading...' : 'Refresh'}
                </button>
                <button
                  onClick={handleCalculateScore}
                  disabled={calculating || loading}
                  className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:bg-gray-400 transition-colors"
                >
                  {calculating ? 'Calculating...' : 'Calculate'}
                </button>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && !healthScore && (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          )}

          {/* Health Score Dashboard */}
          {!loading && healthScore && (
            <>
              {/* Overall Health Widget */}
              <div className="mb-6">
                <HealthScoreWidget
                  pipelineName={healthScore.pipeline_name}
                  overallScore={healthScore.overall_score}
                  status={healthScore.status}
                  timestamp={healthScore.timestamp}
                  loading={loading}
                />
              </div>

              {/* Score Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                {/* Validation Score Card */}
                <PipelineScoreCard
                  title="Validation Quality"
                  score={healthScore.validation_score}
                  description="Data validation success rate"
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                  metrics={[
                    {
                      label: 'Pass Rate',
                      value: healthScore.validation_pass_rate
                        ? `${healthScore.validation_pass_rate.toFixed(1)}%`
                        : 'N/A',
                    },
                    {
                      label: 'Total Checks',
                      value: healthScore.total_validations || 0,
                    },
                  ]}
                  loading={loading}
                />

                {/* Freshness Score Card */}
                <PipelineScoreCard
                  title="Data Freshness"
                  score={healthScore.freshness_score}
                  description="Data timeliness and SLA compliance"
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                  metrics={[
                    {
                      label: 'SLA Violations',
                      value: healthScore.freshness_violations || 0,
                    },
                    {
                      label: 'Status',
                      value: healthScore.freshness_violations === 0 ? 'On Time' : 'Delayed',
                    },
                  ]}
                  loading={loading}
                />

                {/* Latency Score Card */}
                <PipelineScoreCard
                  title="Processing Speed"
                  score={healthScore.latency_score}
                  description="Pipeline processing performance"
                  icon={
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  }
                  metrics={[
                    {
                      label: 'Avg Latency',
                      value: healthScore.avg_latency_seconds
                        ? `${healthScore.avg_latency_seconds.toFixed(0)}s`
                        : 'N/A',
                    },
                    {
                      label: 'Performance',
                      value:
                        healthScore.avg_latency_seconds && healthScore.avg_latency_seconds < 60
                          ? 'Excellent'
                          : healthScore.avg_latency_seconds && healthScore.avg_latency_seconds < 300
                          ? 'Good'
                          : 'Slow',
                    },
                  ]}
                  loading={loading}
                />
              </div>

              {/* Health Trend Chart */}
              <HealthTrendChart
                data={historyData}
                loading={loading}
                height={350}
              />
            </>
          )}

          {/* Empty State */}
          {!loading && !healthScore && !error && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No health score data</h3>
              <p className="mt-1 text-sm text-gray-500">
                Calculate a health score to get started
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCalculateScore}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Calculate Health Score
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
