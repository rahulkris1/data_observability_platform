/**
 * Schema Drift Dashboard Component
 * 
 * Main dashboard for schema drift detection and monitoring
 */

import React, { useState, useEffect } from 'react';
import schemaDriftService, {
  SchemaDrift,
  DriftAlert,
  SchemaTimelineItem,
  SchemaComparisonResponse
} from '@/services/schemaDriftService';
import DriftAlertIndicator from './DriftAlertIndicator';
import SchemaComparisonTable from './SchemaComparisonTable';
import SchemaTimelineView from './SchemaTimelineView';
import LoadingSpinner from './LoadingSpinner';

interface SchemaDriftDashboardProps {
  datasetName?: string;
}

const SchemaDriftDashboard: React.FC<SchemaDriftDashboardProps> = ({ datasetName }) => {
  const [selectedDataset, setSelectedDataset] = useState<string>(datasetName || '');
  const [driftHistory, setDriftHistory] = useState<SchemaDrift[]>([]);
  const [driftAlerts, setDriftAlerts] = useState<DriftAlert | null>(null);
  const [timeline, setTimeline] = useState<SchemaTimelineItem[]>([]);
  const [comparison, setComparison] = useState<SchemaComparisonResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'alerts' | 'history' | 'timeline' | 'comparison'>('alerts');
  const [comparisonVersions, setComparisonVersions] = useState({ version1: 1, version2: 2 });
  const [acknowledgeModal, setAcknowledgeModal] = useState<{ open: boolean; driftId: number | null }>({
    open: false,
    driftId: null
  });
  const [acknowledgeData, setAcknowledgeData] = useState({ acknowledgedBy: '', notes: '' });

  useEffect(() => {
    if (selectedDataset) {
      loadDashboardData();
    }
  }, [selectedDataset]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load alerts, history, and timeline in parallel
      const [alertsData, historyData, timelineData] = await Promise.all([
        schemaDriftService.getDriftAlerts(selectedDataset),
        schemaDriftService.getDatasetDriftHistory(selectedDataset, 50),
        schemaDriftService.getSchemaTimeline(selectedDataset, 50)
      ]);

      setDriftAlerts(alertsData);
      setDriftHistory(historyData);
      setTimeline(timelineData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedDataset) return;

    setLoading(true);
    setError(null);

    try {
      const result = await schemaDriftService.compareSchemas({
        dataset_name: selectedDataset,
        version1: comparisonVersions.version1,
        version2: comparisonVersions.version2
      });
      setComparison(result);
      setActiveTab('comparison');
    } catch (err: any) {
      setError(err.message || 'Failed to compare schemas');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!acknowledgeModal.driftId) return;

    try {
      await schemaDriftService.acknowledgeDrift(acknowledgeModal.driftId, acknowledgeData);
      setAcknowledgeModal({ open: false, driftId: null });
      setAcknowledgeData({ acknowledgedBy: '', notes: '' });
      // Reload data
      loadDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to acknowledge drift');
    }
  };

  const openAcknowledgeModal = (driftId: number) => {
    setAcknowledgeModal({ open: true, driftId });
  };

  if (!selectedDataset) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Schema Drift Dashboard</h2>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Dataset
          </label>
          <input
            type="text"
            placeholder="Enter dataset name..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                setSelectedDataset((e.target as HTMLInputElement).value);
              }
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Schema Drift Dashboard</h2>
            <p className="text-sm text-gray-600 mt-1">
              Dataset: <span className="font-medium">{selectedDataset}</span>
            </p>
          </div>
          <button
            onClick={() => setSelectedDataset('')}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Change Dataset
          </button>
        </div>

        {/* Alert Summary Cards */}
        {driftAlerts && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-6">
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <p className="text-sm text-gray-600">Total Drifts</p>
              <p className="text-2xl font-bold text-gray-900">{driftAlerts.total_drifts}</p>
            </div>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm text-blue-600">Unacknowledged</p>
              <p className="text-2xl font-bold text-blue-900">{driftAlerts.unacknowledged_count}</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg border border-red-200">
              <p className="text-sm text-red-600">Critical</p>
              <p className="text-2xl font-bold text-red-900">{driftAlerts.critical_count}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
              <p className="text-sm text-yellow-600">Warning</p>
              <p className="text-2xl font-bold text-yellow-900">{driftAlerts.warning_count}</p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <p className="text-sm text-green-600">Info</p>
              <p className="text-2xl font-bold text-green-900">{driftAlerts.info_count}</p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'alerts'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Active Alerts
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Drift History
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'timeline'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Timeline
            </button>
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-6 py-3 text-sm font-medium border-b-2 ${
                activeTab === 'comparison'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Compare Versions
            </button>
          </nav>
        </div>

        <div className="p-6">
          {loading && <LoadingSpinner />}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Active Alerts Tab */}
          {activeTab === 'alerts' && !loading && (
            <div className="space-y-4">
              {driftHistory.filter(d => !d.acknowledged).length === 0 ? (
                <p className="text-center text-gray-500 py-8">No active alerts</p>
              ) : (
                driftHistory
                  .filter(d => !d.acknowledged)
                  .map((drift) => (
                    <div key={drift.id} className="relative">
                      <DriftAlertIndicator drift={drift} />
                      <button
                        onClick={() => openAcknowledgeModal(drift.id)}
                        className="absolute top-3 right-3 px-3 py-1 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                      >
                        Acknowledge
                      </button>
                    </div>
                  ))
              )}
            </div>
          )}

          {/* Drift History Tab */}
          {activeTab === 'history' && !loading && (
            <div className="space-y-4">
              {driftHistory.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No drift history</p>
              ) : (
                driftHistory.map((drift) => (
                  <DriftAlertIndicator key={drift.id} drift={drift} />
                ))
              )}
            </div>
          )}

          {/* Timeline Tab */}
          {activeTab === 'timeline' && !loading && (
            <SchemaTimelineView timeline={timeline} datasetName={selectedDataset} />
          )}

          {/* Comparison Tab */}
          {activeTab === 'comparison' && !loading && (
            <div>
              <div className="mb-6 flex items-end gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Version 1
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={comparisonVersions.version1}
                    onChange={(e) =>
                      setComparisonVersions({ ...comparisonVersions, version1: parseInt(e.target.value) })
                    }
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Version 2
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={comparisonVersions.version2}
                    onChange={(e) =>
                      setComparisonVersions({ ...comparisonVersions, version2: parseInt(e.target.value) })
                    }
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <button
                  onClick={handleCompare}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Compare
                </button>
              </div>

              {comparison && <SchemaComparisonTable comparison={comparison} />}
            </div>
          )}
        </div>
      </div>

      {/* Acknowledge Modal */}
      {acknowledgeModal.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Acknowledge Drift</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Acknowledged By
                </label>
                <input
                  type="text"
                  value={acknowledgeData.acknowledgedBy}
                  onChange={(e) =>
                    setAcknowledgeData({ ...acknowledgeData, acknowledgedBy: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  placeholder="Your name or email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notes (optional)
                </label>
                <textarea
                  value={acknowledgeData.notes}
                  onChange={(e) =>
                    setAcknowledgeData({ ...acknowledgeData, notes: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  rows={3}
                  placeholder="Add any notes about this drift..."
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setAcknowledgeModal({ open: false, driftId: null })}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAcknowledge}
                disabled={!acknowledgeData.acknowledgedBy}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Acknowledge
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchemaDriftDashboard;
