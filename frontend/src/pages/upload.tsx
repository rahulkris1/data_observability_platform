import React, { useState } from 'react';
import UploadButton from '../components/UploadButton';
import UploadProgress from '../components/UploadProgress';
import { apiRequest, handleApiError } from '../services/apiClient';

export default function UploadPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);

  const handleFileChange = (file: File | null) => {
    setSelectedFile(file);
    setSuccessMessage('');
    setErrorMessage('');
    setProgress(0);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage('Please choose a CSV or JSON file before uploading.');
      return;
    }

    setUploading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      await apiRequest.post('/ingest', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            setProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
          }
        },
      });

      setSuccessMessage(`Upload complete: ${selectedFile.name}`);
      setUploadedFiles((prev) => [selectedFile.name, ...prev]);
      setSelectedFile(null);
    } catch (error) {
      const apiError = handleApiError(error);
      setErrorMessage(apiError.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-4xl rounded-3xl bg-white p-8 shadow-lg">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Dataset Upload</h1>
          <p className="mt-2 text-slate-600">
            Upload a CSV or JSON dataset file to the local ingestion workflow and store it in MinIO.
          </p>
        </div>

        <div className="space-y-6">
          <UploadButton
            selectedFile={selectedFile}
            onFileChange={handleFileChange}
            onUpload={handleUpload}
            disabled={uploading}
          />

          <UploadProgress progress={progress} visible={uploading} />

          {successMessage ? (
            <div className="rounded-xl border border-green-200 bg-green-50 p-4 text-green-900">
              {successMessage}
            </div>
          ) : null}

          {errorMessage ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-900">
              {errorMessage}
            </div>
          ) : null}

          <section className="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-900">Uploaded files</h2>
              <span className="text-sm text-slate-500">Local-first ingestion only</span>
            </div>
            {uploadedFiles.length === 0 ? (
              <p className="text-slate-600">No files uploaded yet. Your uploaded datasets will appear here.</p>
            ) : (
              <ul className="space-y-2">
                {uploadedFiles.map((name) => (
                  <li key={name} className="rounded-2xl bg-white px-4 py-3 shadow-sm">
                    {name}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
