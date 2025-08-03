export const config = {
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
    defaultCenter: [40.7128, -74.0060],
    defaultZoom: 10,
    minZoom: 3,
    maxZoom: 18,
    tileProvider: 'openstreetmap' as const,
    mapboxToken: undefined,
  },
  ui: {
    theme: 'system' as const,
    dateFormat: 'MM/DD/YYYY',
    numberFormat: 'en-US',
    maxToastMessages: 5,
    toastDuration: 5000,
  },
  analysis: {
    defaultTravelTime: 15,
    maxTravelTime: 60,
    defaultTravelMode: 'walk' as const,
    pollingInterval: 2000,
    maxPollingAttempts: 300,
  },
  development: {
    enableDevTools: false,
    enableLogging: false,
    logLevel: 'info' as const,
    mockAPI: false,
  },
};

export const configHealthCheck = { 
  valid: true, 
  errors: [], 
  warnings: [] 
};

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

export function isFeatureEnabled(feature: keyof typeof config.features): boolean {
  return config.features[feature];
}