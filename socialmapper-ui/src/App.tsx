import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter as Router } from 'react-router-dom'
import { AppRoutes } from './routes'
import { Layout } from './components/Layout'
import { APIProvider, ErrorProvider } from './contexts'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ConfigErrorBoundary } from './components/ConfigErrorBoundary'
import { ToastContainer } from './components/Toast'
import { useErrorHandler } from './hooks/useErrorHandler'
import { config } from './config'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: config.api.retryAttempts,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
  },
})

function AppContent() {
  const { errors, removeError } = useErrorHandler()
  
  return (
    <>
      <Router>
        <Layout>
          <AppRoutes />
        </Layout>
      </Router>
      <ToastContainer messages={errors} onDismiss={removeError} />
    </>
  )
}

function App() {
  return (
    <ConfigErrorBoundary>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ErrorProvider>
            <APIProvider>
              <AppContent />
            </APIProvider>
          </ErrorProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </ConfigErrorBoundary>
  )
}

export default App