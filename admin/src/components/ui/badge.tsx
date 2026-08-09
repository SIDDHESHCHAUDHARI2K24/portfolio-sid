import { type ComponentProps } from 'react'
import { cn } from '@/lib/utils'

function Badge({ className, variant, ...props }: ComponentProps<'span'> & { variant?: 'default' | 'secondary' | 'destructive' | 'outline' }) {
  const variants = {
    default: 'bg-primary text-primary-foreground',
    secondary: 'bg-secondary text-secondary-foreground',
    destructive: 'bg-destructive/10 text-destructive dark:bg-destructive/20',
    outline: 'border border-input bg-background text-foreground',
  }
  return (
    <span
      data-slot="badge"
      className={cn(
        'inline-flex items-center rounded-sm px-1.5 py-0.5 text-xs font-medium',
        variants[variant ?? 'default'],
        className,
      )}
      {...props}
    />
  )
}

export { Badge }
