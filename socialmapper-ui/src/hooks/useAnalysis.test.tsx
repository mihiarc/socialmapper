import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useAnalysis } from './useAnalysis';
import * as apiClient from '../services/apiClient';
import { JobStatusEnum } from '../types/api';

// Mock the API client
jest.mock('../services/apiClient');
const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('useAnalysis', () => {
  let queryClient: QueryClient;

  // Create wrapper with QueryClient
  const createWrapper = () => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    return ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    it('should start in idle state', () => {
      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      expect(result.current.state).toEqual({
        status: 'idle',
        jobId: null,
        result: null,
        error: null,
        progress: 0,
        message: null,
      });

      expect(result.current.isIdle).toBe(true);
      expect(result.current.isRunning).toBe(false);
      expect(result.current.isCompleted).toBe(false);
    });
  });

  describe('analyzeLocation', () => {
    it('should submit location analysis successfully', async () => {
      const mockResponse = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Pending,
        message: 'Analysis started',
        created_at: new Date().toISOString(),
        status_url: '/api/v1/analysis/test-job-123/status',
        results_url: '/api/v1/results/test-job-123',
      };

      mockApiClient.apiClient.analyzeLocation.mockResolvedValueOnce(mockResponse);

      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.analyzeLocation({
          location: 'Portland, OR',
          travel_mode: 'walk',
          travel_time_minutes: 15,
          census_variables: ['B01003_001E'],
        });
      });

      await waitFor(() => {
        expect(result.current.state.status).toBe('running');
        expect(result.current.state.jobId).toBe('test-job-123');
        expect(result.current.state.message).toBe('Analysis started');
      });
    });

    it('should handle submission errors', async () => {
      const mockError = new Error('Network error');
      mockApiClient.apiClient.analyzeLocation.mockRejectedValueOnce(mockError);

      const onError = jest.fn();
      const { result } = renderHook(() => useAnalysis({ onError }), {
        wrapper: createWrapper(),
      });

      act(() => {
        result.current.analyzeLocation({
          location: 'Portland, OR',
          travel_mode: 'walk',
          travel_time_minutes: 15,
        });
      });

      await waitFor(() => {
        expect(result.current.state.status).toBe('failed');
        expect(result.current.state.error).toBe(mockError);
        expect(onError).toHaveBeenCalledWith(mockError);
      });
    });
  });

  describe('job status polling', () => {
    it('should poll job status and complete successfully', async () => {
      const mockSubmitResponse = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Pending,
        message: 'Analysis started',
        created_at: new Date().toISOString(),
        status_url: '/api/v1/analysis/test-job-123/status',
        results_url: '/api/v1/results/test-job-123',
      };

      const mockStatusRunning = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Running,
        progress: 0.5,
        message: 'Processing...',
        created_at: new Date().toISOString(),
      };

      const mockStatusCompleted = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Completed,
        progress: 1,
        message: 'Completed',
        created_at: new Date().toISOString(),
      };

      const mockResult = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Completed,
        request: {
          location: 'Portland, OR',
          travel_mode: 'walk',
          travel_time_minutes: 15,
        },
        poi_count: 5,
        demographics: { B01003_001E: 100000 },
        processing_time_seconds: 10,
        created_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };

      mockApiClient.apiClient.analyzeLocation.mockResolvedValueOnce(mockSubmitResponse);
      mockApiClient.apiClient.getJobStatus
        .mockResolvedValueOnce(mockStatusRunning)
        .mockResolvedValueOnce(mockStatusCompleted);
      mockApiClient.apiClient.getAnalysisResult.mockResolvedValueOnce(mockResult);

      const onProgress = jest.fn();
      const onComplete = jest.fn();

      const { result } = renderHook(
        () => useAnalysis({ onProgress, onComplete, pollInterval: 10 }),
        { wrapper: createWrapper() }
      );

      // Submit analysis
      act(() => {
        result.current.analyzeLocation({
          location: 'Portland, OR',
          travel_mode: 'walk',
          travel_time_minutes: 15,
        });
      });

      // Wait for running status
      await waitFor(() => {
        expect(onProgress).toHaveBeenCalledWith(mockStatusRunning);
        expect(result.current.state.progress).toBe(0.5);
      });

      // Wait for completion
      await waitFor(() => {
        expect(result.current.state.status).toBe('completed');
        expect(result.current.state.result).toEqual(mockResult);
        expect(onComplete).toHaveBeenCalledWith(mockResult);
      });
    });

    it('should handle job failure', async () => {
      const mockSubmitResponse = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Pending,
        message: 'Analysis started',
        created_at: new Date().toISOString(),
        status_url: '/api/v1/analysis/test-job-123/status',
        results_url: '/api/v1/results/test-job-123',
      };

      const mockStatusFailed = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Failed,
        progress: 0,
        error: 'Processing failed',
        created_at: new Date().toISOString(),
      };

      mockApiClient.apiClient.analyzeLocation.mockResolvedValueOnce(mockSubmitResponse);
      mockApiClient.apiClient.getJobStatus.mockResolvedValueOnce(mockStatusFailed);

      const onError = jest.fn();

      const { result } = renderHook(
        () => useAnalysis({ onError, pollInterval: 10 }),
        { wrapper: createWrapper() }
      );

      // Submit analysis
      act(() => {
        result.current.analyzeLocation({
          location: 'Portland, OR',
          travel_mode: 'walk',
        });
      });

      // Wait for failure
      await waitFor(() => {
        expect(result.current.state.status).toBe('failed');
        expect(result.current.state.error?.message).toBe('Processing failed');
        expect(onError).toHaveBeenCalled();
      });
    });
  });

  describe('cancel', () => {
    it('should cancel running analysis', async () => {
      const mockSubmitResponse = {
        job_id: 'test-job-123',
        status: JobStatusEnum.Pending,
        message: 'Analysis started',
        created_at: new Date().toISOString(),
        status_url: '/api/v1/analysis/test-job-123/status',
        results_url: '/api/v1/results/test-job-123',
      };

      mockApiClient.apiClient.analyzeLocation.mockResolvedValueOnce(mockSubmitResponse);
      mockApiClient.apiClient.cancelRequest.mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      // Submit analysis
      act(() => {
        result.current.analyzeLocation({
          location: 'Portland, OR',
          travel_mode: 'walk',
        });
      });

      await waitFor(() => {
        expect(result.current.state.status).toBe('running');
      });

      // Cancel analysis
      act(() => {
        result.current.cancel();
      });

      expect(mockApiClient.apiClient.cancelRequest).toHaveBeenCalledWith('test-job-123');
      expect(result.current.state.status).toBe('cancelled');
      expect(result.current.state.message).toBe('Analysis cancelled');
    });
  });

  describe('reset', () => {
    it('should reset state to initial', async () => {
      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      // Modify state
      act(() => {
        result.current.state.status = 'completed';
        result.current.state.jobId = 'test-job';
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.state).toEqual({
        status: 'idle',
        jobId: null,
        result: null,
        error: null,
        progress: 0,
        message: null,
      });
    });
  });

  describe('exportResults', () => {
    it('should export results successfully', async () => {
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });
      mockApiClient.apiClient.exportResults.mockResolvedValueOnce(mockBlob);

      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      // Set a result
      act(() => {
        result.current.state.result = {
          job_id: 'test-job-123',
          status: JobStatusEnum.Completed,
          request: { location: 'Portland, OR', travel_mode: 'walk' },
          created_at: new Date().toISOString(),
        };
      });

      const blob = await result.current.exportResults('csv');

      expect(blob).toBe(mockBlob);
      expect(mockApiClient.apiClient.exportResults).toHaveBeenCalledWith(
        'test-job-123',
        'csv',
        true,
        true
      );
    });

    it('should return null if no result', async () => {
      const { result } = renderHook(() => useAnalysis(), {
        wrapper: createWrapper(),
      });

      const blob = await result.current.exportResults('csv');
      expect(blob).toBeNull();
    });
  });
});