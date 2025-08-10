/**
 * Global type declarations for SocialMapper UI
 */

// Vite build-time constants
declare const __APP_VERSION__: string;
declare const __BUILD_DATE__: string;

// Environment variables
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_API_TIMEOUT: string;
  readonly VITE_APP_TITLE: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_MAPBOX_TOKEN: string;
  readonly VITE_ENABLE_DEMO_SCENARIOS: string;
  readonly VITE_ENABLE_CUSTOM_POI: string;
  readonly VITE_ENABLE_BATCH_ANALYSIS: string;
  readonly VITE_ENABLE_DEVTOOLS: string;
  readonly VITE_LOG_LEVEL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Extend Window interface for global objects
declare global {
  interface Window {
    // Analytics or monitoring tools
    gtag?: (...args: any[]) => void;
    dataLayer?: any[];
    
    // Development tools
    __REDUX_DEVTOOLS_EXTENSION_COMPOSE__?: any;
    
    // Feature detection
    EventSource: typeof EventSource;
  }
}

// Module declarations for assets
declare module '*.svg' {
  const content: any;
  export default content;
}

declare module '*.png' {
  const content: string;
  export default content;
}

declare module '*.jpg' {
  const content: string;
  export default content;
}

declare module '*.jpeg' {
  const content: string;
  export default content;
}

declare module '*.gif' {
  const content: string;
  export default content;
}

declare module '*.css' {
  const content: Record<string, string>;
  export default content;
}

// Utility types
export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type RequiredField<T, K extends keyof T> = T & Required<Pick<T, K>>;

// API response wrapper
export type ApiResponse<T = any> = {
  success: boolean;
  data?: T;
  error?: string;
  timestamp?: string;
};

// Pagination types
export type PaginationParams = {
  page: number;
  pageSize: number;
  total?: number;
};

export type PaginatedResponse<T> = ApiResponse<T> & {
  pagination: PaginationParams;
};

// Map-related types
export type Coordinates = [number, number]; // [longitude, latitude]
export type BoundingBox = [number, number, number, number]; // [west, south, east, north]

// Analysis configuration types
export type AnalysisPreset = 'quick_start' | 'detailed_analysis' | 'demographic_focus';

export type MapStyle = 
  | 'mapbox://styles/mapbox/light-v11'
  | 'mapbox://styles/mapbox/dark-v11'
  | 'mapbox://styles/mapbox/streets-v12'
  | 'mapbox://styles/mapbox/satellite-v9';

// Theme types
export type ThemeMode = 'light' | 'dark';
export type ColorScheme = 'blue' | 'green' | 'purple' | 'orange';

// Component prop types
export type ComponentSize = 'small' | 'middle' | 'large';
export type ButtonType = 'primary' | 'default' | 'dashed' | 'text' | 'link';
export type AlertType = 'success' | 'info' | 'warning' | 'error';

export {};