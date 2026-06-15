import React from 'react';

export type LoadStatus = 'started' | 'completed' | 'failed' | 'retrying';

export interface LoadStatusIndicatorProps {
  status: LoadStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export default function LoadStatusIndicator({
  status,
  size = 'md',
  showIcon = true
}: LoadStatusIndicatorProps) {
  const baseClasses = 'inline-flex items-center font-medium rounded-full';
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base'
  };
  
  const statusConfig = {
    started: {
      bgColor: 'bg-blue-100',
      textColor: 'text-blue-800',
      borderColor: 'border-blue-200',
      icon: '⏳',
      label: 'Started'
    },
    completed: {
      bgColor: 'bg-green-100',
      textColor: 'text-green-800',
      borderColor: 'border-green-200',
      icon: '✓',
      label: 'Completed'
    },
    failed: {
      bgColor: 'bg-red-100',
      textColor: 'text-red-800',
      borderColor: 'border-red-200',
      icon: '✗',
      label: 'Failed'
    },
    retrying: {
      bgColor: 'bg-yellow-100',
      textColor: 'text-yellow-800',
      borderColor: 'border-yellow-200',
      icon: '↻',
      label: 'Retrying'
    }
  };
  
  const config = statusConfig[status];
  
  return (
    <span
      className={`
        ${baseClasses}
        ${sizeClasses[size]}
        ${config.bgColor}
        ${config.textColor}
        border ${config.borderColor}
      `}
    >
      {showIcon && (
        <span className="mr-1" aria-hidden="true">
          {config.icon}
        </span>
      )}
      {config.label}
    </span>
  );
}
