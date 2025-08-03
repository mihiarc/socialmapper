import { SocialMapperAPIClient } from './SocialMapperAPIClient';
import { TravelMode, JobStatusEnum, ExportFormat } from '../types/api';

// Mock fetch for testing
global.fetch = jest.fn();

describe('SocialMapperAPIClient', () => {
  let client: SocialMapperAPIClient;

  beforeEach(() => {
    client = new SocialMapperAPIClient({
      baseURL: 'http://localhost:8000',
      apiKey: 'test-key'
    });
    jest.clearAllMocks();
  });

  describe('constructor', () => {
    it('should remove trailing slash from baseURL', () => {
      const clientWithSlash = new SocialMapperAPIClient({
        baseURL: 'http://localhost:8000/'
      });
      expect(clientWithSlash['baseURL']).toBe('http://localhost:8000');
    });
  });

  describe('checkHealth', () => {
    it('should call health endpoint', async () => {
      const mockResponse = {
        status: 'healthy',
        timestamp: '2024-01-01T00:00:00Z',
        version: '0.1.0'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await client.checkHealth();

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/health',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-API-Key': 'test-key'
          })
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('createLocationAnalysis', () => {
    it('should create location analysis', async () => {
      const request = {
        location: 'Portland, OR',
        travel_mode: TravelMode.Walk,
        travel_time_minutes: 15
      };

      const mockResponse = {
        job_id: 'test-job-id',
        status: JobStatusEnum.Pending,
        message: 'Analysis job created',
        created_at: '2024-01-01T00:00:00Z',
        status_url: '/api/v1/analysis/test-job-id/status',
        results_url: '/api/v1/results/test-job-id'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await client.createLocationAnalysis(request);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/analysis/location',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(request),
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-API-Key': 'test-key'
          })
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('pollJobStatus', () => {
    it('should poll until job completes', async () => {
      const jobId = 'test-job-id';
      const progressCallback = jest.fn();

      // Mock status responses
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            job_id: jobId,
            status: JobStatusEnum.Running,
            progress: 0.5
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            job_id: jobId,
            status: JobStatusEnum.Completed,
            progress: 1.0
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            job_id: jobId,
            status: JobStatusEnum.Completed,
            poi_count: 10,
            demographics: { total_population: 5000 }
          })
        });

      const result = await client.pollJobStatus(jobId, progressCallback, 100);

      expect(progressCallback).toHaveBeenCalledTimes(2);
      expect(result.poi_count).toBe(10);
    });

    it('should reject on job failure', async () => {
      const jobId = 'test-job-id';

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          job_id: jobId,
          status: JobStatusEnum.Failed,
          error: 'Analysis failed'
        })
      });

      await expect(client.pollJobStatus(jobId)).rejects.toThrow('Analysis failed');
    });

    it('should handle abort signal', async () => {
      const jobId = 'test-job-id';
      const abortController = new AbortController();

      // Mock running status
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          job_id: jobId,
          status: JobStatusEnum.Running,
          progress: 0.5
        })
      });

      // Start polling
      const pollPromise = client.pollJobStatus(
        jobId,
        undefined,
        100,
        abortController.signal
      );

      // Abort after a short delay
      setTimeout(() => abortController.abort(), 50);

      await expect(pollPromise).rejects.toThrow('Polling aborted');
    });
  });

  describe('createPollingController', () => {
    it('should create polling controller with abort capability', async () => {
      const jobId = 'test-job-id';
      const progressCallback = jest.fn();

      // Mock running status that never completes
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          job_id: jobId,
          status: JobStatusEnum.Running,
          progress: 0.5
        })
      });

      const controller = client.createPollingController(jobId, progressCallback, 100);

      // Abort after a short delay
      setTimeout(() => controller.abort(), 150);

      await expect(controller.promise).rejects.toThrow('Polling aborted');
      expect(progressCallback).toHaveBeenCalled();
    });
  });

  describe('exportResults', () => {
    it('should export results as blob', async () => {
      const jobId = 'test-job-id';
      const mockBlob = new Blob(['test data'], { type: 'text/csv' });

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        blob: async () => mockBlob
      });

      const result = await client.exportResults(jobId, ExportFormat.CSV);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/results/test-job-id/export?format=csv&include_isochrones=true&include_demographics=true',
        expect.objectContaining({
          headers: { 'X-API-Key': 'test-key' }
        })
      );
      expect(result).toBe(mockBlob);
    });
  });

  describe('error handling', () => {
    it('should call onError callback on API error', async () => {
      const onError = jest.fn();
      const errorClient = new SocialMapperAPIClient({
        baseURL: 'http://localhost:8000',
        onError
      });

      const mockError = {
        error_code: 'NOT_FOUND',
        message: 'Job not found',
        timestamp: '2024-01-01T00:00:00Z'
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => mockError
      });

      await expect(errorClient.getJobStatus('invalid-id')).rejects.toThrow('Job not found');
      expect(onError).toHaveBeenCalledWith(mockError);
    });

    it('should handle timeout', async () => {
      const timeoutClient = new SocialMapperAPIClient({
        baseURL: 'http://localhost:8000',
        timeout: 100
      });

      // Mock fetch that rejects with AbortError
      const abortError = new Error('The operation was aborted');
      abortError.name = 'AbortError';
      (global.fetch as jest.Mock).mockRejectedValueOnce(abortError);

      await expect(timeoutClient.checkHealth()).rejects.toThrow('Request timeout');
    });
  });
});