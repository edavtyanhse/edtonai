import { ReactNode, cloneElement, isValidElement } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps {
  children: ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  icon?: ReactNode
  className?: string
  type?: 'button' | 'submit' | 'reset'
}

export default function Button({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  icon,
  className = '',
  type = 'button',
}: ButtonProps) {
  const baseStyles =
    'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary:
      'bg-app-accent text-white hover:bg-app-accent-hover shadow-lg shadow-brand-500/25 border border-transparent focus:ring-app-accent',
    secondary:
      'bg-app-surface text-app-text hover:bg-app-surface-muted border border-app-border hover:border-app-border-strong focus:ring-app-border-strong',
    danger:
      'bg-app-danger-soft text-app-danger hover:bg-app-danger-soft/80 border border-app-danger/30 focus:ring-app-danger',
    ghost:
      'text-app-text-muted hover:text-app-text hover:bg-app-surface-muted focus:ring-app-border-strong',
    outline:
      'bg-transparent border border-app-border text-app-text-muted hover:bg-app-surface-muted hover:text-app-text focus:ring-app-accent',
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : icon && isValidElement(icon) ? (
        cloneElement(icon as React.ReactElement, {
          className: 'w-4 h-4',
        })
      ) : (
        icon
      )}
      {children}
    </button>
  )
}
