/**
 * Pipeline Summary Cards
 * Displays summary statistics for pipelines
 */
import React, { useEffect, useState } from 'react';
import { airflowService, PipelineSummary, AirflowStatistics } from '@/services/airflowService';

interface PipelineSummaryCardsProps {
  refreshInterval?: number; // in milliseconds
}

export const PipelineSummaryCards: React.FC<PipelineSummaryCardsProps> = ({
  refreshInterval = 30000,
}) => {
  const [summary, setSummary] = useState<PipelineSummary | null>(null);
  const [stats, setStats] = useState<AirflowStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [summaryData, statsData] = await Promise.all([
        airflowService.getPipelineSummary(),
        airflowService.getStatistics(),
      ]);
      setSummary(summaryData);
      setStats(statsData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch pipeline data');
      console.error('Error fetching pipeline data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-600 text-sm">{error || 'Unable to load pipeline data'}</p>
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Pipelines',
      value: summary.total_pipelines,
      icon: '📊',
      color: 'blue',
      description: `${stats?.total_dags || 0} DAGs registered`,
    },
    {
      title: 'Active Pipelines',
      value: summary.active_pipelines,
      icon: '▶️',
      color: 'green',
      description: 'Currently running',
    },
    {
      title: 'Paused Pipelines',
      value: summary.paused_pipelines,
      icon: '⏸️',
      color: 'yellow',
      description: 'Temporarily disabled',
    },
    {
      title: 'Recent Runs',
      value: summary.recent_runs.total,
      icon: '🔄',
      color: 'purple',
      description: `${summary.recent_runs.success} success, ${summary.recent_runs.failed} failed`,
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600 border-blue-200',
      green: 'bg-green-50 text-green-600 border-green-200',
      yellow: 'bg-yellow-50 text-yellow-600 border-yellow-200',
      purple: 'bg-purple-50 text-purple-600 border-purple-200',
    };
    return colors[color as keyof typeof colors] || colors.blue;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 border-l-4"
          style={{
            borderLeftColor: {
              blue: '#3B82F6',
              green: '#10B981',
              yellow: '#F59E0B',
              purple: '#8B5CF6',
            }[card.color],
          }}
        >
          <div className="flex items-start justify-between mb-3">
            <div className="text-3xl">{card.icon}</div>
            <div className={`px-2 py-1 rounded text-xs font-semibold ${getColorClasses(card.color)}`}>
              {card.color}
            </div>
          </div>
          
          <div>
            <p className="text-sm font-medium text-gray-600 mb-1">{card.title}</p>
            <p className="text-3xl font-bold text-gray-900 mb-2">{card.value}</p>
            <p className="text-xs text-gray-500">{card.description}</p>
          </div>
        </div>
      ))}

      {/* Additional stats card */}
      <div className="md:col-span-2 lg:col-span-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg shadow p-6 border border-blue-100">
        <h4 className="text-lg font-semibold text-gray-900 mb-4">System Information</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-600 mb-1">Airflow Version</p>
            <p className="text-sm font-semibold text-gray-900">{stats?.version || 'Unknown'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Scheduler</p>
            <p className="text-sm font-semibold">
              <span className={stats?.scheduler_healthy ? 'text-green-600' : 'text-red-600'}>
                {stats?.scheduler_healthy ? '✓ Healthy' : '✗ Unhealthy'}
              </span>
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Database</p>
            <p className="text-sm font-semibold">
              <span className={stats?.database_healthy ? 'text-green-600' : 'text-red-600'}>
                {stats?.database_healthy ? '✓ Healthy' : '✗ Unhealthy'}
              </span>
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-600 mb-1">Success Rate</p>
            <p className="text-sm font-semibold text-gray-900">
              {summary.recent_runs.total > 0
                ? `${Math.round((summary.recent_runs.success / summary.recent_runs.total) * 100)}%`
                : 'N/A'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PipelineSummaryCards;
