/**
 * Type-safe API client for SocialMapper backend
 * Provides all API endpoint methods with proper typing
 */
import axios, { AxiosInstance, AxiosResponse } from 'axios';
import type {
  AnalysisResponse,
  AnalysisResult,
  CensusVariablesResponse,
  CustomPOIAnalysisRequest,
  ExportFormat,
  ExportResponse,
  HealthResponse,
  JobStatus,
  LocationAnalysisRequest,
  LocationSearchResponse,
  POITypesResponse,
} from "@/types/api";

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
const API_TIMEOUT = 30000; // 30 seconds

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health endpoints
  async checkHealth(): Promise<HealthResponse> {
    const response: AxiosResponse<HealthResponse> = await this.client.get('/health');
    return response.data;
  }

  // Analysis endpoints
  async submitLocationAnalysis(request: LocationAnalysisRequest): Promise<AnalysisResponse> {
    const response: AxiosResponse<AnalysisResponse> = await this.client.post('/analysis/location', request);
    return response.data;
  }

  async submitCustomPOIAnalysis(request: CustomPOIAnalysisRequest): Promise<AnalysisResponse> {
    const response: AxiosResponse<AnalysisResponse> = await this.client.post('/analysis/custom-poi', request);
    return response.data;
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response: AxiosResponse<JobStatus> = await this.client.get(`/analysis/${jobId}/status`);
    return response.data;
  }

  async getAnalysisResult(jobId: string): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await this.client.get(`/analysis/${jobId}/result`);
    return response.data;
  }

  async deleteAnalysisJob(jobId: string): Promise<{ message: string; job_id: string; timestamp: string }> {
    const response = await this.client.delete(`/analysis/${jobId}`);
    return response.data;
  }

  // Results endpoints
  async getAnalysisResults(jobId: string): Promise<AnalysisResult> {
    const response: AxiosResponse<AnalysisResult> = await this.client.get(`/results/${jobId}`);
    return response.data;
  }

  async exportResults(
    jobId: string,
    format: ExportFormat,
    includeIsochrones = true,
    includeDemographics = true
  ): Promise<Blob> {
    const response = await this.client.get(`/results/${jobId}/export`, {
      params: {
        format,
        include_isochrones: includeIsochrones,
        include_demographics: includeDemographics,
      },
      responseType: 'blob',
    });
    return response.data;
  }

  async createExportJob(
    jobId: string,
    format: ExportFormat,
    includeIsochrones = true,
    includeDemographics = true
  ): Promise<ExportResponse> {
    const response: AxiosResponse<ExportResponse> = await this.client.post(`/results/${jobId}/export`, {
      job_id: jobId,
      format,
      include_isochrones: includeIsochrones,
      include_demographics: includeDemographics,
    });
    return response.data;
  }

  // Metadata endpoints
  async getCensusVariables(): Promise<CensusVariablesResponse> {
    const response: AxiosResponse<CensusVariablesResponse> = await this.client.get('/metadata/census-variables');
    return response.data;
  }

  async getPOITypes(): Promise<POITypesResponse> {
    const response: AxiosResponse<POITypesResponse> = await this.client.get('/metadata/poi-types');
    return response.data;
  }

  async getTravelModes(): Promise<{ travel_modes: string[] }> {
    const response = await this.client.get('/metadata/travel-modes');
    return response.data;
  }

  async searchLocations(query: string): Promise<LocationSearchResponse> {
    const response: AxiosResponse<LocationSearchResponse> = await this.client.get('/metadata/locations/search', {
      params: { query },
    });
    return response.data;
  }

  // Real-time progress tracking with Server-Sent Events
  createProgressEventSource(jobId: string): EventSource {
    return new EventSource(`${API_BASE_URL}/analysis/${jobId}/progress`);
  }

  // File download helper
  async downloadFile(blob: Blob, filename: string): Promise<void> {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  // Batch operations (for future use)
  async getAllJobs(): Promise<any> {
    const response = await this.client.get('/analysis/jobs');
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
export default apiClient;