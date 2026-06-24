/**
 * Schema Drift Page
 * 
 * Main page for schema drift monitoring and management
 */

import React from 'react';
import SchemaDriftDashboard from '@/components/SchemaDriftDashboard';

const SchemaDriftPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <SchemaDriftDashboard />
      </div>
    </div>
  );
};

export default SchemaDriftPage;
