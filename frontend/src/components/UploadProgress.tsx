import React from 'react';

type UploadProgressProps = {
  progress: number;
  visible: boolean;
};

export default function UploadProgress({ progress, visible }: UploadProgressProps) {
  if (!visible) {
    return null;
  }

  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
      <div className="mb-3 flex items-center justify-between text-sm font-medium text-slate-700">
        <span>Upload progress</span>
        <span>{progress}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-blue-600 transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
