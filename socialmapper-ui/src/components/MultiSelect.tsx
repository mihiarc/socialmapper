import { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { Check, ChevronDown, X } from 'lucide-react'

export interface MultiSelectOption {
  value: string
  label: string
  description?: string
}

export interface MultiSelectProps {
  options: MultiSelectOption[]
  value: string[]
  onChange: (values: string[]) => void
  label?: string
  placeholder?: string
  error?: string
  maxHeight?: number
  disabled?: boolean
  className?: string
}

export function MultiSelect({
  options,
  value,
  onChange,
  label,
  placeholder = 'Select options...',
  error,
  maxHeight = 300,
  disabled,
  className
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    option.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const toggleOption = (optionValue: string) => {
    if (value.includes(optionValue)) {
      onChange(value.filter(v => v !== optionValue))
    } else {
      onChange([...value, optionValue])
    }
  }

  const clearAll = () => {
    onChange([])
    setSearchTerm('')
  }

  const selectedLabels = value
    .map(v => options.find(opt => opt.value === v)?.label)
    .filter(Boolean)

  return (
    <div className={cn("w-full", className)} ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          {label}
        </label>
      )}
      
      <div className="relative">
        {/* Main button */}
        <button
          type="button"
          disabled={disabled}
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            // Base styles
            'w-full flex items-center justify-between',
            'rounded-lg border-2 bg-white dark:bg-gray-800',
            'px-4 py-2.5 min-h-[44px]',
            'text-left transition-all duration-200',
            
            // Border and focus styles
            'border-gray-200 dark:border-gray-700',
            'hover:border-gray-300 dark:hover:border-gray-600',
            'focus:border-primary-500 focus:outline-none focus:ring-4 focus:ring-primary-500/20',
            
            // States
            isOpen && 'border-primary-500 ring-4 ring-primary-500/20',
            disabled && 'cursor-not-allowed opacity-50 bg-gray-50 dark:bg-gray-900',
            error && 'border-red-500 hover:border-red-600 focus:border-red-500 focus:ring-red-500/20'
          )}
        >
          <span className="flex-1 truncate">
            {value.length === 0 ? (
              <span className="text-gray-400">{placeholder}</span>
            ) : (
              <span className="text-gray-900 dark:text-gray-100">
                {selectedLabels.length <= 2 
                  ? selectedLabels.join(', ')
                  : `${selectedLabels.slice(0, 2).join(', ')} +${selectedLabels.length - 2} more`
                }
              </span>
            )}
          </span>
          
          <div className="flex items-center ml-2 space-x-1">
            {value.length > 0 && !disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  clearAll()
                }}
                className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              >
                <X className="h-4 w-4 text-gray-400" />
              </button>
            )}
            <ChevronDown className={cn(
              "h-5 w-5 text-gray-400 transition-transform duration-200",
              isOpen && "transform rotate-180"
            )} />
          </div>
        </button>

        {/* Dropdown */}
        {isOpen && !disabled && (
          <div className={cn(
            "absolute z-50 mt-2 w-full",
            "bg-white dark:bg-gray-800",
            "border-2 border-gray-200 dark:border-gray-700",
            "rounded-lg shadow-lg",
            "animate-in fade-in-0 zoom-in-95 duration-200"
          )}>
            {/* Search input */}
            <div className="p-2 border-b border-gray-200 dark:border-gray-700">
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search options..."
                className={cn(
                  "w-full px-3 py-2 text-sm",
                  "bg-gray-50 dark:bg-gray-900",
                  "border border-gray-200 dark:border-gray-700",
                  "rounded-md",
                  "focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500",
                  "placeholder-gray-400"
                )}
              />
            </div>

            {/* Options list */}
            <div 
              className="overflow-auto" 
              style={{ maxHeight: `${maxHeight}px` }}
            >
              {filteredOptions.length === 0 ? (
                <div className="px-4 py-3 text-sm text-gray-500 text-center">
                  No options found
                </div>
              ) : (
                filteredOptions.map((option) => {
                  const isSelected = value.includes(option.value)
                  
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => toggleOption(option.value)}
                      className={cn(
                        "w-full flex items-start px-4 py-3",
                        "hover:bg-gray-50 dark:hover:bg-gray-700",
                        "transition-colors duration-150",
                        "group"
                      )}
                    >
                      <div className={cn(
                        "flex-shrink-0 w-5 h-5 mt-0.5 mr-3",
                        "border-2 rounded",
                        "transition-all duration-200",
                        isSelected
                          ? "bg-primary-500 border-primary-500"
                          : "border-gray-300 dark:border-gray-600 group-hover:border-gray-400"
                      )}>
                        {isSelected && (
                          <Check className="w-3 h-3 text-white m-auto" />
                        )}
                      </div>
                      
                      <div className="flex-1 text-left">
                        <div className={cn(
                          "text-sm font-medium",
                          isSelected 
                            ? "text-gray-900 dark:text-gray-100" 
                            : "text-gray-700 dark:text-gray-300"
                        )}>
                          {option.label}
                        </div>
                        {option.description && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {option.description}
                          </div>
                        )}
                      </div>
                    </button>
                  )
                })
              )}
            </div>

            {/* Footer with selection count */}
            <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{value.length} selected</span>
                <button
                  type="button"
                  onClick={() => {
                    onChange(options.map(opt => opt.value))
                  }}
                  className="hover:text-primary-600 transition-colors"
                >
                  Select all
                </button>
              </div>
            </div>
          </div>
        )}
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