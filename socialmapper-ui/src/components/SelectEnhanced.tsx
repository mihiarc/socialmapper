import { SelectHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  icon?: React.ReactNode
  description?: string
}

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  label?: string
  error?: string
  options: SelectOption[]
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'filled' | 'ghost'
}

const sizeClasses = {
  sm: 'py-1.5 px-3 text-sm',
  md: 'py-2 px-4 text-base',
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

export const SelectEnhanced = forwardRef<HTMLSelectElement, SelectProps>(
  ({ 
    className, 
    label, 
    error, 
    options, 
    placeholder,
    size = 'md',
    variant = 'default',
    disabled,
    ...props 
  }, ref) => {
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
              'block w-full rounded-lg shadow-sm appearance-none cursor-pointer',
              'transition-all duration-200 ease-in-out',
              'text-gray-900 dark:text-gray-100',
              
              // Size variants
              sizeClasses[size],
              
              // Style variants
              variantClasses[variant],
              
              // States
              'disabled:cursor-not-allowed disabled:opacity-50',
              error && 'border-red-500 focus:border-red-500 focus:ring-red-500/20',
              
              // Right padding for icon
              size === 'sm' && 'pr-8',
              size === 'md' && 'pr-10',
              size === 'lg' && 'pr-12',
              
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
          <div className={cn(
            "absolute inset-y-0 right-0 flex items-center pointer-events-none",
            size === 'sm' && 'pr-2',
            size === 'md' && 'pr-3',
            size === 'lg' && 'pr-3'
          )}>
            <ChevronDown className={cn(
              "text-gray-400 transition-colors",
              size === 'sm' && 'h-4 w-4',
              size === 'md' && 'h-5 w-5',
              size === 'lg' && 'h-6 w-6',
              !disabled && "group-hover:text-gray-600"
            )} />
          </div>
        </div>
        
        {error && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center">
            <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            {error}
          </p>
        )}
      </div>
    )
  }
)

SelectEnhanced.displayName = 'SelectEnhanced'

// Export a styled version for travel modes with icons
export const TravelModeSelect = forwardRef<HTMLSelectElement, Omit<SelectProps, 'options'>>(
  (props, ref) => {
    const travelModeOptions: SelectOption[] = [
      { value: 'walk', label: '🚶 Walking' },
      { value: 'bike', label: '🚴 Biking' },
      { value: 'drive', label: '🚗 Driving' },
      { value: 'transit', label: '🚌 Transit' }
    ]

    return (
      <SelectEnhanced
        ref={ref}
        options={travelModeOptions}
        placeholder="Select travel mode"
        {...props}
      />
    )
  }
)

TravelModeSelect.displayName = 'TravelModeSelect'