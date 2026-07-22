import { useEffect, useState } from 'react';
import Link from 'next/link';
import DashboardLayout from '@/layouts/DashboardLayout';

interface DataSource {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error';
  lastSync?: string;
}

export default function DataSourcesPage() {
  const [dataSources, setDataSources] = useState<DataSource[]>([
    {
      id: '1',
      name: 'PostgreSQL - Main Database',
      type: 'PostgreSQL',
      status: 'active',
      lastSync: '2 minutes ago',
    },
    {
      id: '2',
      name: 'MinIO - Object Storage',
      type: 'MinIO',
      status: 'active',
      lastSync: '5 minutes ago',
    },
    {
      id: '3',
      name: 'Redis - Cache',
      type: 'Redis',
      status: 'inactive',
      lastSync: 'Never',
    },
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'inactive':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <DashboardLayout
      title="Data Sources"
      subtitle="Manage and monitor your connected data sources"
    >
      <div className="max-w-7xl mx-auto">

        {/* Data Sources Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dataSources.map((source) => (
            <div
              key={source.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {source.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">{source.type}</p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                    source.status
                  )}`}
                >
                  {source.status}
                </span>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Last Sync:</span>{' '}
                  {source.lastSync}
                </div>
              </div>

              <div className="mt-4 flex space-x-2">
                <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors">
                  Configure
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors">
                  Test
                </button>
              </div>
            </div>
          ))}

          {/* Add New Source Card */}
          <div className="bg-white rounded-lg shadow-sm border-2 border-dashed border-gray-300 p-6 flex flex-col items-center justify-center hover:border-blue-400 transition-colors cursor-pointer">
            <svg
              className="w-12 h-12 text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            <h3 className="text-lg font-semibold text-gray-900">
              Add Data Source
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Connect a new data source
            </p>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6 border border-blue-200">
          <h2 className="text-lg font-semibold text-blue-900 mb-4">
            Related Pages
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/warehouse-status"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Warehouse Status</h3>
              <p className="text-sm text-gray-600 mt-1">
                Monitor warehouse health
              </p>
            </Link>
            <Link
              href="/schema-drift"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Schema Drift</h3>
              <p className="text-sm text-gray-600 mt-1">
                Track schema changes
              </p>
            </Link>
            <Link
              href="/pipelines"
              className="p-4 bg-white rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-medium text-blue-900">Pipelines</h3>
              <p className="text-sm text-gray-600 mt-1">
                View active pipelines
              </p>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
