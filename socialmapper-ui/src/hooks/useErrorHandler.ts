/**
 * React hook for centralized error handling and user feedback
 */

import { useState, useCallback, useEffect } from 'react';
import { APIError } from '../types/api';

export type ErrorSeverity = 'info' | 'warning' | 'error' | 'success';

export interface ErrorMessage {
  id: string;
  message: string;
  severity: ErrorSeverity;
  details?: any;
  timestamp: Date;
  duration?: number; // Auto-dismiss after milliseconds
}

export interface UseErrorHandlerOptions {
  defaultDuration?: number; // Default auto-dismiss duration in milliseconds
  maxErrors?: number; // Maximum number of errors to display at once
  onError?: (error: ErrorMessage) => void;
}

/**
 * Hook for centralized error handling and user notifications
 */
export function useErrorHandler(options: UseErrorHandlerOptions = {}) {
  const {
    defaultDuration = 5000,
    maxErrors = 5,
    onError,
  } = options;

  const [errors, setErrors] = useState<ErrorMessage[]>([]);

  // Add a new error
  const addError = useCallback((
    message: string,
    severity: ErrorSeverity = 'error',
    details?: any,
    duration?: number
  ) => {
    const newError: ErrorMessage = {
      id: `error-${Date.now()}-${Math.random()}`,
      message,
      severity,
      details,
      timestamp: new Date(),
      duration: duration ?? (severity === 'error' ? undefined : defaultDuration),
    };

    setErrors(prev => {
      // Limit the number of errors
      const updated = [...prev, newError];
      if (updated.length > maxErrors) {
        return updated.slice(-maxErrors);
      }
      return updated;
    });

    // Call the onError callback if provided
    onError?.(newError);

    return newError.id;
  }, [defaultDuration, maxErrors, onError]);

  // Remove an error by ID
  const removeError = useCallback((errorId: string) => {
    setErrors(prev => prev.filter(error => error.id !== errorId));
  }, []);

  // Clear all errors
  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  // Handle API errors
  const handleAPIError = useCallback((error: APIError) => {
    const userMessage = getHumanReadableError(error);
    const severity = getErrorSeverity(error.error_code);
    
    addError(userMessage, severity, error.details);
  }, [addError]);

  // Handle generic errors
  const handleError = useCallback((error: Error | string) => {
    const message = typeof error === 'string' ? error : error.message;
    addError(message, 'error');
  }, [addError]);

  // Show success message
  const showSuccess = useCallback((message: string, duration?: number) => {
    addError(message, 'success', undefined, duration ?? defaultDuration);
  }, [addError, defaultDuration]);

  // Show info message
  const showInfo = useCallback((message: string, duration?: number) => {
    addError(message, 'info', undefined, duration ?? defaultDuration);
  }, [addError, defaultDuration]);

  // Show warning message
  const showWarning = useCallback((message: string, duration?: number) => {
    addError(message, 'warning', undefined, duration ?? defaultDuration);
  }, [addError, defaultDuration]);

  // Auto-dismiss errors with duration
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];

    errors.forEach(error => {
      if (error.duration && error.duration > 0) {
        const timer = setTimeout(() => {
          removeError(error.id);
        }, error.duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [errors, removeError]);

  // Get the most recent error
  const latestError = errors.length > 0 ? errors[errors.length - 1] : null;

  // Check if there are any errors of a specific severity
  const hasErrors = useCallback((severity?: ErrorSeverity) => {
    if (!severity) return errors.length > 0;
    return errors.some(error => error.severity === severity);
  }, [errors]);

  return {
    // State
    errors,
    latestError,
    hasErrors,
    
    // Actions
    addError,
    removeError,
    clearErrors,
    handleAPIError,
    handleError,
    showSuccess,
    showInfo,
    showWarning,
  };
}

/**
 * Convert API error codes to human-readable messages
 */
function getHumanReadableError(error: APIError): string {
  const errorMessages: Record<string, string> = {
    // Job-related errors
    JOB_NOT_FOUND: 'The requested analysis could not be found.',
    JOB_PENDING: 'The analysis is queued and will start soon.',
    JOB_RUNNING: 'The analysis is currently in progress.',
    JOB_FAILED: 'The analysis failed to complete. Please try again.',
    JOB_CANCELLED: 'The analysis was cancelled.',
    JOB_NOT_COMPLETED: 'The analysis is not yet completed.',
    
    // Validation errors
    VALIDATION_ERROR: 'Please check your input and try again.',
    INVALID_LOCATION: 'The specified location could not be found.',
    INVALID_POI_TYPE: 'The selected place type is not supported.',
    INVALID_TRAVEL_MODE: 'The selected travel mode is not supported.',
    INVALID_CENSUS_VARIABLE: 'One or more census variables are not valid.',
    INVALID_FILE_FORMAT: 'The uploaded file format is not supported.',
    
    // Rate limiting
    RATE_LIMIT_EXCEEDED: 'Too many requests. Please wait a moment and try again.',
    
    // Authentication
    UNAUTHORIZED: 'You are not authorized to perform this action.',
    API_KEY_INVALID: 'The API key is invalid or has expired.',
    
    // Server errors
    INTERNAL_ERROR: 'An unexpected error occurred. Please try again later.',
    SERVICE_UNAVAILABLE: 'The service is temporarily unavailable.',
    CENSUS_API_ERROR: 'Unable to retrieve census data. Please try again later.',
    OSM_API_ERROR: 'Unable to retrieve map data. Please try again later.',
    
    // Export errors
    EXPORT_ERROR: 'Failed to export the results. Please try again.',
    EXPORT_NOT_FOUND: 'The requested export could not be found.',
    
    // File errors
    FILE_TOO_LARGE: 'The uploaded file is too large. Maximum size is 10MB.',
    FILE_PARSE_ERROR: 'Unable to parse the uploaded file. Please check the format.',
    NO_VALID_LOCATIONS: 'No valid locations found in the uploaded file.',
  };

  // Return custom message if available, otherwise use the API message
  return errorMessages[error.error_code] || error.message || 'An unexpected error occurred.';
}

/**
 * Determine error severity based on error code
 */
function getErrorSeverity(errorCode: string): ErrorSeverity {
  const warningSeverityCodes = [
    'JOB_PENDING',
    'JOB_RUNNING',
    'RATE_LIMIT_EXCEEDED',
    'NO_VALID_LOCATIONS',
  ];

  const infoSeverityCodes = [
    'JOB_CANCELLED',
  ];

  if (infoSeverityCodes.includes(errorCode)) return 'info';
  if (warningSeverityCodes.includes(errorCode)) return 'warning';
  return 'error';
}

/**
 * Hook for displaying errors in a toast-like notification system
 */
export function useToastErrors() {
  const [toasts, setToasts] = useState<ErrorMessage[]>([]);

  const showToast = useCallback((message: ErrorMessage) => {
    setToasts(prev => [...prev, message]);

    // Auto-remove after duration
    if (message.duration) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== message.id));
      }, message.duration);
    }
  }, []);

  const removeToast = useCallback((toastId: string) => {
    setToasts(prev => prev.filter(t => t.id !== toastId));
  }, []);

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    showToast,
    removeToast,
    clearToasts,
  };
}