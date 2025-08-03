import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  variant?: 'default' | 'dots' | 'pulse'
}

export function Spinner({ size = 'md', className, variant = 'default' }: SpinnerProps) {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16'
  }

  if (variant === 'dots') {
    const dotSizes = {
      sm: 'w-1.5 h-1.5',
      md: 'w-2 h-2',
      lg: 'w-2.5 h-2.5',
      xl: 'w-3 h-3'
    }

    return (
      <div className={cn('flex space-x-1.5', className)} role="status" aria-label="Loading">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className={cn(
              'rounded-full bg-gradient-to-r from-primary-400 to-primary-600 animate-pulse',
              dotSizes[size]
            )}
            style={{ animationDelay: `${i * 150}ms` }}
          />
        ))}
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  if (variant === 'pulse') {
    return (
      <div className={cn('relative', sizes[size], className)} role="status" aria-label="Loading">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-primary-400 to-primary-600 opacity-75 animate-ping" />
        <div className="rounded-full bg-gradient-to-r from-primary-400 to-primary-600 h-full w-full" />
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full',
        'border-2 border-gray-200 dark:border-gray-700',
        'border-t-transparent border-l-transparent',
        'bg-gradient-to-br from-primary-400 to-primary-600',
        sizes[size],
        className
      )}
      role="status"
      aria-label="Loading"
      style={{
        maskImage: 'radial-gradient(circle, transparent 35%, black 35%)',
        WebkitMaskImage: 'radial-gradient(circle, transparent 35%, black 35%)'
      }}
    >
      <span className="sr-only">Loading...</span>
    </div>
  )
}