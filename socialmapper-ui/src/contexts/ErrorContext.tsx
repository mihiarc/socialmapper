import { createContext, useContext, ReactNode } from 'react';
import { useErrorHandler, UseErrorHandlerOptions } from '../hooks/useErrorHandler';
import { ToastContainer } from '../components/Toast';

interface ErrorContextValue {
  addError: ReturnType<typeof useErrorHandler>['addError'];
  removeError: ReturnType<typeof useErrorHandler>['removeError'];
  clearErrors: ReturnType<typeof useErrorHandler>['clearErrors'];
  handleAPIError: ReturnType<typeof useErrorHandler>['handleAPIError'];
  handleError: ReturnType<typeof useErrorHandler>['handleError'];
  showSuccess: ReturnType<typeof useErrorHandler>['showSuccess'];
  showInfo: ReturnType<typeof useErrorHandler>['showInfo'];
  showWarning: ReturnType<typeof useErrorHandler>['showWarning'];
  hasErrors: ReturnType<typeof useErrorHandler>['hasErrors'];
}

const ErrorContext = createContext<ErrorContextValue | undefined>(undefined);

export interface ErrorProviderProps {
  children: ReactNode;
  options?: UseErrorHandlerOptions;
}

export function ErrorProvider({ children, options }: ErrorProviderProps) {
  const errorHandler = useErrorHandler(options);

  const contextValue: ErrorContextValue = {
    addError: errorHandler.addError,
    removeError: errorHandler.removeError,
    clearErrors: errorHandler.clearErrors,
    handleAPIError: errorHandler.handleAPIError,
    handleError: errorHandler.handleError,
    showSuccess: errorHandler.showSuccess,
    showInfo: errorHandler.showInfo,
    showWarning: errorHandler.showWarning,
    hasErrors: errorHandler.hasErrors,
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
      <ToastContainer 
        messages={errorHandler.errors} 
        onDismiss={errorHandler.removeError} 
      />
    </ErrorContext.Provider>
  );
}

export function useError() {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider');
  }
  return context;
}