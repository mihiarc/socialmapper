// API Types matching the backend Pydantic models

// Enums
export enum TravelMode {
  Walk = "walk",
  Bike = "bike",
  Drive = "drive",
  Transit = "transit"
}

export enum JobStatusEnum {
  Pending = "pending",
  Running = "running",
  Completed = "completed",
  Failed = "failed",
  Cancelled = "cancelled"
}

export enum ExportFormat {
  CSV = "csv",
  GeoJSON = "geojson",
  Parquet = "parquet",
  GeoParquet = "geoparquet"
}

// Error codes enum
export enum ErrorCode {
  VALIDATION_ERROR = "VALIDATION_ERROR",
  RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND", 
  PROCESSING_ERROR = "PROCESSING_ERROR",
  RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED",
  AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR",
  AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR",
  INTERNAL_ERROR = "INTERNAL_ERROR",
  SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE",
  TIMEOUT_ERROR = "TIMEOUT_ERROR",
  INVALID_REQUEST = "INVALID_REQUEST",
  NETWORK_ERROR = "NETWORK_ERROR"
}

// Base types
export interface APIError {
  error_code: ErrorCode;
  message: string;
  details?: any;
  timestamp: string;
}

// Request types
export interface AnalysisRequest {
  location: string;
  census_variables?: string[];
  travel_mode: TravelMode;
  travel_time_minutes?: number;
  poi_types?: string[];
  use_zcta?: boolean;
}

export interface BatchAnalysisRequest {
  locations: string[];
  census_variables?: string[];
  travel_mode: TravelMode;
  travel_time_minutes?: number;
  poi_types?: string[];
  use_zcta?: boolean;
}

export interface CustomPOIRequest {
  location: string;
  poi_file: File;
  census_variables?: string[];
  travel_mode: TravelMode;
  travel_time_minutes?: number;
  name_column?: string;
  lat_column?: string;
  lon_column?: string;
  use_zcta?: boolean;
}

export interface ExportRequest {
  format: ExportFormat;
  include_isochrones?: boolean;
  include_demographics?: boolean;
  compression?: string;
}

// Response types
export interface AnalysisResponse {
  job_id: string;
  status: JobStatusEnum;
  message: string;
  created_at: string;
  status_url: string;
  results_url: string;
}

export interface JobStatus {
  job_id: string;
  status: JobStatusEnum;
  progress: number;
  message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  error_details?: any;
  results_url?: string;
}

export interface AnalysisResult {
  job_id: string;
  status: JobStatusEnum;
  request: AnalysisRequest;
  poi_count?: number;
  demographics?: Record<string, number>;
  isochrones?: any; // GeoJSON FeatureCollection
  analysis_area_km2?: number;
  population_covered?: number;
  processing_time_seconds?: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  export_urls?: Record<string, string>;
  error?: string;
  error_details?: any;
}

export interface ExportResponse {
  export_id: string;
  job_id: string;
  format: ExportFormat;
  status: JobStatusEnum;
  download_url?: string;
  expires_at: string;
  file_size_bytes?: number;
}

// Metadata types
export interface CensusVariable {
  code: string;
  name: string;
  concept: string;
  group: string;
  universe: string;
}

export interface CensusVariablesResponse {
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

export interface POITypesResponse {
  poi_types: POIType[];
  total_count: number;
  categories: string[];
}

export interface LocationSearchResult {
  display_name: string;
  city?: string;
  state?: string;
  country?: string;
  latitude: number;
  longitude: number;
  importance?: number;
  place_type?: string;
}

export interface LocationSearchResponse {
  query: string;
  results: LocationSearchResult[];
  total_count: number;
}