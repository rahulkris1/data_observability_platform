import React from 'react';
import DashboardLayout from '../layouts/DashboardLayout';
import WorkerStatusCard from '../components/WorkerStatusCard';
import QueueMetricsSection from '../components/QueueMetricsSection';
import TaskStatusTable from '../components/TaskStatusTable';

export default function AsyncTaskMonitoring() {
  return (
    <DashboardLayout
      title="Async Task Monitoring"
      subtitle="Monitor Celery task workers, queues, and execution status"
    >
      {/* Main Content Grid */}
      <div className="space-y-6">
        {/* Worker Status and Queue Metrics Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Worker Status - Takes 1 column */}
          <div>
            <WorkerStatusCard refreshInterval={5000} />
          </div>

          {/* Queue Metrics - Takes 2 columns */}
          <div className="lg:col-span-2">
            <QueueMetricsSection refreshInterval={5000} />
          </div>
        </div>

        {/* Task Status Table - Full Width */}
        <div>
          <TaskStatusTable refreshInterval={5000} />
        </div>

        {/* Information Panel */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">About Async Task Processing</h2>
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">What are Async Tasks?</h3>
              <p>
                Async tasks run in the background using Celery workers, allowing long-running operations 
                like data validation and profiling to execute without blocking API requests.
              </p>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Available Task Types</h3>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>validate_dataset_async:</strong> Validate datasets against schema contracts</li>
                <li><strong>run_validation_rules_async:</strong> Execute validation rules from JSON configuration</li>
                <li><strong>batch_validate_datasets:</strong> Validate multiple datasets in a single batch</li>
                <li><strong>profile_dataset_async:</strong> Generate data quality and profiling metrics</li>
                <li><strong>calculate_data_quality_score:</strong> Compute comprehensive quality scores</li>
                <li><strong>generate_data_lineage:</strong> Track data lineage and dependencies</li>
              </ul>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Task Status Indicators</h3>
              <ul className="list-disc list-inside space-y-1">
                <li><strong>PENDING:</strong> Task is queued and waiting to start</li>
                <li><strong>RUNNING:</strong> Task is currently being executed by a worker</li>
                <li><strong>SUCCESS:</strong> Task completed successfully</li>
                <li><strong>FAILURE:</strong> Task failed with an error</li>
              </ul>
            </div>

            <div>
              <h3 className="font-medium text-gray-900 mb-2">Worker Configuration</h3>
              <p>
                Workers are configured to use Redis as the message broker and result backend. 
                Each worker can process one task at a time (concurrency=1) and will restart 
                after processing 50 tasks to prevent memory leaks.
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mt-4">
              <h3 className="font-medium text-blue-900 mb-2">💡 Pro Tip</h3>
              <p className="text-blue-800">
                Use the <strong>Refresh</strong> button to manually update task status, or let the 
                auto-refresh (every 5 seconds) keep you informed of progress. Monitor the queue 
                metrics to ensure workers are keeping up with task demand.
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
