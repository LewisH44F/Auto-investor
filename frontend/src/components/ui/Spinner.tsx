import { clsx } from 'clsx'

interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg'
  className?: string
  color?: 'brand' | 'white' | 'gain' | 'loss'
}

const sizeMap = {
  xs: 'w-3 h-3 border',
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-[3px]',
}

const colorMap = {
  brand: 'border-brand/20 border-t-brand',
  white: 'border-white/20 border-t-white',
  gain: 'border-gain/20 border-t-gain',
  loss: 'border-loss/20 border-t-loss',
}

export default function Spinner({
  size = 'md',
  className,
  color = 'brand',
}: SpinnerProps) {
  return (
    <div
      className={clsx(
        'rounded-full animate-spin',
        sizeMap[size],
        colorMap[color],
        className
      )}
      role="status"
      aria-label="Loading"
    />
  )
}

export function SpinnerOverlay({ message }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12">
      <Spinner size="lg" />
      {message && <p className="text-sm text-gray-500">{message}</p>}
    </div>
  )
}
