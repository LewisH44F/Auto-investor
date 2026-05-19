import { clsx } from 'clsx'

interface RecommendationBadgeProps {
  recommendation: string
  size?: 'sm' | 'md' | 'lg'
}

const CONFIG: Record<
  string,
  { label: string; bg: string; text: string; border: string; dot: string }
> = {
  hold: {
    label: 'HOLD',
    bg: 'bg-brand/10',
    text: 'text-brand',
    border: 'border-brand/25',
    dot: 'bg-brand',
  },
  buy_more: {
    label: 'BUY MORE',
    bg: 'bg-gain/10',
    text: 'text-gain',
    border: 'border-gain/25',
    dot: 'bg-gain',
  },
  average_down: {
    label: 'AVG DOWN',
    bg: 'bg-warning/10',
    text: 'text-warning',
    border: 'border-warning/25',
    dot: 'bg-warning',
  },
  sell: {
    label: 'SELL',
    bg: 'bg-loss/10',
    text: 'text-loss',
    border: 'border-loss/25',
    dot: 'bg-loss',
  },
}

export default function RecommendationBadge({
  recommendation,
  size = 'sm',
}: RecommendationBadgeProps) {
  const config = CONFIG[recommendation] || {
    label: recommendation.toUpperCase(),
    bg: 'bg-gray-700/50',
    text: 'text-gray-400',
    border: 'border-gray-600/30',
    dot: 'bg-gray-500',
  }

  const sizeClass =
    size === 'sm'
      ? 'text-[10px] px-2 py-0.5'
      : size === 'md'
      ? 'text-xs px-2.5 py-1'
      : 'text-sm px-3 py-1.5'

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-md border font-bold',
        config.bg,
        config.text,
        config.border,
        sizeClass
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full flex-shrink-0', config.dot)} />
      {config.label}
    </span>
  )
}
