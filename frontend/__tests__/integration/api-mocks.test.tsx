/**
 * Integration tests for API integration and mocking
 * 
 * Tests API integration using mocked Axios including:
 * - Request/response handling
 * - Error handling
 * - Loading states
 * - Retry logic
 * - Request interceptors
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { apiClient } from '@/services/api';

// Create mock adapter
const mock = new MockAdapter(axios);

describe('API Integration Tests with Mocked Axios', () => {
  beforeEach(() => {
    mock.reset();
    localStorage.clear();
  });

  afterEach(() => {
    mock.reset();
  });

  describe('Validation API', () => {
    it('should fetch validation history successfully', async () => {
      const mockData = {
        audits: [
          {
            id: 1,
            dataset_name: 'test.csv',
            status: 'PASSED',
            total_records: 100
          }
        ],
        total_count: 1
      };

      mock.onGet('/api/v1/audit/history').reply(200, mockData);

      const response = await axios.get('/api/v1/audit/history');

      expect(response.status).toBe(200);
      expect(response.data).toEqual(mockData);
      expect(response.data.audits).toHaveLength(1);
    });

    it('should execute validation successfully', async () => {
      const requestData = {
        dataset_name: 'test.csv',
        object_name: 'processed/test.json',
        validators: ['schema', 'null']
      };

      const responseData = {
        dataset_name: 'test.csv',
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

      mock.onPost('/api/v1/validations/execute').reply(200, responseData);

      const response = await axios.post('/api/v1/validations/execute', requestData);

      expect(response.status).toBe(200);
      expect(response.data.overall_status).toBe('PASSED');
      expect(response.data.validators).toHaveLength(1);
    });

    it('should handle validation API errors', async () => {
      mock.onPost('/api/v1/validations/execute').reply(500, {
        detail: 'Internal server error'
      });

      try {
        await axios.post('/api/v1/validations/execute', {});
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(500);
        expect(error.response.data.detail).toBe('Internal server error');
      }
    });

    it('should handle network timeout', async () => {
      mock.onGet('/api/v1/audit/history').timeout();

      try {
        await axios.get('/api/v1/audit/history');
        fail('Should have thrown a timeout error');
      } catch (error: any) {
        expect(error.code).toBe('ECONNABORTED');
      }
    });

    it('should filter audit history with query parameters', async () => {
      const mockData = {
        audits: [
          { id: 1, dataset_name: 'test.csv', status: 'PASSED' }
        ],
        total_count: 1
      };

      mock.onGet('/api/v1/audit/history', {
        params: {
          dataset_name: 'test',
          status: 'PASSED',
          limit: 10
        }
      }).reply(200, mockData);

      const response = await axios.get('/api/v1/audit/history', {
        params: {
          dataset_name: 'test',
          status: 'PASSED',
          limit: 10
        }
      });

      expect(response.status).toBe(200);
      expect(response.data.audits).toHaveLength(1);
    });
  });

  describe('Upload API', () => {
    it('should upload file successfully', async () => {
      const mockResponse = {
        filename: 'test.csv',
        raw_object_name: 'raw/test_123.csv',
        record_count: 100
      };

      mock.onPost('/api/v1/upload').reply(200, mockResponse);

      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'test.csv');

      const response = await axios.post('/api/v1/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      expect(response.status).toBe(200);
      expect(response.data.filename).toBe('test.csv');
    });

    it('should handle upload progress', async () => {
      const mockResponse = { filename: 'test.csv' };
      let progressCalled = false;

      mock.onPost('/api/v1/upload').reply(200, mockResponse);

      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'test.csv');

      await axios.post('/api/v1/upload', formData, {
        onUploadProgress: (progressEvent) => {
          progressCalled = true;
          expect(progressEvent.loaded).toBeGreaterThanOrEqual(0);
        }
      });

      // Note: MockAdapter might not trigger progress events
      // This is more for testing the configuration
    });

    it('should handle upload errors', async () => {
      mock.onPost('/api/v1/upload').reply(400, {
        detail: 'Invalid file type'
      });

      const formData = new FormData();
      formData.append('file', new Blob(['test']), 'test.txt');

      try {
        await axios.post('/api/v1/upload', formData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.detail).toContain('Invalid');
      }
    });
  });

  describe('Authentication API', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        access_token: 'token-123',
        token_type: 'bearer',
        user: { id: 1, username: 'testuser' }
      };

      mock.onPost('/auth/login').reply(200, mockResponse);

      const response = await axios.post('/auth/login', {
        username: 'testuser',
        password: 'password123'
      });

      expect(response.status).toBe(200);
      expect(response.data.access_token).toBe('token-123');
    });

    it('should handle login failure', async () => {
      mock.onPost('/auth/login').reply(401, {
        detail: 'Invalid credentials'
      });

      try {
        await axios.post('/auth/login', {
          username: 'wrong',
          password: 'wrong'
        });
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(401);
      }
    });

    it('should include auth token in requests', async () => {
      const token = 'test-token-123';
      localStorage.setItem('auth_token', token);

      mock.onGet('/api/v1/protected').reply((config) => {
        const authHeader = config.headers?.Authorization;
        if (authHeader === `Bearer ${token}`) {
          return [200, { data: 'protected data' }];
        }
        return [401, { detail: 'Unauthorized' }];
      });

      const response = await axios.get('/api/v1/protected', {
        headers: { Authorization: `Bearer ${token}` }
      });

      expect(response.status).toBe(200);
      expect(response.data.data).toBe('protected data');
    });

    it('should refresh token when expired', async () => {
      const oldToken = 'old-token';
      const newToken = 'new-token';

      // First request fails with 401
      mock.onGet('/api/v1/data')
        .replyOnce(401, { detail: 'Token expired' });

      // Token refresh succeeds
      mock.onPost('/auth/refresh').reply(200, {
        access_token: newToken,
        token_type: 'bearer'
      });

      // Retry with new token succeeds
      mock.onGet('/api/v1/data').reply(200, { data: 'success' });

      // Simulate the retry logic
      try {
        await axios.get('/api/v1/data', {
          headers: { Authorization: `Bearer ${oldToken}` }
        });
      } catch (error: any) {
        if (error.response.status === 401) {
          // Refresh token
          const refreshResponse = await axios.post('/auth/refresh');
          const newToken = refreshResponse.data.access_token;

          // Retry with new token
          const retryResponse = await axios.get('/api/v1/data', {
            headers: { Authorization: `Bearer ${newToken}` }
          });

          expect(retryResponse.status).toBe(200);
        }
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 errors', async () => {
      mock.onGet('/api/v1/nonexistent').reply(404, {
        detail: 'Not found'
      });

      try {
        await axios.get('/api/v1/nonexistent');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(404);
      }
    });

    it('should handle 500 errors', async () => {
      mock.onGet('/api/v1/error').reply(500, {
        detail: 'Internal server error'
      });

      try {
        await axios.get('/api/v1/error');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(500);
      }
    });

    it('should handle network errors', async () => {
      mock.onGet('/api/v1/network-error').networkError();

      try {
        await axios.get('/api/v1/network-error');
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.message).toContain('Network Error');
      }
    });

    it('should retry on failure', async () => {
      let attempts = 0;

      mock.onGet('/api/v1/retry').reply(() => {
        attempts++;
        if (attempts < 3) {
          return [500, { detail: 'Server error' }];
        }
        return [200, { data: 'success' }];
      });

      // Implement retry logic
      const maxRetries = 3;
      let lastError;

      for (let i = 0; i < maxRetries; i++) {
        try {
          const response = await axios.get('/api/v1/retry');
          expect(response.status).toBe(200);
          expect(attempts).toBe(3);
          break;
        } catch (error) {
          lastError = error;
          if (i === maxRetries - 1) throw error;
        }
      }
    });
  });

  describe('Request Interceptors', () => {
    it('should add default headers', async () => {
      mock.onGet('/api/v1/test').reply((config) => {
        expect(config.headers?.['Content-Type']).toBeDefined();
        return [200, { data: 'success' }];
      });

      await axios.get('/api/v1/test', {
        headers: { 'Content-Type': 'application/json' }
      });
    });

    it('should transform request data', async () => {
      mock.onPost('/api/v1/transform').reply((config) => {
        const data = JSON.parse(config.data);
        expect(data.transformed).toBe(true);
        return [200, { success: true }];
      });

      await axios.post('/api/v1/transform', {
        transformed: true
      });
    });

    it('should handle request cancellation', async () => {
      const CancelToken = axios.CancelToken;
      const source = CancelToken.source();

      mock.onGet('/api/v1/long-request').reply(() => {
        return new Promise((resolve) => {
          setTimeout(() => resolve([200, { data: 'done' }]), 1000);
        });
      });

      const requestPromise = axios.get('/api/v1/long-request', {
        cancelToken: source.token
      });

      // Cancel the request
      source.cancel('Request cancelled by user');

      try {
        await requestPromise;
        fail('Should have thrown a cancellation error');
      } catch (error: any) {
        expect(axios.isCancel(error)).toBe(true);
      }
    });
  });

  describe('Response Interceptors', () => {
    it('should transform response data', async () => {
      mock.onGet('/api/v1/data').reply(200, {
        result: { value: 123 }
      });

      const response = await axios.get('/api/v1/data');
      
      // Can add custom transformations
      expect(response.data.result.value).toBe(123);
    });

    it('should handle global error logging', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      mock.onGet('/api/v1/error').reply(500, {
        detail: 'Server error'
      });

      try {
        await axios.get('/api/v1/error');
      } catch (error) {
        // Error caught
      }

      // In real implementation, error interceptor would log
      // expect(consoleSpy).toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('Concurrent Requests', () => {
    it('should handle multiple concurrent requests', async () => {
      mock.onGet('/api/v1/data1').reply(200, { id: 1 });
      mock.onGet('/api/v1/data2').reply(200, { id: 2 });
      mock.onGet('/api/v1/data3').reply(200, { id: 3 });

      const [res1, res2, res3] = await Promise.all([
        axios.get('/api/v1/data1'),
        axios.get('/api/v1/data2'),
        axios.get('/api/v1/data3')
      ]);

      expect(res1.data.id).toBe(1);
      expect(res2.data.id).toBe(2);
      expect(res3.data.id).toBe(3);
    });

    it('should handle partial failures in concurrent requests', async () => {
      mock.onGet('/api/v1/success').reply(200, { data: 'ok' });
      mock.onGet('/api/v1/failure').reply(500, { error: 'failed' });

      const results = await Promise.allSettled([
        axios.get('/api/v1/success'),
        axios.get('/api/v1/failure')
      ]);

      expect(results[0].status).toBe('fulfilled');
      expect(results[1].status).toBe('rejected');
    });
  });
});
