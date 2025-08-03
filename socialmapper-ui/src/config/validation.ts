/**
 * Configuration validation utilities with TypeScript type safety
 */

import { z } from 'zod';
import { AppConfig } from './index';

/**
 * Zod schema for configuration validation
 */
export const ConfigSchema = z.object({
  api: z.object({
    baseURL: z.string().url('Invalid API base URL'),
    apiKey: z.string().optional(),
    timeout: z.number().positive('API timeout must be positive'),
    retryAttempts: z.number().min(0).max(10, 'Retry attempts must be between 0 and 10'),
    retryDelay: z.number().min(100).max(10000, 'Retry delay must be between 100ms and 10s'),
  }),
  features: z.object({
    enableCustomPOIs: z.boolean(),
    enableBatchAnalysis: z.boolean(),
    enableAdvancedFilters: z.boolean(),
    enableExperimental: z.boolean(),
  }),
  map: z.object({
    defaultCenter: z.tuple([
      z.number().min(-90).max(90, 'Latitude must be between -90 and 90'),
      z.number().min(-180).max(180, 'Longitude must be between -180 and 180'),
    ]),
    defaultZoom: z.number().min(1).max(20),
    minZoom: z.number().min(1).max(20),
    maxZoom: z.number().min(1).max(20),
    tileProvider: z.enum(['openstreetmap', 'mapbox', 'stadia']),
    mapboxToken: z.string().optional(),
  }).refine((data) => data.defaultZoom >= data.minZoom && data.defaultZoom <= data.maxZoom, {
    message: 'Default zoom must be between min and max zoom',
  }).refine((data) => data.tileProvider !== 'mapbox' || data.mapboxToken, {
    message: 'Mapbox token is required when using Mapbox tile provider',
  }),
  ui: z.object({
    theme: z.enum(['light', 'dark', 'system']),
    dateFormat: z.string(),
    numberFormat: z.string(),
    maxToastMessages: z.number().min(1).max(10),
    toastDuration: z.number().min(1000).max(30000),
  }),
  analysis: z.object({
    defaultTravelTime: z.number().min(5).max(60),
    maxTravelTime: z.number().min(5).max(120),
    defaultTravelMode: z.enum(['walk', 'bike', 'drive', 'transit']),
    pollingInterval: z.number().min(500).max(10000),
    maxPollingAttempts: z.number().min(10).max(600),
  }).refine((data) => data.defaultTravelTime <= data.maxTravelTime, {
    message: 'Default travel time cannot exceed max travel time',
  }),
  development: z.object({
    enableDevTools: z.boolean(),
    enableLogging: z.boolean(),
    logLevel: z.enum(['debug', 'info', 'warn', 'error']),
    mockAPI: z.boolean(),
  }),
});

export type ValidatedConfig = z.infer<typeof ConfigSchema>;

/**
 * Configuration validation error
 */
export class ConfigValidationError extends Error {
  public readonly errors: z.ZodError;

  constructor(errors: z.ZodError) {
    const errorMessages = errors.errors.map(err => 
      `${err.path.join('.')}: ${err.message}`
    ).join('\n');
    
    super(`Configuration validation failed:\n${errorMessages}`);
    this.name = 'ConfigValidationError';
    this.errors = errors;
  }
}

/**
 * Validate configuration object
 */
export function validateConfig(config: unknown): ValidatedConfig {
  try {
    return ConfigSchema.parse(config);
  } catch (error) {
    if (error instanceof z.ZodError) {
      throw new ConfigValidationError(error);
    }
    throw error;
  }
}

/**
 * Safe configuration getter with runtime validation
 */
export function safeGetConfig<T>(
  config: AppConfig,
  path: string,
  validator: z.ZodType<T>
): T | undefined {
  try {
    const keys = path.split('.');
    let value: any = config;

    for (const key of keys) {
      if (value && typeof value === 'object' && key in value) {
        value = value[key];
      } else {
        return undefined;
      }
    }

    return validator.parse(value);
  } catch {
    return undefined;
  }
}

/**
 * Environment variable validators
 */
export const EnvValidators = {
  url: z.string().url(),
  port: z.coerce.number().int().min(1).max(65535),
  boolean: z.enum(['true', 'false']).transform(val => val === 'true'),
  number: z.coerce.number(),
  positiveNumber: z.coerce.number().positive(),
  string: z.string().min(1),
  optionalString: z.string().optional(),
};

/**
 * Parse and validate environment variable
 */
export function parseEnvVar<T>(
  value: string | undefined,
  validator: z.ZodType<T>,
  defaultValue: T
): T {
  if (value === undefined || value === '') {
    return defaultValue;
  }

  try {
    return validator.parse(value);
  } catch (error) {
    console.warn(`Invalid environment variable value: ${value}`, error);
    return defaultValue;
  }
}

/**
 * Configuration health check
 */
export interface ConfigHealthCheck {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

export function checkConfigHealth(config: AppConfig): ConfigHealthCheck {
  const errors: string[] = [];
  const warnings: string[] = [];

  try {
    validateConfig(config);
  } catch (error) {
    if (error instanceof ConfigValidationError) {
      errors.push(...error.errors.errors.map(err => 
        `${err.path.join('.')}: ${err.message}`
      ));
    }
  }

  // Additional health checks
  if (!config.api.apiKey && config.api.baseURL.includes('production')) {
    warnings.push('API key is not set for production environment');
  }

  if (config.development.mockAPI && !import.meta.env.DEV) {
    warnings.push('Mock API is enabled in non-development environment');
  }

  if (config.analysis.maxPollingAttempts * config.analysis.pollingInterval > 1800000) {
    warnings.push('Maximum polling duration exceeds 30 minutes');
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}