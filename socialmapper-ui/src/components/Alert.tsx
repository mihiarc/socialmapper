import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  XCircle,
  Info
} from 'lucide-react'

export interface AlertProps {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info'
  className?: string
  children: ReactNode
  onClose?: () => void
}

const variantStyles = {
  default: 'bg-gray-50 border-gray-200 text-gray-800 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-200',
  success: 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-200',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-800 dark:text-yellow-200',
  error: 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200',
  info: 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-200'
}

const iconMap = {
  default: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  info: AlertCircle
}

export function Alert({ 
  variant = 'default', 
  className = '', 
  children,
  onClose 
}: AlertProps) {
  const Icon = iconMap[variant]
  
  return (
    <div 
      className={cn(
        'relative border rounded-lg p-4 flex items-start',
        variantStyles[variant],
        className
      )}
      role="alert"
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <div className="ml-3 flex-1">
        {children}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="ml-3 inline-flex rounded-md p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          aria-label="Close alert"
        >
          <XCircle className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}