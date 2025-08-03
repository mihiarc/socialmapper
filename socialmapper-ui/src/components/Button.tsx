import { ButtonHTMLAttributes, forwardRef, ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  fullWidth?: boolean
  loading?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'primary', 
    size = 'md', 
    fullWidth = false,
    loading = false,
    leftIcon,
    rightIcon,
    children,
    disabled,
    ...props 
  }, ref) => {
    const variants = {
      primary: [
        'bg-gradient-to-r from-primary-500 to-primary-600 text-white',
        'shadow-lg shadow-primary-500/25',
        'hover:shadow-xl hover:shadow-primary-500/30 hover:-translate-y-0.5',
        'active:translate-y-0 active:shadow-lg',
        'focus:ring-4 focus:ring-primary-500/25',
        'dark:from-primary-600 dark:to-primary-700'
      ].join(' '),
      secondary: [
        'bg-gradient-to-r from-secondary-500 to-secondary-600 text-white',
        'shadow-lg shadow-secondary-500/25',
        'hover:shadow-xl hover:shadow-secondary-500/30 hover:-translate-y-0.5',
        'active:translate-y-0 active:shadow-lg',
        'focus:ring-4 focus:ring-secondary-500/25',
        'dark:from-secondary-600 dark:to-secondary-700'
      ].join(' '),
      outline: [
        'glass glass-hover',
        'border-2 border-gray-200/50 dark:border-gray-700/50',
        'text-gray-700 dark:text-gray-300',
        'hover:border-gray-300 dark:hover:border-gray-600',
        'hover:shadow-lg hover:-translate-y-0.5',
        'active:translate-y-0',
        'focus:ring-4 focus:ring-gray-500/25'
      ].join(' '),
      ghost: [
        'text-gray-700 dark:text-gray-300',
        'hover:bg-gray-100/50 dark:hover:bg-gray-800/50',
        'hover:shadow-md hover:-translate-y-0.5',
        'active:translate-y-0 active:bg-gray-200/50 dark:active:bg-gray-700/50',
        'focus:ring-4 focus:ring-gray-500/25'
      ].join(' '),
      danger: [
        'bg-gradient-to-r from-red-500 to-red-600 text-white',
        'shadow-lg shadow-red-500/25',
        'hover:shadow-xl hover:shadow-red-500/30 hover:-translate-y-0.5',
        'active:translate-y-0 active:shadow-lg',
        'focus:ring-4 focus:ring-red-500/25',
        'dark:from-red-600 dark:to-red-700'
      ].join(' '),
      success: [
        'bg-gradient-to-r from-green-500 to-green-600 text-white',
        'shadow-lg shadow-green-500/25',
        'hover:shadow-xl hover:shadow-green-500/30 hover:-translate-y-0.5',
        'active:translate-y-0 active:shadow-lg',
        'focus:ring-4 focus:ring-green-500/25',
        'dark:from-green-600 dark:to-green-700'
      ].join(' ')
    }

    const sizes = {
      xs: 'px-2.5 py-1 text-xs gap-1.5',
      sm: 'px-3 py-1.5 text-sm gap-2',
      md: 'px-4 py-2.5 text-base gap-2',
      lg: 'px-6 py-3 text-lg gap-2.5',
      xl: 'px-8 py-4 text-xl gap-3'
    }

    const iconSizes = {
      xs: 'h-3 w-3',
      sm: 'h-4 w-4',
      md: 'h-5 w-5',
      lg: 'h-6 w-6',
      xl: 'h-7 w-7'
    }

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center font-medium',
          'rounded-lg transition-all duration-200',
          'focus:outline-none',
          
          // States
          'disabled:cursor-not-allowed disabled:opacity-50',
          'disabled:shadow-none disabled:hover:shadow-none',
          
          // Variants & sizes
          variants[variant],
          sizes[size],
          
          // Full width
          fullWidth && 'w-full',
          
          className
        )}
        {...props}
      >
        {/* Loading spinner or left icon */}
        {loading ? (
          <Loader2 className={cn('animate-spin', iconSizes[size])} />
        ) : leftIcon && (
          <span className={cn(iconSizes[size])}>
            {leftIcon}
          </span>
        )}
        
        {/* Button content */}
        {children && <span>{children}</span>}
        
        {/* Right icon */}
        {rightIcon && !loading && (
          <span className={cn(iconSizes[size])}>
            {rightIcon}
          </span>
        )}
      </button>
    )
  }
)

Button.displayName = 'Button'