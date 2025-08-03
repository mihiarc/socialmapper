import { useEffect } from 'react';
import { cn } from '../lib/utils';
import { ErrorMessage, ErrorSeverity } from '../hooks/useErrorHandler';

export interface ToastProps {
  message: ErrorMessage;
  onDismiss: (id: string) => void;
}

const severityStyles: Record<ErrorSeverity, string> = {
  info: 'bg-blue-50 text-blue-800 border-blue-200',
  warning: 'bg-amber-50 text-amber-800 border-amber-200',
  error: 'bg-red-50 text-red-800 border-red-200',
  success: 'bg-green-50 text-green-800 border-green-200',
};

const severityIcons: Record<ErrorSeverity, string> = {
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌',
  success: '✅',
};

export function Toast({ message, onDismiss }: ToastProps) {
  useEffect(() => {
    if (message.duration) {
      const timer = setTimeout(() => {
        onDismiss(message.id);
      }, message.duration);
      return () => clearTimeout(timer);
    }
  }, [message.id, message.duration, onDismiss]);

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg transition-all',
        'animate-in slide-in-from-top-2 fade-in duration-300',
        severityStyles[message.severity]
      )}
      role="alert"
    >
      <span className="text-xl" role="img" aria-label={message.severity}>
        {severityIcons[message.severity]}
      </span>
      <div className="flex-1">
        <p className="font-medium">{message.message}</p>
        {message.details && (
          <p className="mt-1 text-sm opacity-90">
            {typeof message.details === 'string' 
              ? message.details 
              : JSON.stringify(message.details)}
          </p>
        )}
      </div>
      <button
        onClick={() => onDismiss(message.id)}
        className="text-current opacity-70 hover:opacity-100 transition-opacity"
        aria-label="Dismiss"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export interface ToastContainerProps {
  messages: ErrorMessage[];
  onDismiss: (id: string) => void;
}

export function ToastContainer({ messages, onDismiss }: ToastContainerProps) {
  if (messages.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
      {messages.map((message) => (
        <Toast key={message.id} message={message} onDismiss={onDismiss} />
      ))}
    </div>
  );
}