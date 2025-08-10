/**
 * Type definitions for SocialMapper API
 * Generated from FastAPI backend models to ensure type safety
 */

// Enum types from backend
export enum JobStatusEnum {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum TravelMode {
  WALK = 'walk',
  BIKE = 'bike',
  DRIVE = 'drive',
  TRANSIT = 'transit',
}

export enum GeographicLevel {
  BLOCK_GROUP = 'block_group',
  TRACT = 'tract',
  COUNTY = 'county',
}

export enum ExportFormat {
  CSV = 'csv',
  GEOJSON = 'geojson',
  PARQUET = 'parquet',
  GEOPARQUET = 'geoparquet',
}

// Base models
export interface BaseResponse {
  success: boolean;
  timestamp?: string;
}

export interface CustomPOILocation {
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  category?: string;
}

// Analysis request types
export interface BaseAnalysisRequest {
  travel_time: number;
  census_variables: string[];
  geographic_level: GeographicLevel;
  travel_mode: TravelMode;
  include_isochrones: boolean;
  include_demographics: boolean;
}

export interface LocationAnalysisRequest extends BaseAnalysisRequest {
  location: string;
  poi_type: string;
  poi_name: string;
}

export interface CustomPOIAnalysisRequest extends BaseAnalysisRequest {
  location: string;
  custom_pois: CustomPOILocation[];
}

// Response types
export interface AnalysisResponse extends BaseResponse {
  job_id: string;
  status: JobStatusEnum;
  created_at: string;
  estimated_completion?: string;
  message?: string;
}

export interface JobStatus extends BaseResponse {
  job_id: string;
  status: JobStatusEnum;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  updated_at: string;
  estimated_completion?: string;
  error?: string;
}

export interface AnalysisResult extends BaseResponse {
  job_id: string;
  status: JobStatusEnum;
  request: LocationAnalysisRequest | CustomPOIAnalysisRequest;
  
  // Results data
  poi_count?: number;
  demographics?: Record<string, any>;
  isochrones?: GeoJSON.FeatureCollection;
  
  // Metadata
  analysis_area_km2?: number;
  population_covered?: number;
  processing_time_seconds?: number;
  
  // Timestamps
  created_at: string;
  started_at?: string;
  completed_at?: string;
  
  // Export URLs
  export_urls?: Record<ExportFormat, string>;
  
  // Error information
  error?: string;
  error_details?: Record<string, any>;
}

// Metadata types
export interface CensusVariable {
  code: string;
  name: string;
  concept: string;
  group?: string;
  universe?: string;
}

export interface CensusVariablesResponse extends BaseResponse {
  variables: CensusVariable[];
  total_count: number;
  categories: string[];
}

export interface POIType {
  type: string;
  name: string;
  description?: string;
  category?: string;
  common_names?: string[];
}

export interface POITypesResponse extends BaseResponse {
  poi_types: POIType[];
  total_count: number;
  categories: string[];
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

export interface LocationSearchResponse extends BaseResponse {
  query: string;
  results: LocationSearchResult[];
  total_count: number;
}

// Export types
export interface ExportRequest {
  job_id: string;
  format: ExportFormat;
  include_isochrones: boolean;
  include_demographics: boolean;
}

export interface ExportResponse extends BaseResponse {
  export_id: string;
  job_id: string;
  format: ExportFormat;
  status: JobStatusEnum;
  download_url?: string;
  expires_at?: string;
  file_size_bytes?: number;
}

// Health check
export interface HealthResponse {
  status: string;
  timestamp: string;
  version?: string;
}

// Error response
export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}