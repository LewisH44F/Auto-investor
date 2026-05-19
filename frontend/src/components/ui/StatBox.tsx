import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface StatBoxProps {
  label: string
  value: string | number
  delta?: number
  deltaLabel?: string
  prefix?: string
  suffix?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
  valueClassName?: string
}

export default function StatBox({
  label,
  value,
  delta,
  deltaLabel,
  prefix,
  suffix,
  size = 'md',
  className,
  valueClassName,
}: StatBoxProps) {
  const isPositive = delta !== undefined && delta > 0
  const isNegative = delta !== undefined && delta < 0

  const sizeClasses = {
    sm: { label: 'text-xs', value: 'text-lg', delta: 'text-xs' },
    md: { label: 'text-xs', value: 'text-2xl', delta: 'text-sm' },
    lg: { label: 'text-sm', value: 'text-4xl', delta: 'text-base' },
  }

  return (
    <div className={clsx('flex flex-col gap-1', className)}>
      <span className={clsx('text-gray-500 uppercase tracking-wider font-medium', sizeClasses[size].label)}>
        {label}
      </span>
      <div className="flex items-baseline gap-1">
        {prefix && (
          <span className={clsx('text-gray-300 font-mono', sizeClasses[size].delta)}>
            {prefix}
          </span>
        )}
        <span
          className={clsx(
            'font-mono font-semibold text-white',
            sizeClasses[size].value,
            valueClassName
          )}
        >
          {value}
        </span>
        {suffix && (
          <span className={clsx('text-gray-400 font-mono', sizeClasses[size].delta)}>
            {suffix}
          </span>
        )}
      </div>
      {delta !== undefined && (
        <div
          className={clsx(
            'flex items-center gap-1',
            sizeClasses[size].delta,
            isPositive && 'text-gain',
            isNegative && 'text-loss',
            !isPositive && !isNegative && 'text-gray-500'
          )}
        >
          {isPositive ? (
            <TrendingUp className="w-3 h-3" />
          ) : isNegative ? (
            <TrendingDown className="w-3 h-3" />
          ) : (
            <Minus className="w-3 h-3" />
          )}
          <span className="font-mono">
            {delta > 0 ? '+' : ''}
            {delta.toFixed(2)}%
          </span>
          {deltaLabel && <span className="text-gray-600">{deltaLabel}</span>}
        </div>
      )}
    </div>
  )
}
