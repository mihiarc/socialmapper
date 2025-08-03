import { Component, ReactNode, ErrorInfo } from 'react'
import { AlertTriangle, RefreshCw, Home, FileText } from 'lucide-react'
import { Button } from '../Button'
import { Card, CardContent } from '../Card'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
  showDetails: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      showDetails: false 
    }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    
    this.setState({ errorInfo })
    
    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
    
    // Log to error reporting service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error reporting service like Sentry
      console.error('Error details for reporting:', {
        error: error.toString(),
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent
      })
    }
  }

  handleReset = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      showDetails: false 
    })
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  toggleDetails = () => {
    this.setState(prev => ({ showDetails: !prev.showDetails }))
  }

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return <>{this.props.fallback}</>
      }

      const { error, errorInfo, showDetails } = this.state
      const isDevelopment = process.env.NODE_ENV === 'development'

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
          <Card variant="elevated" className="max-w-2xl w-full">
            <CardContent className="p-8">
              {/* Error Icon and Title */}
              <div className="flex items-center justify-center mb-6">
                <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-full">
                  <AlertTriangle className="h-12 w-12 text-red-600 dark:text-red-400" />
                </div>
              </div>

              <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-2">
                Oops! Something went wrong
              </h1>

              <p className="text-center text-gray-600 dark:text-gray-400 mb-8">
                We encountered an unexpected error. Don't worry, your data is safe.
              </p>

              {/* Error Message */}
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
                <p className="text-sm font-mono text-red-800 dark:text-red-300">
                  {error?.message || 'An unexpected error occurred'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 mb-6">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={this.handleReset}
                  className="flex-1"
                  leftIcon={<RefreshCw className="h-4 w-4" />}
                >
                  Try Again
                </Button>
                <Button
                  variant="secondary"
                  size="lg"
                  onClick={this.handleReload}
                  className="flex-1"
                >
                  Reload Page
                </Button>
                <Button
                  variant="ghost"
                  size="lg"
                  onClick={this.handleGoHome}
                  className="flex-1"
                  leftIcon={<Home className="h-4 w-4" />}
                >
                  Go Home
                </Button>
              </div>

              {/* Show Details Toggle (Development Only) */}
              {(isDevelopment || this.props.showDetails) && (
                <div className="text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={this.toggleDetails}
                    leftIcon={<FileText className="h-4 w-4" />}
                  >
                    {showDetails ? 'Hide' : 'Show'} Error Details
                  </Button>
                </div>
              )}

              {/* Error Details */}
              {showDetails && (isDevelopment || this.props.showDetails) && (
                <div className="mt-6 space-y-4">
                  {/* Stack Trace */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Stack Trace:
                    </h3>
                    <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto text-xs text-gray-800 dark:text-gray-200">
                      {error?.stack}
                    </pre>
                  </div>

                  {/* Component Stack */}
                  {errorInfo?.componentStack && (
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        Component Stack:
                      </h3>
                      <pre className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-x-auto text-xs text-gray-800 dark:text-gray-200">
                        {errorInfo.componentStack}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Help Text */}
              <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-center text-gray-500 dark:text-gray-400">
                  If this problem persists, please{' '}
                  <a
                    href="https://github.com/socialmapper/socialmapper/issues"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 underline"
                  >
                    report an issue
                  </a>{' '}
                  or contact support.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}