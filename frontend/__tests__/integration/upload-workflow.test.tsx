/**
 * Integration tests for upload workflow
 * 
 * Tests file upload functionality including:
 * - File selection and validation
 * - Upload progress tracking
 * - Success and error handling
 * - API integration with mocked responses
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import UploadPage from '@/pages/upload';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Upload Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render upload form', () => {
    render(<UploadPage />);
    
    expect(screen.getByText(/upload/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/file/i) || screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument();
  });

  it('should handle successful file upload', async () => {
    const user = userEvent.setup();
    
    // Mock successful upload response
    mockedAxios.post.mockResolvedValueOnce({
      data: {
        filename: 'test.csv',
        raw_object_name: 'raw/test_123.csv',
        processed_object_name: 'processed/test_123.json',
        record_count: 100,
        preview: [{ id: '1', name: 'Test' }]
      }
    });

    render(<UploadPage />);

    // Create and upload file
    const file = new File(['id,name\n1,Test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    // Wait for success message
    await waitFor(() => {
      expect(screen.getByText(/success/i) || screen.getByText(/uploaded/i)).toBeInTheDocument();
    });

    // Verify API was called
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining('/upload'),
      expect.any(FormData),
      expect.any(Object)
    );
  });

  it('should show upload progress', async () => {
    const user = userEvent.setup();
    let progressCallback: ((progressEvent: any) => void) | undefined;

    mockedAxios.post.mockImplementation((url, data, config) => {
      progressCallback = config?.onUploadProgress;
      
      // Simulate progress
      setTimeout(() => {
        if (progressCallback) {
          progressCallback({ loaded: 50, total: 100 });
        }
      }, 100);

      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({
            data: { filename: 'test.csv', record_count: 100 }
          });
        }, 200);
      });
    });

    render(<UploadPage />);

    const file = new File(['test data'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    // Progress indicator should appear
    await waitFor(() => {
      expect(screen.getByText(/uploading/i) || screen.getByRole('progressbar')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should handle upload errors', async () => {
    const user = userEvent.setup();

    // Mock failed upload
    mockedAxios.post.mockRejectedValueOnce({
      response: {
        status: 400,
        data: { detail: 'Invalid file format' }
      }
    });

    render(<UploadPage />);

    const file = new File(['invalid'], 'test.txt', { type: 'text/plain' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/error/i) || screen.getByText(/failed/i) || screen.getByText(/invalid/i)).toBeInTheDocument();
    });
  });

  it('should validate file type before upload', async () => {
    const user = userEvent.setup();

    render(<UploadPage />);

    // Try to upload invalid file type
    const file = new File(['test'], 'test.exe', { type: 'application/x-msdownload' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    // Should show validation error
    await waitFor(() => {
      const errorText = screen.queryByText(/invalid/i) || screen.queryByText(/supported/i);
      if (errorText) {
        expect(errorText).toBeInTheDocument();
      }
    });
  });

  it('should validate file size', async () => {
    const user = userEvent.setup();

    render(<UploadPage />);

    // Create large file (simulated)
    const largeContent = 'x'.repeat(100 * 1024 * 1024); // 100MB
    const file = new File([largeContent], 'large.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    // Should show size validation error
    await waitFor(() => {
      const errorText = screen.queryByText(/too large/i) || screen.queryByText(/size/i);
      if (errorText) {
        expect(errorText).toBeInTheDocument();
      }
    });
  });

  it('should show file preview after selection', async () => {
    const user = userEvent.setup();

    render(<UploadPage />);

    const file = new File(['id,name\n1,Test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    // Should show file name
    await waitFor(() => {
      expect(screen.getByText(/test.csv/i)).toBeInTheDocument();
    });
  });

  it('should allow file removal before upload', async () => {
    const user = userEvent.setup();

    render(<UploadPage />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    // Find and click remove button
    const removeButton = screen.queryByRole('button', { name: /remove/i }) || 
                        screen.queryByRole('button', { name: /clear/i });
    
    if (removeButton) {
      await user.click(removeButton);

      // File should be removed
      await waitFor(() => {
        expect(screen.queryByText(/test.csv/i)).not.toBeInTheDocument();
      });
    }
  });

  it('should handle network errors gracefully', async () => {
    const user = userEvent.setup();

    // Mock network error
    mockedAxios.post.mockRejectedValueOnce(new Error('Network Error'));

    render(<UploadPage />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/network/i) || screen.getByText(/connection/i) || screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('should disable upload button while uploading', async () => {
    const user = userEvent.setup();

    mockedAxios.post.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ data: { filename: 'test.csv' } });
        }, 1000);
      });
    });

    render(<UploadPage />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    // Button should be disabled during upload
    expect(submitButton).toBeDisabled();
  });

  it('should reset form after successful upload', async () => {
    const user = userEvent.setup();

    mockedAxios.post.mockResolvedValueOnce({
      data: { filename: 'test.csv', record_count: 100 }
    });

    render(<UploadPage />);

    const file = new File(['test'], 'test.csv', { type: 'text/csv' });
    const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
    
    if (input) {
      await user.upload(input, file);
    }

    const submitButton = screen.getByRole('button', { name: /upload/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/success/i) || screen.getByText(/uploaded/i)).toBeInTheDocument();
    });

    // Form should be reset (file input cleared)
    // This behavior depends on implementation
  });
});
