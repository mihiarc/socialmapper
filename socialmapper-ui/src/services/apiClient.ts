/**
 * SocialMapper API Client for React Frontend
 * 
 * This client provides type-safe methods for communicating with the
 * SocialMapper REST API backend.
 */

import { config } from '../config/settings';

// Request and Response Types
export enum TravelMode {
  WALK = 'walk',
  BIKE = 'bike',
  DRIVE = 'drive',
}

export enum GeographicLevel {
  BLOCK_GROUP = 'block_group',
  ZCTA = 'zcta',
}

export enum ExportFormat {
  CSV = 'csv',
  GEOJSON = 'geojson',
  PARQUET = 'parquet',
  GEOPARQUET = 'geoparquet',
}

export enum JobStatusEnum {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface BaseAnalysisRequest {
  travel_time?: number;
  census_variables?: string[];
  geographic_level?: GeographicLevel;
  travel_mode?: TravelMode;
  include_isochrones?: boolean;
  include_demographics?: boolean;
}

export interface LocationAnalysisRequest extends BaseAnalysisRequest {
  location: string;
  poi_type: string;
  poi_name: string;
}

export interface CustomPOILocation {
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  category?: string;
}

export interface CustomPOIAnalysisRequest extends BaseAnalysisRequest {
  location: string;
  custom_pois: CustomPOILocation[];
}

export interface AnalysisResponse {
  job_id: string;
  status: JobStatusEnum;
  created_at: string;
  estimated_completion?: string;
  message?: string;
  timestamp: string;
  request_id?: string;
}

export interface JobStatus {
  job_id: string;
  status: JobStatusEnum;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  updated_at: string;
  estimated_completion?: string;
  error?: string;
  timestamp: string;
  request_id?: string;
}

export interface AnalysisResult {
  job_id: string;
  status: JobStatusEnum;
  request: LocationAnalysisRequest | CustomPOIAnalysisRequest;
  poi_count?: number;
  demographics?: Record<string, any>;
  isochrones?: Record<string, any>;
  analysis_area_km2?: number;
  population_covered?: number;
  processing_time_seconds?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  export_urls?: Record<ExportFormat, string>;
  error?: string;
  error_details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

export interface CensusVariable {
  code: string;
  name: string;
  concept: string;
  group?: string;
  universe?: string;
}

export interface CensusVariablesResponse {
  variables: CensusVariable[];
  total_count: number;
  categories: string[];
  timestamp: string;
  request_id?: string;
}

export interface POIType {
  type: string;
  name: string;
  description?: string;
  category?: string;
  common_names?: string[];
}

export interface POITypesResponse {
  poi_types: POIType[];
  total_count: number;
  categories: string[];
  timestamp: string;
  request_id?: string;
}

export interface LocationSearchResult {
  display_name: string;
  city?: string;
  state?: string;
  country: string;
  latitude: number;
  longitude: number;
  importance?: number;
  place_type?: string;
}

export interface LocationSearchResponse {
  query: string;
  results: LocationSearchResult[];
  total_count: number;
  timestamp: string;
  request_id?: string;
}

export interface ExportRequest {
  job_id: string;
  format: ExportFormat;
  include_isochrones?: boolean;
  include_demographics?: boolean;
}

export interface APIError {
  error_code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
  request_id?: string;
}

export class APIClientError extends Error {
  constructor(
    public statusCode: number,
    public apiError: APIError
  ) {
    super(`${statusCode}: ${apiError.message}`);
    this.name = 'APIClientError';
  }
}

/**
 * SocialMapper API Client
 */
export class SocialMapperAPIClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private abortControllers: Map<string, AbortController> = new Map();

  constructor(baseUrl?: string, apiKey?: string, timeout?: number) {
    this.baseUrl = baseUrl || config.apiBaseUrl;
    this.apiKey = apiKey;
    this.timeout = timeout || config.apiTimeout;
  }

  /**
   * Make an authenticated HTTP request
   */
  private async request<T>(
    path: string,
    options: RequestInit = {},
    jobId?: string
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    
    // Create abort controller for this request
    const abortController = new AbortController();
    if (jobId) {
      // Cancel any existing request for this job
      this.cancelRequest(jobId);
      this.abortControllers.set(jobId, abortController);
    }
    
    // Set up timeout
    const timeoutId = setTimeout(() => abortController.abort(), this.timeout);
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
    
    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: abortController.signal,
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIClientError(response.status, {
          error_code: errorData.error_code || 'UNKNOWN_ERROR',
          message: errorData.message || `HTTP ${response.status}`,
          details: errorData.details,
          timestamp: errorData.timestamp || new Date().toISOString(),
          request_id: errorData.request_id,
        });
      }
      
      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof APIClientError) {
        throw error;
      }
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new APIClientError(0, {
            error_code: 'REQUEST_CANCELLED',
            message: 'Request was cancelled',
            timestamp: new Date().toISOString(),
          });
        }
      }
      
      throw new APIClientError(0, {
        error_code: 'NETWORK_ERROR',
        message: error instanceof Error ? error.message : 'Network error',
        timestamp: new Date().toISOString(),
      });
    } finally {
      if (jobId) {
        this.abortControllers.delete(jobId);
      }
    }
  }

  /**
   * Cancel a request by job ID
   */
  public cancelRequest(jobId: string): void {
    const controller = this.abortControllers.get(jobId);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(jobId);
    }
  }

  /**
   * Cancel all ongoing requests
   */
  public cancelAllRequests(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }

  // Analysis endpoints

  /**
   * Submit a location-based analysis request
   */
  async analyzeLocation(request: LocationAnalysisRequest): Promise<AnalysisResponse> {
    return this.request<AnalysisResponse>('/api/v1/analysis/location', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Submit a custom POI analysis request
   */
  async analyzeCustomPOIs(request: CustomPOIAnalysisRequest): Promise<AnalysisResponse> {
    return this.request<AnalysisResponse>('/api/v1/analysis/custom-pois', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get the status of an analysis job
   */
  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/v1/analysis/${jobId}/status`, {}, jobId);
  }

  /**
   * Get the complete results of an analysis job
   */
  async getAnalysisResult(jobId: string): Promise<AnalysisResult> {
    return this.request<AnalysisResult>(`/api/v1/results/${jobId}`, {}, jobId);
  }

  /**
   * Poll for analysis completion with automatic retries
   */
  async pollAnalysis(
    jobId: string,
    onProgress?: (status: JobStatus) => void,
    pollInterval: number = config.pollInterval
  ): Promise<AnalysisResult> {
    while (true) {
      try {
        const status = await this.getJobStatus(jobId);
        
        if (onProgress) {
          onProgress(status);
        }
        
        switch (status.status) {
          case JobStatusEnum.COMPLETED:
            return await this.getAnalysisResult(jobId);
            
          case JobStatusEnum.FAILED:
            throw new APIClientError(422, {
              error_code: 'JOB_FAILED',
              message: status.error || 'Analysis job failed',
              timestamp: new Date().toISOString(),
            });
            
          case JobStatusEnum.CANCELLED:
            throw new APIClientError(422, {
              error_code: 'JOB_CANCELLED',
              message: 'Analysis job was cancelled',
              timestamp: new Date().toISOString(),
            });
            
          default:
            // Job is still pending or running
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
      } catch (error) {
        // Re-throw if it's a cancellation or job failure
        if (error instanceof APIClientError && 
            ['REQUEST_CANCELLED', 'JOB_FAILED', 'JOB_CANCELLED'].includes(error.apiError.error_code)) {
          throw error;
        }
        
        // For other errors, wait and retry
        await new Promise(resolve => setTimeout(resolve, pollInterval));
      }
    }
  }

  /**
   * Export analysis results in the specified format
   */
  async exportResults(
    jobId: string,
    format: ExportFormat,
    includeIsochrones: boolean = true,
    includeDemographics: boolean = true
  ): Promise<Blob> {
    const params = new URLSearchParams({
      format,
      include_isochrones: String(includeIsochrones),
      include_demographics: String(includeDemographics),
    });
    
    const url = `${this.baseUrl}/api/v1/results/${jobId}/export?${params}`;
    
    const response = await fetch(url, {
      headers: this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {},
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new APIClientError(response.status, {
        error_code: errorData.error_code || 'EXPORT_ERROR',
        message: errorData.message || 'Export failed',
        details: errorData.details,
        timestamp: errorData.timestamp || new Date().toISOString(),
      });
    }
    
    return await response.blob();
  }

  /**
   * Delete analysis results
   */
  async deleteResults(jobId: string): Promise<void> {
    await this.request<void>(`/api/v1/results/${jobId}`, {
      method: 'DELETE',
    });
  }

  // Metadata endpoints

  /**
   * Get available census variables
   */
  async getCensusVariables(
    group?: string,
    search?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<CensusVariablesResponse> {
    const params = new URLSearchParams();
    if (group) params.append('group', group);
    if (search) params.append('search', search);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    
    return this.request<CensusVariablesResponse>(
      `/api/v1/census/variables?${params}`
    );
  }

  /**
   * Get available POI types
   */
  async getPOITypes(
    category?: string,
    search?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<POITypesResponse> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    
    return this.request<POITypesResponse>(
      `/api/v1/poi/types?${params}`
    );
  }

  /**
   * Search for geographic locations
   */
  async searchLocations(
    query: string,
    limit: number = 10,
    country: string = 'US'
  ): Promise<LocationSearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: String(limit),
      country,
    });
    
    return this.request<LocationSearchResponse>(
      `/api/v1/geography/search?${params}`
    );
  }

  // Health check

  /**
   * Check API health status
   */
  async checkHealth(): Promise<{
    status: string;
    version: string;
    uptime_seconds: number;
    dependencies?: Record<string, string>;
  }> {
    return this.request('/api/v1/health');
  }
}

// Export a default instance
export const apiClient = new SocialMapperAPIClient();