/**
 * Application constants
 */

// Application info
export const APP_VERSION = import.meta.env.VITE_APP_VERSION || '1.0.0';
export const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'SocialMapper';
export const BUILD_DATE = (typeof __BUILD_DATE__ !== 'undefined' ? __BUILD_DATE__ : new Date().toISOString());

// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';
export const API_TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT) || 30000;

// Map configuration
export const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN;
export const DEFAULT_MAP_CENTER: [number, number] = [-98.5795, 39.8283]; // Geographic center of US
export const DEFAULT_MAP_ZOOM = 4;

// Analysis defaults
export const DEFAULT_TRAVEL_TIME = 15; // minutes
export const DEFAULT_TRAVEL_MODE = 'walk';
export const DEFAULT_GEOGRAPHIC_LEVEL = 'block_group';
export const DEFAULT_CENSUS_VARIABLES = ['B01003_001E']; // Total population

// Export formats
export const EXPORT_FORMATS = {
  CSV: 'csv',
  GEOJSON: 'geojson',
  PARQUET: 'parquet',
  GEOPARQUET: 'geoparquet',
} as const;

// File size limits (in bytes)
export const MAX_FILE_UPLOAD_SIZE = 10 * 1024 * 1024; // 10MB
export const MAX_CUSTOM_POIS = 100;

// Polling intervals
export const JOB_STATUS_POLL_INTERVAL = 2000; // 2 seconds
export const HEALTH_CHECK_INTERVAL = 30000; // 30 seconds

// UI constants
export const SIDEBAR_WIDTH = 240;
export const HEADER_HEIGHT = 64;
export const MOBILE_BREAKPOINT = 768;

// Success metrics (from requirements)
export const TARGET_COMPLETION_RATE = 0.75; // 75%
export const TARGET_ONBOARDING_TIME = 5 * 60 * 1000; // 5 minutes in milliseconds
export const TARGET_VALIDATION_ERRORS = 3;
export const TARGET_SATISFACTION_SCORE = 0.9; // 90%

// Demo scenarios
export const DEMO_CATEGORIES = {
  EDUCATION: 'Education & Culture',
  FOOD_SECURITY: 'Food Security',
  HEALTHCARE: 'Healthcare',
  RECREATION: 'Recreation',
  TRANSPORTATION: 'Transportation',
} as const;

// Color schemes
export const STATUS_COLORS = {
  pending: '#faad14',
  running: '#1890ff',
  completed: '#52c41a',
  failed: '#ff4d4f',
  cancelled: '#d9d9d9',
} as const;

export const CATEGORY_COLORS = {
  [DEMO_CATEGORIES.EDUCATION]: '#722ed1',
  [DEMO_CATEGORIES.FOOD_SECURITY]: '#fa8c16',
  [DEMO_CATEGORIES.HEALTHCARE]: '#f5222d',
  [DEMO_CATEGORIES.RECREATION]: '#52c41a',
  [DEMO_CATEGORIES.TRANSPORTATION]: '#1890ff',
} as const;

// Feature flags
export const FEATURES = {
  DEMO_SCENARIOS: import.meta.env.VITE_ENABLE_DEMO_SCENARIOS !== 'false',
  CUSTOM_POI: import.meta.env.VITE_ENABLE_CUSTOM_POI !== 'false',
  BATCH_ANALYSIS: import.meta.env.VITE_ENABLE_BATCH_ANALYSIS === 'true',
  DEVTOOLS: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true',
} as const;

// Local storage keys
export const STORAGE_KEYS = {
  THEME: 'socialmapper_theme',
  MAP_STYLE: 'socialmapper_map_style',
  SIDEBAR_COLLAPSED: 'socialmapper_sidebar_collapsed',
  RECENT_LOCATIONS: 'socialmapper_recent_locations',
  USER_PREFERENCES: 'socialmapper_user_preferences',
} as const;

// Census variable categories (common ones)
export const CENSUS_CATEGORIES = {
  POPULATION: 'Population',
  HOUSING: 'Housing',
  INCOME: 'Income and Poverty',
  EMPLOYMENT: 'Employment',
  EDUCATION: 'Education',
  TRANSPORTATION: 'Transportation',
  DEMOGRAPHICS: 'Demographics',
} as const;

// Travel modes with display names
export const TRAVEL_MODES = {
  walk: 'Walking',
  bike: 'Cycling',
  drive: 'Driving',
  transit: 'Public Transit',
} as const;

// Geographic levels with display names
export const GEOGRAPHIC_LEVELS = {
  block_group: 'Block Group',
  tract: 'Census Tract',
  county: 'County',
} as const;