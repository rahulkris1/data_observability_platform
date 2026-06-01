import React, { useState } from 'react';

export interface ExportCSVButtonProps<T = any> {
  data: T[];
  filename?: string;
  headers?: { key: string; label: string }[];
  disabled?: boolean;
  className?: string;
}

/**
 * Generic CSV export button component
 * Converts array of objects to CSV and triggers download
 */
export default function ExportCSVButton<T extends Record<string, any>>({
  data,
  filename = 'export.csv',
  headers,
  disabled = false,
  className = ''
}: ExportCSVButtonProps<T>) {
  const [isExporting, setIsExporting] = useState(false);

  const convertToCSV = (data: T[], headers?: { key: string; label: string }[]): string => {
    if (data.length === 0) return '';

    // Determine headers
    let csvHeaders: { key: string; label: string }[];
    if (headers) {
      csvHeaders = headers;
    } else {
      // Auto-detect from first row
      const firstRow = data[0];
      csvHeaders = Object.keys(firstRow).map((key) => ({
        key,
        label: key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')
      }));
    }

    // Create header row
    const headerRow = csvHeaders.map((h) => `"${h.label}"`).join(',');

    // Create data rows
    const dataRows = data.map((row) => {
      return csvHeaders
        .map((header) => {
          const value = row[header.key];
          // Handle different data types
          if (value === null || value === undefined) {
            return '""';
          }
          if (typeof value === 'object') {
            return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
          }
          // Escape quotes and wrap in quotes
          return `"${String(value).replace(/"/g, '""')}"`;
        })
        .join(',');
    });

    return [headerRow, ...dataRows].join('\n');
  };

  const handleExport = () => {
    if (data.length === 0) {
      alert('No data to export');
      return;
    }

    setIsExporting(true);

    try {
      // Convert to CSV
      const csv = convertToCSV(data, headers);

      // Create blob
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });

      // Create download link
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      // Clean up
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting CSV:', error);
      alert('Failed to export CSV. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const defaultClassName =
    'inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200';

  return (
    <button
      onClick={handleExport}
      disabled={disabled || isExporting || data.length === 0}
      className={className || defaultClassName}
      title={data.length === 0 ? 'No data to export' : 'Export to CSV'}
    >
      {isExporting ? (
        <>
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-700"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          Exporting...
        </>
      ) : (
        <>
          <svg
            className="-ml-1 mr-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export CSV
        </>
      )}
    </button>
  );
}
