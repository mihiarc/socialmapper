/**
 * Application configuration with environment variable support
 * Uses Vite's import.meta.env for environment variables
 */

import { validateConfig, parseEnvVar, EnvValidators, checkConfigHealth, type ValidatedConfig } from './validation';

export interface AppConfig {
  api: {
    baseURL: string;
    apiKey?: string;
    timeout: number;
    retryAttempts: number;
    retryDelay: number;
  };
  features: {
    enableCustomPOIs: boolean;
    enableBatchAnalysis: boolean;
    enableAdvancedFilters: boolean;
    enableExperimental: boolean;
  };
  map: {
    defaultCenter: [number, number];
    defaultZoom: number;
    minZoom: number;
    maxZoom: number;
    tileProvider: 'openstreetmap' | 'mapbox' | 'stadia';
    mapboxToken?: string;
  };
  ui: {
    theme: 'light' | 'dark' | 'system';
    dateFormat: string;
    numberFormat: string;
    maxToastMessages: number;
    toastDuration: number;
  };
  analysis: {
    defaultTravelTime: number;
    maxTravelTime: number;
    defaultTravelMode: 'walk' | 'bike' | 'drive' | 'transit';
    pollingInterval: number;
    maxPollingAttempts: number;
  };
  development: {
    enableDevTools: boolean;
    enableLogging: boolean;
    logLevel: 'debug' | 'info' | 'warn' | 'error';
    mockAPI: boolean;
  };
}

/**
 * Default configuration values
 */
const defaultConfig: AppConfig = {
  api: {
    baseURL: 'http://localhost:8000',
    apiKey: undefined,
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
  },
  features: {
    enableCustomPOIs: true,
    enableBatchAnalysis: true,
    enableAdvancedFilters: false,
    enableExperimental: false,
  },
  map: {
    defaultCenter: [40.7128, -74.0060], // NYC
    defaultZoom: 10,
    minZoom: 3,
    maxZoom: 18,
    tileProvider: 'openstreetmap',
    mapboxToken: undefined,
  },
  ui: {
    theme: 'system',
    dateFormat: 'MM/DD/YYYY',
    numberFormat: 'en-US',
    maxToastMessages: 5,
    toastDuration: 5000,
  },
  analysis: {
    defaultTravelTime: 15,
    maxTravelTime: 60,
    defaultTravelMode: 'walk',
    pollingInterval: 2000,
    maxPollingAttempts: 300, // 10 minutes max
  },
  development: {
    enableDevTools: true,
    enableLogging: true,
    logLevel: 'info',
    mockAPI: false,
  },
};

/**
 * Parse boolean environment variables
 */
function parseBoolean(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true';
}

/**
 * Parse number environment variables
 */
function parseNumber(value: string | undefined, defaultValue: number): number {
  if (value === undefined) return defaultValue;
  const parsed = Number(value);
  return isNaN(parsed) ? defaultValue : parsed;
}

/**
 * Get env vars safely for both Vite and Jest environments
 */
const getEnv = () => {
  try {
    // @ts-ignore
    return import.meta.env || {};
  } catch {
    // Fallback for test environment - use globals from Jest config
    if (typeof global !== 'undefined' && (global as any)['import.meta']) {
      return (global as any)['import.meta'].env;
    }
    return {};
  }
};

/**
 * Build configuration from environment variables
 */
function buildConfig(): AppConfig {
  const env = getEnv();

  return {
    api: {
      baseURL: parseEnvVar(env.VITE_API_URL, EnvValidators.string, defaultConfig.api.baseURL),
      apiKey: parseEnvVar(env.VITE_API_KEY, EnvValidators.optionalString, undefined),
      timeout: parseEnvVar(env.VITE_API_TIMEOUT, EnvValidators.positiveNumber, defaultConfig.api.timeout),
      retryAttempts: parseEnvVar(env.VITE_API_RETRY_ATTEMPTS, EnvValidators.positiveNumber, defaultConfig.api.retryAttempts),
      retryDelay: parseEnvVar(env.VITE_API_RETRY_DELAY, EnvValidators.positiveNumber, defaultConfig.api.retryDelay),
    },
    features: {
      enableCustomPOIs: parseBoolean(env.VITE_ENABLE_CUSTOM_POIS, defaultConfig.features.enableCustomPOIs),
      enableBatchAnalysis: parseBoolean(env.VITE_ENABLE_BATCH_ANALYSIS, defaultConfig.features.enableBatchAnalysis),
      enableAdvancedFilters: parseBoolean(env.VITE_ENABLE_ADVANCED_FILTERS, defaultConfig.features.enableAdvancedFilters),
      enableExperimental: parseBoolean(env.VITE_ENABLE_EXPERIMENTAL, defaultConfig.features.enableExperimental),
    },
    map: {
      defaultCenter: [
        parseNumber(env.VITE_MAP_CENTER_LAT, defaultConfig.map.defaultCenter[0]),
        parseNumber(env.VITE_MAP_CENTER_LNG, defaultConfig.map.defaultCenter[1]),
      ],
      defaultZoom: parseNumber(env.VITE_MAP_DEFAULT_ZOOM, defaultConfig.map.defaultZoom),
      minZoom: parseNumber(env.VITE_MAP_MIN_ZOOM, defaultConfig.map.minZoom),
      maxZoom: parseNumber(env.VITE_MAP_MAX_ZOOM, defaultConfig.map.maxZoom),
      tileProvider: (env.VITE_MAP_TILE_PROVIDER || defaultConfig.map.tileProvider) as AppConfig['map']['tileProvider'],
      mapboxToken: env.VITE_MAPBOX_TOKEN || undefined,
    },
    ui: {
      theme: (env.VITE_UI_THEME || defaultConfig.ui.theme) as AppConfig['ui']['theme'],
      dateFormat: env.VITE_UI_DATE_FORMAT || defaultConfig.ui.dateFormat,
      numberFormat: env.VITE_UI_NUMBER_FORMAT || defaultConfig.ui.numberFormat,
      maxToastMessages: parseNumber(env.VITE_UI_MAX_TOAST_MESSAGES, defaultConfig.ui.maxToastMessages),
      toastDuration: parseNumber(env.VITE_UI_TOAST_DURATION, defaultConfig.ui.toastDuration),
    },
    analysis: {
      defaultTravelTime: parseNumber(env.VITE_ANALYSIS_DEFAULT_TRAVEL_TIME, defaultConfig.analysis.defaultTravelTime),
      maxTravelTime: parseNumber(env.VITE_ANALYSIS_MAX_TRAVEL_TIME, defaultConfig.analysis.maxTravelTime),
      defaultTravelMode: (env.VITE_ANALYSIS_DEFAULT_TRAVEL_MODE || defaultConfig.analysis.defaultTravelMode) as AppConfig['analysis']['defaultTravelMode'],
      pollingInterval: parseNumber(env.VITE_ANALYSIS_POLLING_INTERVAL, defaultConfig.analysis.pollingInterval),
      maxPollingAttempts: parseNumber(env.VITE_ANALYSIS_MAX_POLLING_ATTEMPTS, defaultConfig.analysis.maxPollingAttempts),
    },
    development: {
      enableDevTools: parseBoolean(env.VITE_DEV_ENABLE_DEVTOOLS, defaultConfig.development.enableDevTools),
      enableLogging: parseBoolean(env.VITE_DEV_ENABLE_LOGGING, defaultConfig.development.enableLogging),
      logLevel: (env.VITE_DEV_LOG_LEVEL || defaultConfig.development.logLevel) as AppConfig['development']['logLevel'],
      mockAPI: parseBoolean(env.VITE_DEV_MOCK_API, defaultConfig.development.mockAPI),
    },
  };
}


/**
 * Create and export the configuration singleton
 */
let _config: AppConfig;
let _healthCheck: ReturnType<typeof checkConfigHealth>;

try {
  _config = buildConfig();
  const validatedConfig = validateConfig(_config) as AppConfig;
  _config = validatedConfig;
  _healthCheck = checkConfigHealth(_config);
  
  // Log warnings in development
  if (getEnv().DEV && _healthCheck.warnings.length > 0) {
    console.warn('Configuration warnings:', _healthCheck.warnings);
  }
} catch (error) {
  console.error('Configuration error:', error);
  // Fall back to default configuration
  _config = defaultConfig;
  _healthCheck = { valid: false, errors: [error?.message || 'Unknown configuration error'], warnings: [] };
}

export const config = _config;
export const configHealthCheck = _healthCheck;

/**
 * Helper function to get nested config values
 */
export function getConfigValue<T>(path: string, defaultValue?: T): T {
  const keys = path.split('.');
  let value: any = config;

  for (const key of keys) {
    if (value && typeof value === 'object' && key in value) {
      value = value[key];
    } else {
      return defaultValue as T;
    }
  }

  return value as T;
}

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(feature: keyof AppConfig['features']): boolean {
  return config.features[feature];
}

/**
 * Export configuration for debugging (only in development)
 */
if (getEnv().DEV && config.development.enableDevTools) {
  (window as any).__SOCIALMAPPER_CONFIG__ = config;
}