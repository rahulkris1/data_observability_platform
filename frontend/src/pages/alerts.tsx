import { useState } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/layouts/DashboardLayout';

interface Alert {
  id: string;
  title: string;
  severity: 'critical' | 'warning' | 'info';
  status: 'active' | 'resolved' | 'acknowledged';
  description: string;
  timestamp: string;
  source: string;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([
    {
      id: '1',
      title: 'Cache status unavailable',
      severity: 'warning',
      status: 'active',
      description: 'Redis connection failed - caching operating in degraded mode',
      timestamp: '2 minutes ago',
      source: 'Cache Service',
    },
    {
      id: '2',
      title: 'Storage provider status check failed',
      severity: 'warning',
      status: 'active',
      description: 'Failed to connect to MinIO storage provider',
      timestamp: '5 minutes ago',
      source: 'Storage Service',
    },
    {
      id: '3',
      title: 'Data quality score below threshold',
      severity: 'critical',
      status: 'active',
      description: 'Validation success rate dropped to 89% (threshold: 95%)',
      timestamp: '15 minutes ago',
      source: 'Validation Pipeline',
    },
  ]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-red-600 bg-red-100';
      case 'acknowledged':
        return 'text-yellow-600 bg-yellow-100';
      case 'resolved':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const handleAcknowledge = (alertId: string) => {
    setAlerts(
      alerts.map((alert) =>
        alert.id === alertId ? { ...alert, status: 'acknowledged' as const } : alert
      )
    );
  };

  const handleResolve = (alertId: string) => {
    setAlerts(
      alerts.map((alert) =>
        alert.id === alertId ? { ...alert, status: 'resolved' as const } : alert
      )
    );
  };

  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const criticalAlerts = activeAlerts.filter((a) => a.severity === 'critical');

  return (
    <DashboardLayout
      title="Alerts"
      subtitle="Monitor and manage system alerts and notifications"
    >
      <div className="max-w-7xl mx-auto">

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Active Alerts</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  {activeAlerts.length}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">🚨</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Critical</p>
                <p className="text-3xl font-bold text-red-600 mt-2">
                  {criticalAlerts.length}
                </p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">⚠️</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Resolved Today</p>
                <p className="text-3xl font-bold text-green-600 mt-2">12</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">✓</span>
              </div>
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
          </div>

          <div className="divide-y divide-gray-200">
            {alerts.map((alert) => (
              <div key={alert.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getSeverityColor(
                          alert.severity
                        )} border`}
                      >
                        {alert.severity.toUpperCase()}
                      </span>
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                          alert.status
                        )}`}
                      >
                        {alert.status}
                      </span>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {alert.title}
                    </h3>
                    <p className="text-gray-600 text-sm mb-2">{alert.description}</p>

                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>📍 {alert.source}</span>
                      <span>🕐 {alert.timestamp}</span>
                    </div>
                  </div>

                  {alert.status === 'active' && (
                    <div className="flex space-x-2 ml-4">
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors"
                      >
                        Acknowledge
                      </button>
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                      >
                        Resolve
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Alert Rules */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">
            Alert Configuration
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/rules-management"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Manage Rules</h3>
              <p className="text-sm text-gray-600 mt-1">
                Configure alert conditions
              </p>
            </Link>
            <Link
              href="/validation"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Validation Alerts</h3>
              <p className="text-sm text-gray-600 mt-1">Data quality alerts</p>
            </Link>
            <Link
              href="/logs"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">System Logs</h3>
              <p className="text-sm text-gray-600 mt-1">View detailed logs</p>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
