import { InputHTMLAttributes, forwardRef, ReactNode, useId } from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle, Search, Mail, Lock, User, Calendar, DollarSign } from 'lucide-react'

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string
  error?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'filled' | 'ghost'
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  iconType?: 'search' | 'email' | 'password' | 'user' | 'date' | 'currency'
}

const sizeClasses = {
  sm: 'py-1.5 text-sm',
  md: 'py-2.5 text-base',
  lg: 'py-3 text-lg'
}

const variantClasses = {
  default: [
    'glass border-2 border-gray-200/50',
    'hover:border-gray-300/70 hover:shadow-lg',
    'focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20 focus:shadow-glow-primary',
    'dark:border-gray-700/50 dark:hover:border-gray-600/70'
  ].join(' '),
  filled: [
    'bg-gray-50/80 dark:bg-gray-800/80 backdrop-blur-sm border-2 border-transparent',
    'hover:bg-gray-100/80 dark:hover:bg-gray-700/80',
    'focus:bg-white/90 dark:focus:bg-gray-900/90 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20',
  ].join(' '),
  ghost: [
    'bg-transparent border-2 border-transparent',
    'hover:bg-gray-50/50 dark:hover:bg-gray-800/50 hover:backdrop-blur-sm',
    'focus:bg-gray-50/70 dark:focus:bg-gray-800/70 focus:border-primary-500 focus:ring-4 focus:ring-primary-500/20',
  ].join(' ')
}

const iconMap = {
  search: Search,
  email: Mail,
  password: Lock,
  user: User,
  date: Calendar,
  currency: DollarSign
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    label, 
    error, 
    size = 'md',
    variant = 'default',
    leftIcon,
    rightIcon,
    iconType,
    disabled,
    id,
    ...props 
  }, ref) => {
    // Generate a unique ID if not provided
    const generatedId = useId()
    const inputId = id || generatedId
    
    // Auto-detect icon based on type or iconType
    const LeftIconComponent = iconType && !leftIcon ? iconMap[iconType] : null
    const hasLeftIcon = leftIcon || LeftIconComponent
    const hasRightIcon = rightIcon || error

    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {/* Left Icon */}
          {hasLeftIcon && (
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              {leftIcon || (
                LeftIconComponent && (
                  <LeftIconComponent className={cn(
                    "text-gray-400",
                    size === 'sm' && "h-4 w-4",
                    size === 'md' && "h-5 w-5",
                    size === 'lg' && "h-6 w-6"
                  )} />
                )
              )}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            className={cn(
              // Base styles
              'block w-full rounded-lg shadow-sm',
              'transition-all duration-200 ease-in-out',
              'text-gray-900 dark:text-gray-100 placeholder-gray-400',
              'focus:outline-none',
              
              // Size variants
              sizeClasses[size],
              
              // Padding adjustments
              hasLeftIcon ? (
                size === 'sm' ? 'pl-9 pr-4' :
                size === 'md' ? 'pl-11 pr-4' :
                'pl-12 pr-4'
              ) : 'px-4',
              
              hasRightIcon && (
                size === 'sm' ? 'pr-9' :
                size === 'md' ? 'pr-11' :
                'pr-12'
              ),
              
              // Style variants
              variantClasses[variant],
              
              // States
              'disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
              
              className
            )}
            {...props}
          />

          {/* Right Icon or Error Icon */}
          {hasRightIcon && (
            <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
              {error ? (
                <AlertCircle className={cn(
                  "text-red-500",
                  size === 'sm' && "h-4 w-4",
                  size === 'md' && "h-5 w-5",
                  size === 'lg' && "h-6 w-6"
                )} />
              ) : rightIcon}
            </div>
          )}
        </div>
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center">
            {error}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'