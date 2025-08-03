import { SelectHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: SelectOption[]
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, placeholder, disabled, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            disabled={disabled}
            className={cn(
              // Base styles
              'block w-full appearance-none cursor-pointer',
              'rounded-lg border-2 glass',
              'px-4 py-2.5 pr-10',
              'text-gray-900 dark:text-gray-100',
              'shadow-lg transition-all duration-200',
              
              // Border and focus styles
              'border-gray-200/50 dark:border-gray-700/50',
              'hover:border-gray-300/70 dark:hover:border-gray-600/70 hover:shadow-xl',
              'focus:border-primary-500 focus:outline-none focus:ring-4 focus:ring-primary-500/20 focus:shadow-glow-primary',
              
              // Disabled state
              'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-gray-900',
              
              // Error state
              error && 'border-red-500 hover:border-red-600 focus:border-red-500 focus:ring-red-500/20',
              
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled className="text-gray-400">
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option 
                key={option.value} 
                value={option.value}
                className="text-gray-900 dark:text-gray-100"
              >
                {option.label}
              </option>
            ))}
          </select>
          
          {/* Custom dropdown icon */}
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
            <ChevronDown 
              className={cn(
                "h-5 w-5 text-gray-400 transition-transform duration-200",
                !disabled && "group-hover:text-gray-600"
              )} 
            />
          </div>
        </div>
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center">
            <svg className="w-4 h-4 mr-1.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'