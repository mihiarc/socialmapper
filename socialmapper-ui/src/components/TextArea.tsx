import { TextareaHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle } from 'lucide-react'

export interface TextAreaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  label?: string
  error?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'filled' | 'ghost'
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  showCharCount?: boolean
  maxLength?: number
}

const sizeClasses = {
  sm: 'py-1.5 px-3 text-sm',
  md: 'py-2.5 px-4 text-base',
  lg: 'py-3 px-4 text-lg'
}

const variantClasses = {
  default: [
    'bg-white border-2 border-gray-200',
    'hover:border-gray-300',
    'focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20',
    'dark:bg-gray-800 dark:border-gray-700 dark:hover:border-gray-600'
  ].join(' '),
  filled: [
    'bg-gray-50 border-2 border-transparent',
    'hover:bg-gray-100',
    'focus:bg-white focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20',
    'dark:bg-gray-800 dark:hover:bg-gray-700'
  ].join(' '),
  ghost: [
    'bg-transparent border-2 border-transparent',
    'hover:bg-gray-50',
    'focus:bg-gray-50 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20',
    'dark:hover:bg-gray-800 dark:focus:bg-gray-800'
  ].join(' ')
}

const resizeClasses = {
  none: 'resize-none',
  vertical: 'resize-y',
  horizontal: 'resize-x',
  both: 'resize'
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(
  ({ 
    className, 
    label, 
    error, 
    size = 'md',
    variant = 'default',
    resize = 'vertical',
    showCharCount = false,
    maxLength,
    disabled,
    value,
    ...props 
  }, ref) => {
    const charCount = value ? String(value).length : 0

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}
        
        <div className="relative">
          <textarea
            ref={ref}
            value={value}
            disabled={disabled}
            maxLength={maxLength}
            className={cn(
              // Base styles
              'block w-full rounded-lg shadow-sm',
              'transition-all duration-200 ease-in-out',
              'text-gray-900 dark:text-gray-100 placeholder-gray-400',
              'focus:outline-none',
              'min-h-[100px]',
              
              // Size variants
              sizeClasses[size],
              
              // Style variants
              variantClasses[variant],
              
              // Resize control
              resizeClasses[resize],
              
              // States
              'disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
              
              // Bottom padding for char count
              showCharCount && 'pb-8',
              
              className
            )}
            {...props}
          />
          
          {/* Character count */}
          {showCharCount && (
            <div className={cn(
              "absolute bottom-2 right-3 text-xs",
              charCount === maxLength 
                ? "text-red-500 font-medium" 
                : "text-gray-400"
            )}>
              {charCount}{maxLength && `/${maxLength}`}
            </div>
          )}
          
          {/* Error icon */}
          {error && (
            <div className="absolute top-3 right-3 pointer-events-none">
              <AlertCircle className={cn(
                "text-red-500",
                size === 'sm' && "h-4 w-4",
                size === 'md' && "h-5 w-5",
                size === 'lg' && "h-6 w-6"
              )} />
            </div>
          )}
        </div>
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center">
            <AlertCircle className="h-4 w-4 mr-1.5 flex-shrink-0" />
            {error}
          </p>
        )}
      </div>
    )
  }
)

TextArea.displayName = 'TextArea'