import { useEffect } from 'react'
import { cn } from '@/lib/utils'
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  XCircle,
  Info,
  X
} from 'lucide-react'
import { ToastMessage, ToastSeverity } from '@/hooks/useToast'
import { Button } from '../Button'

export interface ToastProps {
  message: ToastMessage
  onDismiss: (id: string) => void
}

const severityStyles: Record<ToastSeverity, string> = {
  info: 'bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-900/20 dark:text-blue-200 dark:border-blue-800',
  warning: 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-900/20 dark:text-amber-200 dark:border-amber-800',
  error: 'bg-red-50 text-red-800 border-red-200 dark:bg-red-900/20 dark:text-red-200 dark:border-red-800',
  success: 'bg-green-50 text-green-800 border-green-200 dark:bg-green-900/20 dark:text-green-200 dark:border-green-800',
}

const severityIcons: Record<ToastSeverity, typeof Info> = {
  info: Info,
  warning: AlertTriangle,
  error: XCircle,
  success: CheckCircle,
}

export function Toast({ message, onDismiss }: ToastProps) {
  useEffect(() => {
    if (message.duration && message.duration > 0) {
      const timer = setTimeout(() => {
        onDismiss(message.id)
      }, message.duration)
      return () => clearTimeout(timer)
    }
  }, [message.id, message.duration, onDismiss])

  const Icon = severityIcons[message.severity]

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-4 rounded-lg border shadow-lg transition-all min-w-[320px] max-w-md',
        'animate-in slide-in-from-top-2 fade-in duration-300',
        severityStyles[message.severity]
      )}
      role="alert"
      aria-live="polite"
    >
      <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
      
      <div className="flex-1 space-y-1">
        <p className="font-medium leading-tight">{message.message}</p>
        
        {message.details && (
          <div className="text-sm opacity-90">
            {typeof message.details === 'string' ? (
              <p>{message.details}</p>
            ) : (
              <pre className="font-mono text-xs mt-2 p-2 bg-black/10 dark:bg-white/10 rounded overflow-x-auto">
                {JSON.stringify(message.details, null, 2)}
              </pre>
            )}
          </div>
        )}
        
        {message.action && (
          <div className="mt-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                message.action!.onClick()
                onDismiss(message.id)
              }}
              className="text-current hover:bg-black/10 dark:hover:bg-white/10"
            >
              {message.action.label}
            </Button>
          </div>
        )}
      </div>
      
      <button
        onClick={() => onDismiss(message.id)}
        className="text-current opacity-70 hover:opacity-100 transition-opacity p-1 hover:bg-black/10 dark:hover:bg-white/10 rounded"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export interface ToastContainerProps {
  messages: ToastMessage[]
  onDismiss: (id: string) => void
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center'
  maxToasts?: number
}

const positionClasses = {
  'top-right': 'top-4 right-4',
  'top-left': 'top-4 left-4',
  'bottom-right': 'bottom-4 right-4',
  'bottom-left': 'bottom-4 left-4',
  'top-center': 'top-4 left-1/2 -translate-x-1/2',
  'bottom-center': 'bottom-4 left-1/2 -translate-x-1/2'
}

export function ToastContainer({ 
  messages, 
  onDismiss,
  position = 'top-right',
  maxToasts = 5
}: ToastContainerProps) {
  if (messages.length === 0) return null

  // Only show the most recent maxToasts messages
  const visibleMessages = messages.slice(-maxToasts)

  return (
    <div 
      className={cn(
        'fixed z-50 space-y-2',
        positionClasses[position]
      )}
      aria-live="polite"
      aria-atomic="false"
    >
      {visibleMessages.map((message) => (
        <Toast key={message.id} message={message} onDismiss={onDismiss} />
      ))}
    </div>
  )
}