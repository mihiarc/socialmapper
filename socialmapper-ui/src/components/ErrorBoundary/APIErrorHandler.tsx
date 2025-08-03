import { ReactNode } from 'react'
import { AlertCircle, WifiOff, Clock, ShieldAlert, Ban } from 'lucide-react'
import { Alert } from '../Alert'
import { Button } from '../Button'
import { APIError, ErrorCode } from '@/types/api'

interface APIErrorHandlerProps {
  error: Error | APIError | null
  onRetry?: () => void
  className?: string
  showDetails?: boolean
}

export function APIErrorHandler({ 
  error, 
  onRetry, 
  className = '',
  showDetails = false 
}: APIErrorHandlerProps) {
  if (!error) return null

  // Parse API error
  const apiError = isAPIError(error) ? error : parseAPIError(error)
  
  // Get error icon based on error code
  const getErrorIcon = () => {
    switch (apiError.error_code) {
      case ErrorCode.NETWORK_ERROR:
        return <WifiOff className="h-5 w-5" />
      case ErrorCode.TIMEOUT_ERROR:
        return <Clock className="h-5 w-5" />
      case ErrorCode.AUTHENTICATION_ERROR:
      case ErrorCode.AUTHORIZATION_ERROR:
        return <ShieldAlert className="h-5 w-5" />
      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return <Ban className="h-5 w-5" />
      default:
        return <AlertCircle className="h-5 w-5" />
    }
  }

  // Get user-friendly message
  const getUserMessage = (): string => {
    switch (apiError.error_code) {
      case ErrorCode.NETWORK_ERROR:
        return 'Unable to connect to the server. Please check your internet connection.'
      case ErrorCode.TIMEOUT_ERROR:
        return 'The request took too long. The server might be busy.'
      case ErrorCode.AUTHENTICATION_ERROR:
        return 'Authentication failed. Please check your credentials.'
      case ErrorCode.AUTHORIZATION_ERROR:
        return 'You do not have permission to perform this action.'
      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return `Too many requests. Please wait ${apiError.details?.retry_after_seconds || 60} seconds before trying again.`
      case ErrorCode.VALIDATION_ERROR:
        return 'Please check your input and try again.'
      case ErrorCode.RESOURCE_NOT_FOUND:
        return 'The requested resource was not found.'
      case ErrorCode.SERVICE_UNAVAILABLE:
        return 'The service is temporarily unavailable. Please try again later.'
      default:
        return apiError.message || 'An unexpected error occurred.'
    }
  }

  // Get alert variant based on error severity
  const getAlertVariant = () => {
    switch (apiError.error_code) {
      case ErrorCode.VALIDATION_ERROR:
      case ErrorCode.INVALID_REQUEST:
        return 'warning'
      case ErrorCode.AUTHENTICATION_ERROR:
      case ErrorCode.AUTHORIZATION_ERROR:
      case ErrorCode.RATE_LIMIT_EXCEEDED:
        return 'error'
      default:
        return 'error'
    }
  }

  return (
    <div className={className}>
      <Alert variant={getAlertVariant()} className="mb-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            {getErrorIcon()}
          </div>
          <div className="ml-3 flex-1">
            <p className="font-semibold">
              {getErrorTitle(apiError.error_code)}
            </p>
            <p className="text-sm mt-1">
              {getUserMessage()}
            </p>
            
            {/* Show validation errors */}
            {apiError.error_code === ErrorCode.VALIDATION_ERROR && apiError.details?.field_errors && (
              <ul className="mt-2 text-sm space-y-1">
                {apiError.details.field_errors.map((fieldError: any, index: number) => (
                  <li key={index} className="flex items-start">
                    <span className="font-medium">{fieldError.field}:</span>
                    <span className="ml-2">{fieldError.message}</span>
                  </li>
                ))}
              </ul>
            )}
            
            {/* Show retry button if applicable */}
            {onRetry && canRetry(apiError.error_code) && (
              <div className="mt-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={onRetry}
                >
                  Try Again
                </Button>
              </div>
            )}
            
            {/* Show error details in development */}
            {showDetails && process.env.NODE_ENV === 'development' && (
              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-medium">
                  Error Details
                </summary>
                <pre className="mt-2 text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
                  {JSON.stringify(apiError, null, 2)}
                </pre>
              </details>
            )}
          </div>
        </div>
      </Alert>
    </div>
  )
}

// Helper functions
function isAPIError(error: any): error is APIError {
  return error && typeof error === 'object' && 'error_code' in error
}

function parseAPIError(error: Error): APIError {
  // Try to parse error message as JSON
  try {
    const parsed = JSON.parse(error.message)
    if (isAPIError(parsed)) {
      return parsed
    }
  } catch {}
  
  // Check for network errors
  if (error.message.toLowerCase().includes('network') || 
      error.message.toLowerCase().includes('fetch')) {
    return {
      error_code: ErrorCode.NETWORK_ERROR,
      message: 'Network connection error',
      details: {},
      timestamp: new Date().toISOString()
    }
  }
  
  // Check for timeout errors
  if (error.message.toLowerCase().includes('timeout')) {
    return {
      error_code: ErrorCode.TIMEOUT_ERROR,
      message: 'Request timeout',
      details: {},
      timestamp: new Date().toISOString()
    }
  }
  
  // Default to internal error
  return {
    error_code: ErrorCode.INTERNAL_ERROR,
    message: error.message,
    details: {},
    timestamp: new Date().toISOString()
  }
}

function getErrorTitle(errorCode: ErrorCode): string {
  switch (errorCode) {
    case ErrorCode.NETWORK_ERROR:
      return 'Connection Error'
    case ErrorCode.TIMEOUT_ERROR:
      return 'Request Timeout'
    case ErrorCode.AUTHENTICATION_ERROR:
      return 'Authentication Failed'
    case ErrorCode.AUTHORIZATION_ERROR:
      return 'Access Denied'
    case ErrorCode.RATE_LIMIT_EXCEEDED:
      return 'Rate Limit Exceeded'
    case ErrorCode.VALIDATION_ERROR:
      return 'Validation Error'
    case ErrorCode.RESOURCE_NOT_FOUND:
      return 'Not Found'
    case ErrorCode.SERVICE_UNAVAILABLE:
      return 'Service Unavailable'
    case ErrorCode.INVALID_REQUEST:
      return 'Invalid Request'
    default:
      return 'Error'
  }
}

function canRetry(errorCode: ErrorCode): boolean {
  // Don't retry on validation or auth errors
  const nonRetryableCodes = [
    ErrorCode.VALIDATION_ERROR,
    ErrorCode.AUTHENTICATION_ERROR,
    ErrorCode.AUTHORIZATION_ERROR,
    ErrorCode.INVALID_REQUEST,
    ErrorCode.RESOURCE_NOT_FOUND
  ]
  
  return !nonRetryableCodes.includes(errorCode)
}