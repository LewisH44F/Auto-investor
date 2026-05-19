import { clsx } from 'clsx'

type BadgeVariant =
  | 'default'
  | 'gain'
  | 'loss'
  | 'warning'
  | 'brand'
  | 'outline'
  | 'ghost'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'xs' | 'sm' | 'md'
  className?: string
  dot?: boolean
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-700/60 text-gray-300 border-gray-600/30',
  gain: 'bg-gain/15 text-gain border-gain/30',
  loss: 'bg-loss/15 text-loss border-loss/30',
  warning: 'bg-warning/15 text-warning border-warning/30',
  brand: 'bg-brand/15 text-brand border-brand/30',
  outline: 'bg-transparent text-gray-400 border-gray-600/50',
  ghost: 'bg-white/5 text-gray-300 border-transparent',
}

const sizeClasses = {
  xs: 'text-[10px] px-1.5 py-0.5',
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-2.5 py-1',
}

const dotColors: Record<BadgeVariant, string> = {
  default: 'bg-gray-400',
  gain: 'bg-gain',
  loss: 'bg-loss',
  warning: 'bg-warning',
  brand: 'bg-brand',
  outline: 'bg-gray-400',
  ghost: 'bg-gray-400',
}

export default function Badge({
  children,
  variant = 'default',
  size = 'sm',
  className,
  dot,
}: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-md border font-medium',
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
    >
      {dot && (
        <span
          className={clsx('inline-block w-1.5 h-1.5 rounded-full flex-shrink-0', dotColors[variant])}
        />
      )}
      {children}
    </span>
  )
}

// Specialized badges
export function RiskBadge({ risk }: { risk: string }) {
  const variant: BadgeVariant =
    risk === 'low' ? 'gain' : risk === 'medium' ? 'warning' : 'loss'
  return (
    <Badge variant={variant} size="xs">
      {risk.toUpperCase()} RISK
    </Badge>
  )
}

export function RecommendationTypeBadge({ type }: { type: string }) {
  const variant: BadgeVariant =
    type === 'primary' ? 'gain' : type === 'secondary' ? 'brand' : 'default'
  const label =
    type === 'primary' ? 'PRIMARY' : type === 'secondary' ? 'SECONDARY' : 'WATCHLIST'
  return (
    <Badge variant={variant} size="xs" dot>
      {label}
    </Badge>
  )
}

export function HoldingRecommendationBadge({ rec }: { rec: string }) {
  const map: Record<string, { variant: BadgeVariant; label: string }> = {
    hold: { variant: 'brand', label: 'HOLD' },
    buy_more: { variant: 'gain', label: 'BUY MORE' },
    average_down: { variant: 'warning', label: 'AVG DOWN' },
    sell: { variant: 'loss', label: 'SELL' },
  }
  const config = map[rec] || { variant: 'default' as BadgeVariant, label: rec.toUpperCase() }
  return (
    <Badge variant={config.variant} size="sm" dot>
      {config.label}
    </Badge>
  )
}

export function SignalBadge({ signal }: { signal: string }) {
  const colorMap: Record<string, BadgeVariant> = {
    momentum: 'gain',
    catalyst: 'warning',
    technical: 'brand',
    sentiment: 'brand',
    volume: 'default',
    macro: 'outline',
  }
  return (
    <Badge variant={colorMap[signal] || 'default'} size="xs">
      {signal.toUpperCase()}
    </Badge>
  )
}
