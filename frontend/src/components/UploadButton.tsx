import React from 'react';

type UploadButtonProps = {
  selectedFile: File | null;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
  disabled?: boolean;
};

export default function UploadButton({
  selectedFile,
  onFileChange,
  onUpload,
  disabled = false,
}: UploadButtonProps) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-700">Upload dataset</label>
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <input
          type="file"
          accept=".csv,application/json,application/csv"
          onChange={(event) => {
            const file = event.target.files?.[0] ?? null;
            onFileChange(file);
          }}
          className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-white focus:outline-none"
        />
        <button
          type="button"
          onClick={onUpload}
          disabled={disabled}
          className="inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
        >
          {selectedFile ? 'Upload file' : 'Upload'}
        </button>
      </div>
      {selectedFile ? (
        <p className="text-sm text-gray-600">Selected file: {selectedFile.name}</p>
      ) : (
        <p className="text-sm text-gray-500">Choose a CSV or JSON dataset from your computer.</p>
      )}
    </div>
  );
}
