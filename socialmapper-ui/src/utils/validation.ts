/**
 * Form validation utilities
 */
import type { LocationAnalysisRequest, CustomPOIAnalysisRequest } from '@types/api';

export interface ValidationError {
  field: string;
  message: string;
}

export type ValidationResult = {
  isValid: boolean;
  errors: ValidationError[];
};

/**
 * Validate location analysis request
 */
export const validateLocationAnalysis = (request: Partial<LocationAnalysisRequest>): ValidationResult => {
  const errors: ValidationError[] = [];

  // Required fields
  if (!request.location || request.location.trim().length < 3) {
    errors.push({
      field: 'location',
      message: 'Location must be at least 3 characters long',
    });
  }

  if (!request.poi_type || request.poi_type.trim().length < 2) {
    errors.push({
      field: 'poi_type',
      message: 'POI type must be at least 2 characters long',
    });
  }

  if (!request.poi_name || request.poi_name.trim().length < 2) {
    errors.push({
      field: 'poi_name',
      message: 'POI name must be at least 2 characters long',
    });
  }

  // Travel time validation
  if (request.travel_time !== undefined && (request.travel_time < 1 || request.travel_time > 120)) {
    errors.push({
      field: 'travel_time',
      message: 'Travel time must be between 1 and 120 minutes',
    });
  }

  // Census variables validation
  if (request.census_variables && request.census_variables.length === 0) {
    errors.push({
      field: 'census_variables',
      message: 'At least one census variable must be selected',
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate custom POI analysis request
 */
export const validateCustomPOIAnalysis = (request: Partial<CustomPOIAnalysisRequest>): ValidationResult => {
  const errors: ValidationError[] = [];

  // Location validation
  if (!request.location || request.location.trim().length < 3) {
    errors.push({
      field: 'location',
      message: 'Location must be at least 3 characters long',
    });
  }

  // Custom POIs validation
  if (!request.custom_pois || request.custom_pois.length === 0) {
    errors.push({
      field: 'custom_pois',
      message: 'At least one custom POI must be provided',
    });
  } else if (request.custom_pois.length > 100) {
    errors.push({
      field: 'custom_pois',
      message: 'Too many custom POIs (maximum 100 allowed)',
    });
  } else {
    // Validate each custom POI
    request.custom_pois.forEach((poi, index) => {
      if (!poi.name || poi.name.trim().length === 0) {
        errors.push({
          field: `custom_pois[${index}].name`,
          message: `POI ${index + 1} name cannot be empty`,
        });
      }

      if (poi.latitude < -90 || poi.latitude > 90) {
        errors.push({
          field: `custom_pois[${index}].latitude`,
          message: `POI ${index + 1} latitude must be between -90 and 90`,
        });
      }

      if (poi.longitude < -180 || poi.longitude > 180) {
        errors.push({
          field: `custom_pois[${index}].longitude`,
          message: `POI ${index + 1} longitude must be between -180 and 180`,
        });
      }
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Validate email address
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate coordinates
 */
export const isValidLatitude = (lat: number): boolean => {
  return lat >= -90 && lat <= 90;
};

export const isValidLongitude = (lng: number): boolean => {
  return lng >= -180 && lng <= 180;
};

/**
 * Validate census variable format
 */
export const isValidCensusVariable = (variable: string): boolean => {
  // Basic census variable format: B01003_001E
  const censusRegex = /^[A-Z]\d{5}_\d{3}[E|M]$/;
  return censusRegex.test(variable);
};

/**
 * Clean and validate location string
 */
export const sanitizeLocation = (location: string): string => {
  return location.trim().replace(/[<>]/g, ''); // Remove potentially dangerous characters
};

/**
 * Validate file upload
 */
export const validateFileUpload = (file: File, maxSize: number = 10 * 1024 * 1024): ValidationResult => {
  const errors: ValidationError[] = [];

  if (file.size > maxSize) {
    errors.push({
      field: 'file',
      message: `File size must be less than ${Math.round(maxSize / 1024 / 1024)}MB`,
    });
  }

  const allowedTypes = ['application/json', 'text/csv', 'application/vnd.ms-excel'];
  if (!allowedTypes.includes(file.type)) {
    errors.push({
      field: 'file',
      message: 'Only JSON and CSV files are allowed',
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
};