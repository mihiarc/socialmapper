/**
 * Application configuration settings for the SocialMapper React frontend.
 * 
 * These settings are loaded from environment variables at build time
 * using Vite's import.meta.env system.
 */

export interface AppConfig {
  // API Configuration
  apiBaseUrl: string;
  apiTimeout: number;
  pollInterval: number;
  
  // File Upload Configuration
  maxFileSizeMB: number;
  allowedFileTypes: string[];
  
  // Map Configuration
  defaultMapCenter: [number, number];
  defaultMapZoom: number;
  mapTileUrl: string;
  mapAttribution: string;
  
  // Feature Flags
  enableBatchAnalysis: boolean;
  enableExperimentalFeatures: boolean;
  
  // Analytics (optional)
  analyticsEnabled: boolean;
  analyticsId?: string;
}

// Get env vars safely for both Vite and Jest environments
const getEnv = () => {
  try {
    // @ts-ignore
    return import.meta.env || {};
  } catch {
    // Fallback for test environment
    return {};
  }
};

const env = getEnv();

export const config: AppConfig = {
  // API Configuration
  apiBaseUrl: env.VITE_API_BASE_URL || 'http://localhost:8000',
  apiTimeout: parseInt(env.VITE_API_TIMEOUT || '300000'), // 5 minutes
  pollInterval: parseInt(env.VITE_POLL_INTERVAL || '2000'), // 2 seconds
  
  // File Upload Configuration
  maxFileSizeMB: parseInt(env.VITE_MAX_FILE_SIZE_MB || '10'),
  allowedFileTypes: (env.VITE_ALLOWED_FILE_TYPES || '.csv,.xlsx,.xls,.json,.geojson').split(','),
  
  // Map Configuration
  defaultMapCenter: [
    parseFloat(env.VITE_DEFAULT_MAP_LAT || '45.5152'),
    parseFloat(env.VITE_DEFAULT_MAP_LNG || '-122.6784')
  ] as [number, number], // Portland, OR
  defaultMapZoom: parseInt(env.VITE_DEFAULT_MAP_ZOOM || '12'),
  mapTileUrl: env.VITE_MAP_TILE_URL || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  mapAttribution: env.VITE_MAP_ATTRIBUTION || 
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  
  // Feature Flags
  enableBatchAnalysis: env.VITE_ENABLE_BATCH_ANALYSIS === 'true',
  enableExperimentalFeatures: env.VITE_ENABLE_EXPERIMENTAL === 'true',
  
  // Analytics
  analyticsEnabled: env.VITE_ANALYTICS_ENABLED === 'true',
  analyticsId: env.VITE_ANALYTICS_ID,
};

// Validate configuration at runtime
export function validateConfig(): void {
  const errors: string[] = [];
  
  if (!config.apiBaseUrl) {
    errors.push('API base URL is required');
  }
  
  if (config.apiTimeout < 1000) {
    errors.push('API timeout must be at least 1000ms');
  }
  
  if (config.pollInterval < 100) {
    errors.push('Poll interval must be at least 100ms');
  }
  
  if (config.maxFileSizeMB < 1) {
    errors.push('Max file size must be at least 1MB');
  }
  
  if (config.defaultMapZoom < 1 || config.defaultMapZoom > 20) {
    errors.push('Default map zoom must be between 1 and 20');
  }
  
  if (errors.length > 0) {
    throw new Error(`Configuration validation failed:\n${errors.join('\n')}`);
  }
}

// Export environment type for TypeScript
declare global {
  interface ImportMetaEnv {
    VITE_API_BASE_URL?: string;
    VITE_API_TIMEOUT?: string;
    VITE_POLL_INTERVAL?: string;
    VITE_MAX_FILE_SIZE_MB?: string;
    VITE_ALLOWED_FILE_TYPES?: string;
    VITE_DEFAULT_MAP_LAT?: string;
    VITE_DEFAULT_MAP_LNG?: string;
    VITE_DEFAULT_MAP_ZOOM?: string;
    VITE_MAP_TILE_URL?: string;
    VITE_MAP_ATTRIBUTION?: string;
    VITE_ENABLE_BATCH_ANALYSIS?: string;
    VITE_ENABLE_EXPERIMENTAL?: string;
    VITE_ANALYTICS_ENABLED?: string;
    VITE_ANALYTICS_ID?: string;
  }
}