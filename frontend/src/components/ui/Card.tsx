import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  animate?: boolean
  glass?: boolean
  noPadding?: boolean
  glow?: 'blue' | 'green' | 'red' | 'amber' | null
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, animate = false, glass = false, noPadding = false, glow, ...props }, ref) => {
    const classes = clsx(
      'bg-surface border border-white/5 rounded-xl shadow-card',
      !noPadding && 'p-4',
      glass && 'backdrop-blur-sm bg-glass',
      glow === 'blue' && 'shadow-glow-blue border-brand/20',
      glow === 'green' && 'shadow-glow-green border-gain/20',
      glow === 'red' && 'shadow-glow-red border-loss/20',
      glow === 'amber' && 'border-warning/20',
      className
    )

    if (animate) {
      return (
        <motion.div
          ref={ref}
          className={classes}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          {...(props as React.ComponentProps<typeof motion.div>)}
        >
          {children}
        </motion.div>
      )
    }

    return (
      <div ref={ref} className={classes} {...props}>
        {children}
      </div>
    )
  }
)

Card.displayName = 'Card'

export const CardHeader = ({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={clsx('flex items-center justify-between mb-4', className)} {...props}>
    {children}
  </div>
)

export const CardTitle = ({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3
    className={clsx('text-sm font-semibold text-gray-400 uppercase tracking-wider', className)}
    {...props}
  >
    {children}
  </h3>
)

export default Card
