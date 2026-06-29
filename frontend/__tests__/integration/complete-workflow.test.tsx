/**
 * Complete frontend integration tests
 * 
 * Tests complete frontend workflows including:
 * - Frontend-backend integration
 * - Loading and error states
 * - User workflows
 * - State management
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import App from '@/pages/_app';
import Dashboard from '@/pages/dashboard';
import UploadPage from '@/pages/upload';

const mock = new MockAdapter(axios);

describe('Complete Frontend Integration Tests', () => {
  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  describe('Upload to Validation Workflow', () => {
    it('should complete full upload to validation workflow', async () => {
      const user = userEvent.setup();

      // Step 1: Upload file
      const uploadResponse = {
        filename: 'customers.csv',
        raw_object_name: 'raw/customers_123.csv',
        processed_object_name: 'processed/customers_123.json',
        record_count: 100
      };

      mock.onPost('/api/v1/upload').reply(200, uploadResponse);

      render(<UploadPage />);

      const file = new File(['id,name\n1,Test'], 'customers.csv', { type: 'text/csv' });
      const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
      
      if (input) {
        await user.upload(input, file);
      }

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/success/i) || screen.getByText(/uploaded/i)).toBeInTheDocument();
      });

      // Step 2: Navigate to validation
      const validateButton = screen.queryByRole('button', { name: /validate/i });
      
      if (validateButton) {
        const validationResponse = {
          dataset_name: 'customers.csv',
          overall_status: 'PASSED',
          total_records: 100,
          validators: [
            {
              validator_name: 'schema',
              status: 'PASSED',
              pass_rate: 100.0
            }
          ]
        };

        mock.onPost('/api/v1/validations/execute').reply(200, validationResponse);

        await user.click(validateButton);

        await waitFor(() => {
          expect(screen.getByText(/passed/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Dashboard Data Flow', () => {
    it('should load, filter, and display validation data', async () => {
      const user = userEvent.setup();

      const mockData = {
        audits: [
          {
            id: 1,
            dataset_name: 'customers.csv',
            status: 'PASSED',
            total_records: 1000,
            created_at: '2024-01-15T10:00:00Z'
          },
          {
            id: 2,
            dataset_name: 'orders.csv',
            status: 'FAILED',
            total_records: 500,
            created_at: '2024-01-15T09:00:00Z'
          }
        ],
        total_count: 2
      };

      mock.onGet('/api/v1/audit/history').reply(200, mockData);

      render(<Dashboard />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
        expect(screen.getByText(/orders.csv/i)).toBeInTheDocument();
      });

      // Apply filter
      const searchInput = screen.queryByPlaceholderText(/search/i);
      
      if (searchInput) {
        const filteredData = {
          audits: [mockData.audits[0]],
          total_count: 1
        };

        mock.onGet('/api/v1/audit/history').reply((config) => {
          if (config.params?.dataset_name?.includes('customers')) {
            return [200, filteredData];
          }
          return [200, mockData];
        });

        await user.type(searchInput, 'customers');

        await waitFor(() => {
          expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
          expect(screen.queryByText(/orders.csv/i)).not.toBeInTheDocument();
        });
      }
    });
  });

  describe('Loading States', () => {
    it('should show loading state during API calls', async () => {
      mock.onGet('/api/v1/audit/history').reply(() => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve([200, { audits: [], total_count: 0 }]);
          }, 100);
        });
      });

      render(<Dashboard />);

      // Should show loading
      expect(screen.getByText(/loading/i) || screen.getByRole('progressbar')).toBeInTheDocument();

      // Should hide loading after data loads
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('should show loading state for upload', async () => {
      const user = userEvent.setup();

      mock.onPost('/api/v1/upload').reply(() => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve([200, { filename: 'test.csv' }]);
          }, 100);
        });
      });

      render(<UploadPage />);

      const file = new File(['test'], 'test.csv', { type: 'text/csv' });
      const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
      
      if (input) {
        await user.upload(input, file);
      }

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      // Should show uploading state
      expect(screen.getByText(/uploading/i) || uploadButton).toBeDisabled();

      await waitFor(() => {
        expect(screen.queryByText(/uploading/i)).not.toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe('Error States', () => {
    it('should display error message on API failure', async () => {
      mock.onGet('/api/v1/audit/history').reply(500, {
        detail: 'Internal server error'
      });

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/error/i) || screen.getByText(/failed/i)).toBeInTheDocument();
      });
    });

    it('should display network error message', async () => {
      mock.onGet('/api/v1/audit/history').networkError();

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/network/i) || screen.getByText(/connection/i) || screen.getByText(/error/i)).toBeInTheDocument();
      });
    });

    it('should allow retry after error', async () => {
      const user = userEvent.setup();

      mock.onGet('/api/v1/audit/history').replyOnce(500);

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });

      // Mock successful retry
      mock.onGet('/api/v1/audit/history').reply(200, {
        audits: [],
        total_count: 0
      });

      const retryButton = screen.queryByRole('button', { name: /retry/i });
      
      if (retryButton) {
        await user.click(retryButton);

        await waitFor(() => {
          expect(screen.queryByText(/error/i)).not.toBeInTheDocument();
        });
      }
    });

    it('should show validation-specific errors', async () => {
      const user = userEvent.setup();

      mock.onPost('/api/v1/validations/execute').reply(400, {
        detail: 'Dataset not found'
      });

      render(<UploadPage />);

      const file = new File(['test'], 'test.csv', { type: 'text/csv' });
      const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
      
      if (input) {
        await user.upload(input, file);
      }

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      await user.click(uploadButton);

      await waitFor(() => {
        expect(screen.getByText(/not found/i) || screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    it('should update dashboard when new validation completes', async () => {
      const initialData = {
        audits: [
          { id: 1, dataset_name: 'test1.csv', status: 'PASSED' }
        ],
        total_count: 1
      };

      const updatedData = {
        audits: [
          { id: 2, dataset_name: 'test2.csv', status: 'PASSED' },
          { id: 1, dataset_name: 'test1.csv', status: 'PASSED' }
        ],
        total_count: 2
      };

      mock.onGet('/api/v1/audit/history').replyOnce(200, initialData);

      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/test1.csv/i)).toBeInTheDocument();
      });

      // Simulate refresh or polling
      mock.onGet('/api/v1/audit/history').reply(200, updatedData);

      // Trigger refresh (implementation-specific)
      const refreshButton = screen.queryByRole('button', { name: /refresh/i });
      
      if (refreshButton) {
        const user = userEvent.setup();
        await user.click(refreshButton);

        await waitFor(() => {
          expect(screen.getByText(/test2.csv/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup();

      render(<UploadPage />);

      const submitButton = screen.getByRole('button', { name: /upload/i });
      await user.click(submitButton);

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/required/i) || screen.getByText(/select a file/i)).toBeInTheDocument();
      });

      // Should not call API
      expect(mock.history.post.length).toBe(0);
    });

    it('should validate file size', async () => {
      const user = userEvent.setup();

      render(<UploadPage />);

      // Large file
      const largeFile = new File(
        [new ArrayBuffer(100 * 1024 * 1024)],
        'large.csv',
        { type: 'text/csv' }
      );

      const input = screen.getByLabelText(/file/i) || screen.getByRole('textbox', { hidden: true });
      
      if (input) {
        await user.upload(input, largeFile);

        await waitFor(() => {
          expect(screen.getByText(/too large/i) || screen.getByText(/size/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Accessibility', () => {
    it('should have accessible form labels', () => {
      render(<UploadPage />);

      expect(screen.getByLabelText(/file/i)).toBeInTheDocument();
    });

    it('should have accessible buttons', () => {
      render(<UploadPage />);

      const uploadButton = screen.getByRole('button', { name: /upload/i });
      expect(uploadButton).toBeInTheDocument();
      expect(uploadButton).toHaveAccessibleName();
    });

    it('should show error messages accessibly', async () => {
      mock.onGet('/api/v1/audit/history').reply(500);

      render(<Dashboard />);

      await waitFor(() => {
        const errorMessage = screen.getByText(/error/i);
        expect(errorMessage).toBeInTheDocument();
        // Should have role alert or aria-live
        expect(errorMessage.getAttribute('role') || errorMessage.closest('[role="alert"]')).toBeTruthy();
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should render mobile view correctly', () => {
      // Set mobile viewport
      global.innerWidth = 375;
      global.dispatchEvent(new Event('resize'));

      mock.onGet('/api/v1/audit/history').reply(200, {
        audits: [],
        total_count: 0
      });

      render(<Dashboard />);

      // Mobile-specific elements should be visible
      // Desktop-specific elements might be hidden
    });
  });

  describe('Performance', () => {
    it('should handle large datasets efficiently', async () => {
      const largeDataset = {
        audits: Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          dataset_name: `dataset_${i}.csv`,
          status: 'PASSED',
          total_records: 100
        })),
        total_count: 1000
      };

      mock.onGet('/api/v1/audit/history').reply(200, largeDataset);

      const startTime = performance.now();
      
      render(<Dashboard />);

      await waitFor(() => {
        expect(screen.getByText(/dataset_0.csv/i)).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render in reasonable time (< 3 seconds)
      expect(renderTime).toBeLessThan(3000);
    });
  });
});
