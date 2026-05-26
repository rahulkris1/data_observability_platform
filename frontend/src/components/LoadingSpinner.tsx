import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'blue' | 'gray' | 'white';
  fullScreen?: boolean;
  message?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
};

const colorClasses = {
  blue: 'border-blue-600',
  gray: 'border-gray-600',
  white: 'border-white',
};

export default function LoadingSpinner({
  size = 'md',
  color = 'blue',
  fullScreen = false,
  message,
}: LoadingSpinnerProps) {
  const spinner = (
    <div className="flex flex-col items-center justify-center">
      <div
        className={`
          animate-spin rounded-full border-b-2
          ${sizeClasses[size]}
          ${colorClasses[color]}
        `}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="mt-4 text-sm text-gray-600 font-medium">{message}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}

// Alternative inline spinner for buttons
export function InlineSpinner({
  size = 'sm',
  color = 'white',
}: Pick<LoadingSpinnerProps, 'size' | 'color'>) {
  return (
    <div
      className={`
        animate-spin rounded-full border-b-2
        ${sizeClasses[size]}
        ${colorClasses[color]}
      `}
      role="status"
      aria-label="Loading"
    />
  );
}
