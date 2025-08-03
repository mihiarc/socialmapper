import { ReactNode, useState, useEffect } from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '../Button'
import { Alert } from '../Alert'

interface AsyncErrorBoundaryProps {
  children: ReactNode
  fallback?: (error: Error, retry: () => void) => ReactNode
  onError?: (error: Error) => void
}

export function AsyncErrorBoundary({ 
  children, 
  fallback, 
  onError 
}: AsyncErrorBoundaryProps) {
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    // Reset error when children change
    setError(null)
  }, [children])

  const handleError = (error: Error) => {
    setError(error)
    onError?.(error)
  }

  const retry = () => {
    setError(null)
  }

  // Provide error handling context to children
  const errorHandler = {
    handleError,
    clearError: retry
  }

  if (error) {
    if (fallback) {
      return <>{fallback(error, retry)}</>
    }

    return (
      <div className="p-4">
        <Alert variant="error" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <div className="ml-2">
            <p className="font-semibold">An error occurred</p>
            <p className="text-sm mt-1">{error.message}</p>
          </div>
        </Alert>
        <Button
          variant="secondary"
          size="sm"
          onClick={retry}
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Try Again
        </Button>
      </div>
    )
  }

  // Clone children and pass error handler
  return (
    <AsyncErrorProvider value={errorHandler}>
      {children}
    </AsyncErrorProvider>
  )
}

// Context for async error handling
import { createContext, useContext } from 'react'

interface AsyncErrorContextValue {
  handleError: (error: Error) => void
  clearError: () => void
}

const AsyncErrorContext = createContext<AsyncErrorContextValue | null>(null)

export function AsyncErrorProvider({ 
  children, 
  value 
}: { 
  children: ReactNode
  value: AsyncErrorContextValue 
}) {
  return (
    <AsyncErrorContext.Provider value={value}>
      {children}
    </AsyncErrorContext.Provider>
  )
}

export function useAsyncError() {
  const context = useContext(AsyncErrorContext)
  if (!context) {
    // Fallback to console.error if not in boundary
    return {
      handleError: (error: Error) => console.error('Async error:', error),
      clearError: () => {}
    }
  }
  return context
}