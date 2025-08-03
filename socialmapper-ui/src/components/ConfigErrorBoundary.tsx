import { Component, ReactNode } from 'react';
import { configHealthCheck } from '@/config';
import { Button } from '@/components';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ConfigErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    
    // Check configuration health on initialization
    this.state = {
      hasError: !configHealthCheck.valid,
      error: configHealthCheck.valid ? undefined : new Error(configHealthCheck.errors.join('\n')),
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Configuration error caught:', error, errorInfo);
  }

  handleReset = () => {
    // Clear local storage and reload
    localStorage.clear();
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return <>{this.props.fallback}</>;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-lg">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-red-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              
              <h1 className="mt-4 text-2xl font-bold text-gray-900">
                Configuration Error
              </h1>
              
              <p className="mt-2 text-gray-600">
                There's a problem with the application configuration.
              </p>

              {this.state.error && (
                <div className="mt-4 p-4 bg-red-50 rounded-md text-left">
                  <h3 className="text-sm font-medium text-red-800">
                    Error Details:
                  </h3>
                  <pre className="mt-2 text-xs text-red-700 whitespace-pre-wrap">
                    {this.state.error.message}
                  </pre>
                </div>
              )}

              {configHealthCheck.warnings.length > 0 && (
                <div className="mt-4 p-4 bg-amber-50 rounded-md text-left">
                  <h3 className="text-sm font-medium text-amber-800">
                    Warnings:
                  </h3>
                  <ul className="mt-2 text-xs text-amber-700 list-disc list-inside">
                    {configHealthCheck.warnings.map((warning, index) => (
                      <li key={index}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-6 space-y-3">
                <Button
                  onClick={this.handleReset}
                  variant="primary"
                  className="w-full"
                >
                  Reset Configuration
                </Button>
                
                <Button
                  onClick={() => window.location.href = '/docs/configuration'}
                  variant="outline"
                  className="w-full"
                >
                  View Documentation
                </Button>
              </div>
              
              <p className="mt-4 text-xs text-gray-500">
                If the problem persists, please check your environment variables
                or contact support.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}