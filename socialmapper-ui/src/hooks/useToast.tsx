import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { APIError, ErrorCode } from '@/types/api'

export type ToastSeverity = 'info' | 'success' | 'warning' | 'error'

export interface ToastMessage {
  id: string
  message: string
  severity: ToastSeverity
  details?: string | Record<string, any>
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

interface ToastContextValue {
  messages: ToastMessage[]
  addToast: (message: Omit<ToastMessage, 'id'>) => void
  removeToast: (id: string) => void
  clearToasts: () => void
  showError: (error: Error | APIError | string) => void
  showSuccess: (message: string, details?: string) => void
  showWarning: (message: string, details?: string) => void
  showInfo: (message: string, details?: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([])

  const addToast = useCallback((message: Omit<ToastMessage, 'id'>) => {
    const id = uuidv4()
    const newMessage: ToastMessage = {
      id,
      duration: 5000, // Default 5 seconds
      ...message
    }
    
    setMessages(prev => [...prev, newMessage])
  }, [])

  const removeToast = useCallback((id: string) => {
    setMessages(prev => prev.filter(msg => msg.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    setMessages([])
  }, [])

  const showError = useCallback((error: Error | APIError | string) => {
    let message: string
    let details: string | undefined
    let duration = 7000 // Errors show longer
    let action: ToastMessage['action'] | undefined

    if (typeof error === 'string') {
      message = error
    } else if (isAPIError(error)) {
      // Handle API errors with specific messages
      message = getAPIErrorMessage(error)
      details = error.details ? JSON.stringify(error.details, null, 2) : undefined
      
      // Add retry action for certain errors
      if (canRetryError(error.error_code)) {
        action = {
          label: 'Retry',
          onClick: () => window.location.reload()
        }
      }
      
      // Longer duration for rate limit errors
      if (error.error_code === ErrorCode.RATE_LIMIT_EXCEEDED) {
        duration = 15000
      }
    } else {
      message = error.message || 'An unexpected error occurred'
    }

    addToast({
      message,
      severity: 'error',
      details,
      duration,
      action
    })
  }, [addToast])

  const showSuccess = useCallback((message: string, details?: string) => {
    addToast({
      message,
      severity: 'success',
      details,
      duration: 4000
    })
  }, [addToast])

  const showWarning = useCallback((message: string, details?: string) => {
    addToast({
      message,
      severity: 'warning',
      details,
      duration: 6000
    })
  }, [addToast])

  const showInfo = useCallback((message: string, details?: string) => {
    addToast({
      message,
      severity: 'info',
      details,
      duration: 5000
    })
  }, [addToast])

  const value: ToastContextValue = {
    messages,
    addToast,
    removeToast,
    clearToasts,
    showError,
    showSuccess,
    showWarning,
    showInfo
  }

  return (
    <ToastContext.Provider value={value}>
      {children}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider')
  }
  return context
}

// Helper functions
function isAPIError(error: any): error is APIError {
  return error && typeof error === 'object' && 'error_code' in error
}

function getAPIErrorMessage(error: APIError): string {
  const messages: Record<ErrorCode, string> = {
    [ErrorCode.NETWORK_ERROR]: 'Network connection error. Please check your internet connection.',
    [ErrorCode.TIMEOUT_ERROR]: 'Request timed out. Please try again.',
    [ErrorCode.AUTHENTICATION_ERROR]: 'Authentication failed. Please log in again.',
    [ErrorCode.AUTHORIZATION_ERROR]: 'You do not have permission to perform this action.',
    [ErrorCode.RATE_LIMIT_EXCEEDED]: `Rate limit exceeded. Please wait ${error.details?.retry_after_seconds || 60} seconds.`,
    [ErrorCode.VALIDATION_ERROR]: 'Please check your input and try again.',
    [ErrorCode.RESOURCE_NOT_FOUND]: 'The requested resource was not found.',
    [ErrorCode.PROCESSING_ERROR]: 'An error occurred while processing your request.',
    [ErrorCode.SERVICE_UNAVAILABLE]: 'Service temporarily unavailable. Please try again later.',
    [ErrorCode.INVALID_REQUEST]: 'Invalid request. Please check your input.',
    [ErrorCode.INTERNAL_ERROR]: 'An unexpected error occurred. Please try again.',
  }
  
  return messages[error.error_code] || error.message || 'An error occurred'
}

function canRetryError(errorCode: ErrorCode): boolean {
  const retryableCodes = [
    ErrorCode.NETWORK_ERROR,
    ErrorCode.TIMEOUT_ERROR,
    ErrorCode.SERVICE_UNAVAILABLE,
    ErrorCode.PROCESSING_ERROR
  ]
  
  return retryableCodes.includes(errorCode)
}