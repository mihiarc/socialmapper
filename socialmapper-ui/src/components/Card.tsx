import { HTMLAttributes, forwardRef, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'bordered' | 'elevated' | 'ghost' | 'gradient'
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  hover?: boolean
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', padding = 'lg', hover = false, ...props }, ref) => {
    const variants = {
      default: [
        'glass',
        'shadow-xl',
        'border border-gray-200/20 dark:border-gray-700/20'
      ].join(' '),
      bordered: [
        'glass',
        'border-2 border-gray-300/50 dark:border-gray-600/50',
        'shadow-lg'
      ].join(' '),
      elevated: [
        'glass',
        'shadow-2xl shadow-gray-900/10 dark:shadow-black/20',
        'border border-white/30 dark:border-gray-700/30'
      ].join(' '),
      ghost: [
        'bg-gray-100/30 dark:bg-gray-800/30',
        'backdrop-blur-sm',
        'border border-gray-200/10 dark:border-gray-700/10'
      ].join(' '),
      gradient: [
        'bg-gradient-to-br from-white/80 via-white/60 to-white/80',
        'dark:from-gray-800/80 dark:via-gray-800/60 dark:to-gray-800/80',
        'backdrop-blur-xl backdrop-saturate-150',
        'border border-white/30 dark:border-gray-700/30',
        'shadow-xl'
      ].join(' ')
    }

    const paddingSizes = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
      xl: 'p-10'
    }

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl transition-all duration-200',
          variants[variant],
          paddingSizes[padding],
          hover && [
            'cursor-pointer',
            'hover:shadow-lg hover:scale-[1.02]',
            'hover:border-primary-300 dark:hover:border-primary-700'
          ],
          className
        )}
        {...props}
      />
    )
  }
)

Card.displayName = 'Card'

export interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  border?: boolean
  sticky?: boolean
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, border = false, sticky = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'px-8 py-6 -m-8 mb-6',
        border && 'border-b border-gray-200 dark:border-gray-700',
        sticky && 'sticky top-0 z-10 bg-white dark:bg-gray-800 rounded-t-xl',
        className
      )}
      {...props}
    />
  )
)

CardHeader.displayName = 'CardHeader'

export interface CardTitleProps extends HTMLAttributes<HTMLHeadingElement> {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  icon?: ReactNode
}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, size = 'lg', icon, children, ...props }, ref) => {
    const sizes = {
      sm: 'text-base',
      md: 'text-lg',
      lg: 'text-xl',
      xl: 'text-2xl'
    }

    return (
      <h3
        ref={ref}
        className={cn(
          'font-semibold text-gray-900 dark:text-gray-100',
          'flex items-center gap-3',
          sizes[size],
          className
        )}
        {...props}
      >
        {icon && <span className="text-primary-600 dark:text-primary-400">{icon}</span>}
        {children}
      </h3>
    )
  }
)

CardTitle.displayName = 'CardTitle'

export interface CardDescriptionProps extends HTMLAttributes<HTMLParagraphElement> {}

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-gray-500 dark:text-gray-400 mt-1', className)}
      {...props}
    />
  )
)

CardDescription.displayName = 'CardDescription'

export interface CardContentProps extends HTMLAttributes<HTMLDivElement> {
  noPadding?: boolean
}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, noPadding = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'text-gray-600 dark:text-gray-300',
        !noPadding && 'space-y-4',
        className
      )}
      {...props}
    />
  )
)

CardContent.displayName = 'CardContent'

export interface CardFooterProps extends HTMLAttributes<HTMLDivElement> {
  border?: boolean
  align?: 'left' | 'center' | 'right' | 'between'
}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, border = false, align = 'right', ...props }, ref) => {
    const alignments = {
      left: 'justify-start',
      center: 'justify-center',
      right: 'justify-end',
      between: 'justify-between'
    }

    return (
      <div
        ref={ref}
        className={cn(
          'px-8 py-6 -m-8 mt-6',
          'flex items-center gap-3',
          alignments[align],
          border && 'border-t border-gray-200 dark:border-gray-700',
          className
        )}
        {...props}
      />
    )
  }
)

CardFooter.displayName = 'CardFooter'