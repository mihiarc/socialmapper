import {
  AnalysisRequest,
  AnalysisResponse,
  BatchAnalysisRequest,
  CustomPOIRequest,
  JobStatus,
  AnalysisResult,
  ExportRequest,
  ExportResponse,
  CensusVariablesResponse,
  POITypesResponse,
  LocationSearchResponse,
  APIError,
  ExportFormat
} from '../types/api';

export interface APIClientConfig {
  baseURL: string;
  apiKey?: string;
  timeout?: number;
  onError?: (error: APIError) => void;
}

export class SocialMapperAPIClient {
  private baseURL: string;
  private apiKey?: string;
  private timeout: number;
  private onError?: (error: APIError) => void;

  constructor(config: APIClientConfig) {
    this.baseURL = config.baseURL.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000; // Default 30 second timeout
    this.onError = config.onError;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${path}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json() as APIError;
        if (this.onError) {
          this.onError(errorData);
        }
        throw new Error(errorData.message || `HTTP ${response.status}`);
      }

      return await response.json() as T;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error('Request timeout');
        }
        throw error;
      }
      throw new Error('Network error');
    }
  }

  // Health check
  async checkHealth(): Promise<{ status: string; timestamp: string; version: string }> {
    return this.request('/api/v1/health');
  }

  // Analysis endpoints
  async createLocationAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
    return this.request('/api/v1/analysis/location', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async createBatchAnalysis(request: BatchAnalysisRequest): Promise<AnalysisResponse> {
    return this.request('/api/v1/analysis/batch', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async createCustomPOIAnalysis(request: CustomPOIRequest): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append('location', request.location);
    formData.append('poi_file', request.poi_file);
    formData.append('travel_mode', request.travel_mode);
    
    if (request.census_variables) {
      request.census_variables.forEach(v => formData.append('census_variables', v));
    }
    if (request.travel_time_minutes) {
      formData.append('travel_time_minutes', request.travel_time_minutes.toString());
    }
    if (request.poi_types) {
      request.poi_types.forEach(t => formData.append('poi_types', t));
    }
    if (request.name_column) {
      formData.append('name_column', request.name_column);
    }
    if (request.lat_column) {
      formData.append('lat_column', request.lat_column);
    }
    if (request.lon_column) {
      formData.append('lon_column', request.lon_column);
    }
    if (request.use_zcta !== undefined) {
      formData.append('use_zcta', request.use_zcta.toString());
    }

    return this.request('/api/v1/analysis/custom-pois', {
      method: 'POST',
      body: formData,
      headers: {} // Let browser set Content-Type for multipart/form-data
    });
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request(`/api/v1/analysis/${jobId}/status`);
  }

  async cancelJob(jobId: string): Promise<{ message: string }> {
    return this.request(`/api/v1/analysis/${jobId}/cancel`, {
      method: 'POST'
    });
  }

  // Results endpoints
  async getAnalysisResults(jobId: string): Promise<AnalysisResult> {
    return this.request(`/api/v1/results/${jobId}`);
  }

  async exportResults(
    jobId: string,
    format: ExportFormat,
    includeIsochrones: boolean = true,
    includeDemographics: boolean = true
  ): Promise<Blob> {
    const params = new URLSearchParams({
      format,
      include_isochrones: includeIsochrones.toString(),
      include_demographics: includeDemographics.toString()
    });

    const response = await fetch(
      `${this.baseURL}/api/v1/results/${jobId}/export?${params}`,
      {
        headers: this.apiKey ? { 'X-API-Key': this.apiKey } : {}
      }
    );

    if (!response.ok) {
      const errorData = await response.json() as APIError;
      if (this.onError) {
        this.onError(errorData);
      }
      throw new Error(errorData.message || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  async createExportJob(jobId: string, request: ExportRequest): Promise<ExportResponse> {
    return this.request(`/api/v1/results/${jobId}/export`, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async deleteResults(jobId: string): Promise<{ message: string }> {
    return this.request(`/api/v1/results/${jobId}`, {
      method: 'DELETE'
    });
  }

  // Metadata endpoints
  async getCensusVariables(params?: {
    group?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<CensusVariablesResponse> {
    const queryParams = new URLSearchParams();
    if (params?.group) queryParams.append('group', params.group);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const query = queryParams.toString();
    return this.request(`/api/v1/census/variables${query ? `?${query}` : ''}`);
  }

  async getPOITypes(params?: {
    category?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<POITypesResponse> {
    const queryParams = new URLSearchParams();
    if (params?.category) queryParams.append('category', params.category);
    if (params?.search) queryParams.append('search', params.search);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const query = queryParams.toString();
    return this.request(`/api/v1/poi/types${query ? `?${query}` : ''}`);
  }

  async searchLocations(params: {
    q: string;
    limit?: number;
    country?: string;
  }): Promise<LocationSearchResponse> {
    const queryParams = new URLSearchParams({ q: params.q });
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.country) queryParams.append('country', params.country);

    return this.request(`/api/v1/geography/search?${queryParams}`);
  }

  // Polling utilities
  async pollJobStatus(
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    pollInterval: number = 2000,
    abortSignal?: AbortSignal
  ): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      let timeoutId: NodeJS.Timeout | null = null;
      
      // Handle abort signal
      if (abortSignal) {
        abortSignal.addEventListener('abort', () => {
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          reject(new Error('Polling aborted'));
        });
      }

      const checkStatus = async () => {
        try {
          // Check if already aborted
          if (abortSignal?.aborted) {
            reject(new Error('Polling aborted'));
            return;
          }

          const status = await this.getJobStatus(jobId);
          
          if (onProgress) {
            onProgress(status);
          }

          switch (status.status) {
            case 'completed':
              const results = await this.getAnalysisResults(jobId);
              resolve(results);
              break;
            case 'failed':
            case 'cancelled':
              reject(new Error(status.error || `Job ${status.status}`));
              break;
            case 'pending':
            case 'running':
              if (!abortSignal?.aborted) {
                timeoutId = setTimeout(checkStatus, pollInterval);
              }
              break;
          }
        } catch (error) {
          reject(error);
        }
      };

      checkStatus();
    });
  }

  // Enhanced polling with built-in abort controller
  createPollingController(
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    pollInterval: number = 2000
  ): { promise: Promise<AnalysisResult>; abort: () => void } {
    const abortController = new AbortController();
    
    const promise = this.pollJobStatus(
      jobId,
      onProgress,
      pollInterval,
      abortController.signal
    );

    return {
      promise,
      abort: () => abortController.abort()
    };
  }

  // Utility method to download export
  async downloadExport(
    jobId: string,
    format: ExportFormat,
    filename?: string
  ): Promise<void> {
    const blob = await this.exportResults(jobId, format);
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || `socialmapper_${jobId}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}