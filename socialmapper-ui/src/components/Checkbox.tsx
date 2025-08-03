import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { Check, Minus } from 'lucide-react'

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string
  description?: string
  error?: string
  size?: 'sm' | 'md' | 'lg'
  indeterminate?: boolean
}

const sizeClasses = {
  sm: {
    box: 'h-4 w-4',
    icon: 'h-3 w-3',
    label: 'text-sm',
    description: 'text-xs'
  },
  md: {
    box: 'h-5 w-5',
    icon: 'h-3.5 w-3.5',
    label: 'text-base',
    description: 'text-sm'
  },
  lg: {
    box: 'h-6 w-6',
    icon: 'h-4 w-4',
    label: 'text-lg',
    description: 'text-base'
  }
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ 
    className, 
    label, 
    description,
    error, 
    size = 'md',
    indeterminate = false,
    disabled,
    checked,
    ...props 
  }, ref) => {
    const sizes = sizeClasses[size]

    return (
      <div className="relative">
        <label className={cn(
          "flex items-start gap-3 cursor-pointer",
          disabled && "cursor-not-allowed opacity-50"
        )}>
          <div className="relative flex items-center">
            <input
              ref={ref}
              type="checkbox"
              disabled={disabled}
              checked={checked}
              className="sr-only peer"
              {...props}
            />
            
            <div className={cn(
              // Base styles
              sizes.box,
              "rounded border-2 transition-all duration-200",
              "flex items-center justify-center",
              
              // Unchecked state
              "bg-white border-gray-300",
              "hover:border-gray-400",
              
              // Checked state
              "peer-checked:bg-primary-600 peer-checked:border-primary-600",
              "peer-checked:hover:bg-primary-700 peer-checked:hover:border-primary-700",
              
              // Focus state
              "peer-focus:ring-4 peer-focus:ring-primary-500/25",
              
              // Error state
              error && "border-red-500 peer-checked:bg-red-600 peer-checked:border-red-600",
              
              // Dark mode
              "dark:bg-gray-800 dark:border-gray-600",
              "dark:peer-checked:bg-primary-500 dark:peer-checked:border-primary-500",
              
              className
            )}>
              {/* Check icon */}
              {(checked || indeterminate) && (
                indeterminate ? (
                  <Minus className={cn(sizes.icon, "text-white")} strokeWidth={3} />
                ) : (
                  <Check className={cn(sizes.icon, "text-white")} strokeWidth={3} />
                )
              )}
            </div>
          </div>

          {/* Label and description */}
          {(label || description) && (
            <div className="flex-1">
              {label && (
                <span className={cn(
                  sizes.label,
                  "font-medium text-gray-700 dark:text-gray-300",
                  "select-none"
                )}>
                  {label}
                </span>
              )}
              {description && (
                <p className={cn(
                  sizes.description,
                  "text-gray-500 dark:text-gray-400 mt-0.5",
                  "select-none"
                )}>
                  {description}
                </p>
              )}
            </div>
          )}
        </label>
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 ml-7">
            {error}
          </p>
        )}
      </div>
    )
  }
)

Checkbox.displayName = 'Checkbox'