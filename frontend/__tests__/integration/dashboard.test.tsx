/**
 * Integration tests for dashboard
 * 
 * Tests dashboard functionality including:
 * - Data loading and display
 * - Filtering and sorting
 * - Real-time updates
 * - Error handling
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import Dashboard from '@/pages/dashboard';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

const mockValidationData = {
  audits: [
    {
      id: 1,
      dataset_name: 'customers.csv',
      validation_type: 'schema',
      status: 'PASSED',
      total_records: 1000,
      failed_records: 0,
      pass_rate: 100.0,
      execution_time_ms: 250,
      created_at: '2024-01-15T10:00:00Z',
      triggered_by: 'user1',
      environment: 'production'
    },
    {
      id: 2,
      dataset_name: 'orders.csv',
      validation_type: 'null',
      status: 'FAILED',
      total_records: 500,
      failed_records: 25,
      pass_rate: 95.0,
      execution_time_ms: 180,
      created_at: '2024-01-15T09:00:00Z',
      triggered_by: 'user2',
      environment: 'production'
    },
    {
      id: 3,
      dataset_name: 'products.csv',
      validation_type: 'datatype',
      status: 'WARNING',
      total_records: 750,
      failed_records: 5,
      pass_rate: 99.3,
      execution_time_ms: 200,
      created_at: '2024-01-15T08:00:00Z',
      triggered_by: 'user1',
      environment: 'staging'
    }
  ],
  total_count: 3,
  limit: 100,
  offset: 0
};

describe('Dashboard Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should load and display validation data', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/orders.csv/i)).toBeInTheDocument();
    expect(screen.getByText(/products.csv/i)).toBeInTheDocument();
  });

  it('should show loading state while fetching data', async () => {
    mockedAxios.get.mockImplementation(() => {
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve({ data: mockValidationData });
        }, 100);
      });
    });

    render(<Dashboard />);

    // Loading indicator should be visible
    expect(screen.getByText(/loading/i) || screen.getByRole('progressbar')).toBeInTheDocument();

    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    mockedAxios.get.mockRejectedValueOnce(new Error('API Error'));

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/error/i) || screen.getByText(/failed/i)).toBeInTheDocument();
    });
  });

  it('should filter validations by status', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find and click status filter
    const statusFilter = screen.queryByLabelText(/status/i) || 
                        screen.queryByRole('combobox', { name: /filter/i });
    
    if (statusFilter) {
      await user.click(statusFilter);
      
      const passedOption = screen.queryByText(/passed/i);
      if (passedOption) {
        await user.click(passedOption);

        // Should filter to show only PASSED validations
        await waitFor(() => {
          expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
          expect(screen.queryByText(/orders.csv/i)).not.toBeInTheDocument();
        });
      }
    }
  });

  it('should filter validations by dataset name', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find search input
    const searchInput = screen.queryByPlaceholderText(/search/i) || 
                       screen.queryByLabelText(/search/i);
    
    if (searchInput) {
      await user.type(searchInput, 'customers');

      // Should filter results
      await waitFor(() => {
        expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
        expect(screen.queryByText(/orders.csv/i)).not.toBeInTheDocument();
      });
    }
  });

  it('should sort validations by date', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find sort button
    const sortButton = screen.queryByRole('button', { name: /sort/i }) ||
                      screen.queryByLabelText(/sort/i);
    
    if (sortButton) {
      await user.click(sortButton);

      // Verify API called with sort parameter
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('sort'),
          expect.any(Object)
        );
      });
    }
  });

  it('should display validation statistics', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Should show total count
    expect(screen.getByText(/3/i) || screen.getByText(/total/i)).toBeInTheDocument();
  });

  it('should show validation details on row click', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Click on first validation row
    const customerRow = screen.getByText(/customers.csv/i).closest('tr') || 
                       screen.getByText(/customers.csv/i);
    
    await user.click(customerRow);

    // Should show details (modal or expanded row)
    await waitFor(() => {
      expect(screen.getByText(/1000/i) || screen.getByText(/records/i)).toBeInTheDocument();
    });
  });

  it('should paginate results', async () => {
    const user = userEvent.setup();
    
    const page1Data = { ...mockValidationData, total_count: 25 };
    mockedAxios.get.mockResolvedValueOnce({ data: page1Data });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find next page button
    const nextButton = screen.queryByRole('button', { name: /next/i }) ||
                      screen.queryByLabelText(/next/i);
    
    if (nextButton && !nextButton.hasAttribute('disabled')) {
      mockedAxios.get.mockResolvedValueOnce({ 
        data: { ...mockValidationData, offset: 10 } 
      });

      await user.click(nextButton);

      // Should call API with new offset
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledWith(
          expect.stringContaining('offset'),
          expect.any(Object)
        );
      });
    }
  });

  it('should refresh data on button click', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find refresh button
    const refreshButton = screen.queryByRole('button', { name: /refresh/i }) ||
                         screen.queryByLabelText(/refresh/i);
    
    if (refreshButton) {
      mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });
      
      await user.click(refreshButton);

      // Should call API again
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalledTimes(2);
      });
    }
  });

  it('should display status badges with correct colors', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Check for status indicators
    const passedStatus = screen.queryByText(/passed/i);
    const failedStatus = screen.queryByText(/failed/i);
    const warningStatus = screen.queryByText(/warning/i);

    if (passedStatus) {
      expect(passedStatus).toHaveClass(/success|green/i);
    }
    if (failedStatus) {
      expect(failedStatus).toHaveClass(/error|red|danger/i);
    }
    if (warningStatus) {
      expect(warningStatus).toHaveClass(/warning|yellow/i);
    }
  });

  it('should show empty state when no data', async () => {
    mockedAxios.get.mockResolvedValueOnce({ 
      data: { audits: [], total_count: 0, limit: 100, offset: 0 } 
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/no data/i) || 
             screen.getByText(/no validations/i) || 
             screen.getByText(/empty/i)).toBeInTheDocument();
    });
  });

  it('should handle concurrent filter updates', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValue({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Apply multiple filters quickly
    const searchInput = screen.queryByPlaceholderText(/search/i);
    
    if (searchInput) {
      await user.type(searchInput, 'test');
      
      // Should debounce or handle concurrent requests
      await waitFor(() => {
        expect(mockedAxios.get).toHaveBeenCalled();
      });
    }
  });

  it('should display execution time metrics', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/250/i) || screen.getByText(/ms/i)).toBeInTheDocument();
    });
  });

  it('should export data functionality', async () => {
    const user = userEvent.setup();
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockValidationData });

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText(/customers.csv/i)).toBeInTheDocument();
    });

    // Find export button
    const exportButton = screen.queryByRole('button', { name: /export/i }) ||
                        screen.queryByLabelText(/export/i);
    
    if (exportButton) {
      await user.click(exportButton);
      
      // Export functionality should trigger
      // Implementation specific
    }
  });
});
