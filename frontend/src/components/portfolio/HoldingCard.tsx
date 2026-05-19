import { motion } from 'framer-motion'
import { Clock, Trash2 } from 'lucide-react'
import { clsx } from 'clsx'
import { Holding } from '@/types'
import Card from '@/components/ui/Card'
import { HoldingRecommendationBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import { formatCurrency, formatPercent, formatTimeAgo, formatShares } from '@/utils/formatters'
import { getChangeColor } from '@/utils/colors'

interface HoldingCardProps {
  holding: Holding
  onRemove?: (id: string) => void
  delay?: number
}

export default function HoldingCard({ holding, onRemove, delay = 0 }: HoldingCardProps) {
  const isGain = holding.unrealized_pnl >= 0

  const convictionColor =
    holding.conviction_score >= 75
      ? '#10b981'
      : holding.conviction_score >= 55
      ? '#3b82f6'
      : '#f59e0b'

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: delay * 0.08 }}
    >
      <Card
        className={clsx(
          'hover:border-white/10 transition-all duration-200',
          isGain ? 'hover:shadow-glow-green/5' : 'hover:shadow-glow-red/5'
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-black font-mono text-white">{holding.ticker}</span>
              <HoldingRecommendationBadge rec={holding.ai_recommendation} />
            </div>
            {holding.company_name && (
              <div className="text-xs text-gray-600 mt-0.5">{holding.company_name}</div>
            )}
            {holding.sector && (
              <div className="text-[10px] text-gray-700 mt-0.5">{holding.sector}</div>
            )}
          </div>

          {/* P&L Badge */}
          <div
            className={clsx(
              'flex flex-col items-end px-3 py-2 rounded-lg border',
              isGain
                ? 'bg-gain/10 border-gain/20'
                : 'bg-loss/10 border-loss/20'
            )}
          >
            <div
              className={clsx(
                'font-mono text-lg font-bold',
                isGain ? 'text-gain' : 'text-loss'
              )}
            >
              {isGain ? '+' : ''}{formatCurrency(holding.unrealized_pnl)}
            </div>
            <div
              className={clsx(
                'font-mono text-xs font-semibold',
                isGain ? 'text-gain/70' : 'text-loss/70'
              )}
            >
              {formatPercent(holding.unrealized_pnl_pct)}
            </div>
          </div>
        </div>

        {/* Price Info */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Shares</div>
            <div className="font-mono text-sm text-gray-200">{formatShares(holding.shares)}</div>
          </div>
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Avg Cost</div>
            <div className="font-mono text-sm text-gray-200">
              {formatCurrency(holding.purchase_price)}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Current</div>
            <div className={clsx('font-mono text-sm font-semibold', getChangeColor(holding.unrealized_pnl_pct))}>
              {formatCurrency(holding.current_price)}
            </div>
          </div>
        </div>

        {/* Total Value */}
        <div className="flex items-center justify-between mb-4 py-2 border-y border-white/5">
          <span className="text-xs text-gray-600">Total Value</span>
          <span className="font-mono text-sm font-semibold text-gray-200">
            {formatCurrency(holding.current_price * holding.shares)}
          </span>
        </div>

        {/* Conviction Score */}
        <div className="mb-4 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-gray-600 uppercase tracking-wider">
              AI Conviction
            </span>
            <span className="text-xs font-mono font-bold" style={{ color: convictionColor }}>
              {holding.conviction_score}%
            </span>
          </div>
          <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: convictionColor, boxShadow: `0 0 6px ${convictionColor}60` }}
              initial={{ width: 0 }}
              animate={{ width: `${holding.conviction_score}%` }}
              transition={{ duration: 0.7, delay: 0.2 + delay * 0.08 }}
            />
          </div>
        </div>

        {/* AI Reasoning */}
        <div className="bg-base/60 border border-white/5 rounded-lg p-3 mb-4">
          <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">
            {holding.reasoning}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-gray-600">
            <Clock className="w-3 h-3" />
            <span className="text-[10px]">{formatTimeAgo(holding.last_assessed)}</span>
          </div>
          {onRemove && (
            <Button
              variant="ghost"
              size="xs"
              icon={<Trash2 className="w-3.5 h-3.5 text-gray-600 hover:text-loss" />}
              onClick={(e) => {
                e.stopPropagation()
                onRemove(holding.id)
              }}
              className="opacity-0 group-hover:opacity-100 hover:bg-loss/10"
            />
          )}
        </div>
      </Card>
    </motion.div>
  )
}
