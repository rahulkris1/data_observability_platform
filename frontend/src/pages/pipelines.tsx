/**
 * Pipelines Page
 * Displays Airflow pipeline status, health, and management
 */
import React, { useState, useEffect } from 'react';
import MainLayout from '@/layouts/MainLayout';
import AirflowHealthWidget from '@/components/AirflowHealthWidget';
import SchedulerStatusIndicator from '@/components/SchedulerStatusIndicator';
import PipelineSummaryCards from '@/components/PipelineSummaryCards';
import { airflowService, DAGInfo } from '@/services/airflowService';

export default function PipelinesPage() {
  const [dags, setDags] = useState<DAGInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  const fetchDAGs = async () => {
    try {
      const data = await airflowService.listDAGs({ limit: 100 });
      setDags(data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch DAGs');
      console.error('Error fetching DAGs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDAGs();
    const interval = setInterval(fetchDAGs, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTogglePause = async (dagId: string, isPaused: boolean) => {
    try {
      if (isPaused) {
        await airflowService.unpauseDAG(dagId);
      } else {
        await airflowService.pauseDAG(dagId);
      }
      await fetchDAGs();
    } catch (err) {
      console.error('Error toggling DAG pause:', err);
      alert('Failed to update DAG status');
    }
  };

  const handleTrigger = async (dagId: string) => {
    try {
      await airflowService.triggerDAG(dagId);
      alert(`DAG ${dagId} triggered successfully`);
      await fetchDAGs();
    } catch (err) {
      console.error('Error triggering DAG:', err);
      alert('Failed to trigger DAG');
    }
  };

  // Get unique tags
  const allTags = Array.from(new Set(dags.flatMap(dag => dag.tags)));

  // Filter DAGs by selected tag
  const filteredDAGs = selectedTag
    ? dags.filter(dag => dag.tags.includes(selectedTag))
    : dags;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pipeline Management</h1>
            <p className="text-gray-600 mt-2">Monitor and manage Airflow pipelines</p>
          </div>
          <a
            href="http://localhost:8080"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Open Airflow UI →
          </a>
        </div>

        {/* Summary Cards */}
        <PipelineSummaryCards refreshInterval={30000} />

        {/* Health and Scheduler Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AirflowHealthWidget refreshInterval={30000} />
          <SchedulerStatusIndicator refreshInterval={10000} />
        </div>

        {/* DAGs List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Pipelines (DAGs)</h2>
              <button
                onClick={fetchDAGs}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                🔄 Refresh
              </button>
            </div>

            {/* Tag Filter */}
            {allTags.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedTag(null)}
                  className={`px-3 py-1 rounded-full text-sm ${
                    selectedTag === null
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
                {allTags.map(tag => (
                  <button
                    key={tag}
                    onClick={() => setSelectedTag(tag)}
                    className={`px-3 py-1 rounded-full text-sm ${
                      selectedTag === tag
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : error ? (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            ) : filteredDAGs.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">
                  {selectedTag ? `No DAGs found with tag "${selectedTag}"` : 'No DAGs found'}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        DAG ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tags
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Last Parsed
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredDAGs.map(dag => (
                      <tr key={dag.dag_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className={`w-2 h-2 rounded-full mr-3 ${
                              dag.is_active ? 'bg-green-500' : 'bg-gray-300'
                            }`}></div>
                            <span className="text-sm font-medium text-gray-900">{dag.dag_id}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            dag.is_paused
                              ? 'bg-yellow-100 text-yellow-800'
                              : dag.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {dag.is_paused ? 'Paused' : dag.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex flex-wrap gap-1">
                            {dag.tags.map(tag => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {dag.last_parsed_time
                            ? new Date(dag.last_parsed_time).toLocaleString()
                            : 'Never'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleTogglePause(dag.dag_id, dag.is_paused)}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              {dag.is_paused ? 'Resume' : 'Pause'}
                            </button>
                            <button
                              onClick={() => handleTrigger(dag.dag_id)}
                              className="text-green-600 hover:text-green-900"
                              disabled={dag.is_paused}
                            >
                              Trigger
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
