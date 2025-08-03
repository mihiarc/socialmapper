import { InputHTMLAttributes, forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface RadioOption {
  value: string
  label: string
  description?: string
  disabled?: boolean
}

export interface RadioGroupProps {
  name: string
  value?: string
  onChange?: (value: string) => void
  options: RadioOption[]
  label?: string
  error?: string
  size?: 'sm' | 'md' | 'lg'
  orientation?: 'horizontal' | 'vertical'
  disabled?: boolean
}

export interface RadioProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
}

const sizeClasses = {
  sm: {
    box: 'h-4 w-4',
    dot: 'h-2 w-2',
    label: 'text-sm',
    description: 'text-xs',
    gap: 'gap-2'
  },
  md: {
    box: 'h-5 w-5',
    dot: 'h-2.5 w-2.5',
    label: 'text-base',
    description: 'text-sm',
    gap: 'gap-3'
  },
  lg: {
    box: 'h-6 w-6',
    dot: 'h-3 w-3',
    label: 'text-lg',
    description: 'text-base',
    gap: 'gap-3'
  }
}

export const Radio = forwardRef<HTMLInputElement, RadioProps>(
  ({ 
    className, 
    label, 
    description,
    size = 'md',
    disabled,
    ...props 
  }, ref) => {
    const sizes = sizeClasses[size]

    return (
      <label className={cn(
        "flex items-start cursor-pointer",
        sizes.gap,
        disabled && "cursor-not-allowed opacity-50"
      )}>
        <div className="relative flex items-center">
          <input
            ref={ref}
            type="radio"
            disabled={disabled}
            className="sr-only peer"
            {...props}
          />
          
          <div className={cn(
            // Base styles
            sizes.box,
            "rounded-full border-2 transition-all duration-200",
            "flex items-center justify-center",
            
            // Unchecked state
            "bg-white border-gray-300",
            "hover:border-gray-400",
            
            // Checked state
            "peer-checked:border-primary-600",
            "peer-checked:hover:border-primary-700",
            
            // Focus state
            "peer-focus:ring-4 peer-focus:ring-primary-500/25",
            
            // Dark mode
            "dark:bg-gray-800 dark:border-gray-600",
            "dark:peer-checked:border-primary-500",
            
            className
          )}>
            {/* Radio dot */}
            <div className={cn(
              sizes.dot,
              "rounded-full bg-primary-600",
              "scale-0 transition-transform duration-200",
              "peer-checked:scale-100",
              "dark:bg-primary-500"
            )} />
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
    )
  }
)

Radio.displayName = 'Radio'

export function RadioGroup({
  name,
  value,
  onChange,
  options,
  label,
  error,
  size = 'md',
  orientation = 'vertical',
  disabled
}: RadioGroupProps) {
  return (
    <fieldset className="w-full">
      {label && (
        <legend className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </legend>
      )}
      
      <div className={cn(
        "flex",
        orientation === 'vertical' ? 'flex-col space-y-3' : 'flex-row flex-wrap gap-6'
      )}>
        {options.map((option) => (
          <Radio
            key={option.value}
            name={name}
            value={option.value}
            checked={value === option.value}
            onChange={() => onChange?.(option.value)}
            label={option.label}
            description={option.description}
            disabled={disabled || option.disabled}
            size={size}
          />
        ))}
      </div>
      
      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </fieldset>
  )
}