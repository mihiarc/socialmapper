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

// Feedback System Types
export interface FeedbackRequest {
  type: FeedbackType;
  touchpoint: FeedbackTouchpoint;
  rating?: number; // 1-5 star rating
  comment?: string;
  context?: FeedbackContext;
  metadata?: Record<string, any>;
  user_id?: string; // Optional anonymous identifier
}

export interface FeedbackResponse extends BaseResponse {
  id: string;
  type: FeedbackType;
  touchpoint: FeedbackTouchpoint;
  rating?: number;
  comment?: string;
  context?: FeedbackContext;
  created_at: string;
  status: 'pending' | 'reviewed' | 'resolved';
}

export interface FeedbackContext {
  job_id?: string;
  page_url?: string;
  user_agent?: string;
  session_duration?: number;
  error_occurred?: boolean;
  feature_used?: string;
}

export type FeedbackType = 
  | 'rating' 
  | 'usability' 
  | 'bug_report' 
  | 'feature_request' 
  | 'general';

export type FeedbackTouchpoint = 
  | 'post_analysis' 
  | 'configuration_wizard' 
  | 'results_dashboard' 
  | 'error_state' 
  | 'export_download' 
  | 'general_usage';

// Analytics Types
export interface UserAnalyticsEvent {
  event_name: string;
  event_category: 'navigation' | 'interaction' | 'conversion' | 'error';
  properties?: Record<string, any>;
  timestamp?: string;
  session_id?: string;
  user_id?: string;
}

export interface UserJourneyStep {
  step_name: string;
  timestamp: string;
  duration_ms?: number;
  completed: boolean;
  error?: string;
}

export interface UserSession {
  session_id: string;
  started_at: string;
  ended_at?: string;
  total_duration_ms?: number;
  page_views: number;
  interactions: number;
  conversion_events: string[];
  journey_steps: UserJourneyStep[];
}

// Feature Request Types
export interface FeatureRequest extends BaseResponse {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'submitted' | 'under_review' | 'planned' | 'in_development' | 'completed' | 'rejected';
  votes: number;
  github_issue_url?: string;
  created_at: string;
  updated_at: string;
}

export interface FeatureVoteRequest {
  feature_id: string;
  vote_type: 'upvote' | 'downvote';
}

export interface FeatureVote extends BaseResponse {
  feature_id: string;
  user_id?: string;
  vote_type: 'upvote' | 'downvote';
  created_at: string;
}

// User Interview Types
export interface InterviewRequest {
  name: string;
  email: string;
  user_type: 'academic' | 'government' | 'nonprofit' | 'corporate' | 'individual';
  research_focus?: string;
  preferred_times: string[];
  timezone: string;
  interview_type: 'usability' | 'feature_discussion' | 'workflow_analysis' | 'general_feedback';
}

export interface InterviewSession extends BaseResponse {
  id: string;
  participant_id: string;
  scheduled_at: string;
  duration_minutes: number;
  interview_type: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  recording_url?: string;
  notes?: string;
  insights: string[];
  created_at: string;
}

// Summary and Insights Types
export interface FeedbackSummary extends BaseResponse {
  total_feedback: number;
  average_rating: number;
  feedback_by_type: Record<FeedbackType, number>;
  feedback_by_touchpoint: Record<FeedbackTouchpoint, number>;
  recent_comments: string[];
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  period_days: number;
  response_rate?: number;
  recent_feedback_count?: number;
}

export interface AnalyticsSummary extends BaseResponse {
  total_events: number;
  unique_users: number;
  unique_sessions: number;
  events_by_category: Record<string, number>;
  top_events: Array<{ name: string; count: number }>;
  conversion_rate: number;
  average_session_duration_ms: number;
  period_days: number;
  total_sessions?: number;
  total_page_views?: number;
  total_conversions?: number;
  user_journey_funnel?: Array<{ stage: string; users: number; dropoff_rate?: number }>;
}

export interface FeedbackInsights extends BaseResponse {
  top_issues: Array<{ issue: string; count: number; severity: string }>;
  trending_topics: string[];
  user_satisfaction_score: number;
  improvement_suggestions: Array<{ suggestion: string; impact: 'low' | 'medium' | 'high' }>;
  feature_adoption_rates: Record<string, number>;
  period_days: number;
  sentiment_score?: number;
  common_themes?: string[];
}