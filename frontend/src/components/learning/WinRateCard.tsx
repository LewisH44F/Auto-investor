import { Award, TrendingUp, Target, Zap } from 'lucide-react'
import { clsx } from 'clsx'
import { motion } from 'framer-motion'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { ModelPerformance } from '@/types'
import { formatPercent } from '@/utils/formatters'
import { SpinnerOverlay } from '@/components/ui/Spinner'

interface WinRateCardProps {
  performance: ModelPerformance | null
  isLoading?: boolean
}

export default function WinRateCard({ performance, isLoading }: WinRateCardProps) {
  if (isLoading || !performance) {
    return (
      <Card>
        <SpinnerOverlay />
      </Card>
    )
  }

  const winRateColor =
    performance.win_rate >= 65 ? 'text-gain' : performance.win_rate >= 50 ? 'text-warning' : 'text-loss'

  return (
    <Card animate>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Award className="w-4 h-4 text-warning" />
          <CardTitle>Model Performance</CardTitle>
        </div>
      </CardHeader>

      {/* Win Rate Hero */}
      <div className="flex flex-col items-center py-4 mb-4 bg-base/40 rounded-xl border border-white/5">
        <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">Win Rate</div>
        <motion.div
          className={clsx('text-5xl font-black font-mono', winRateColor)}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          {performance.win_rate.toFixed(1)}%
        </motion.div>
        <div className="text-xs text-gray-600 mt-1">
          {performance.total_predictions} total predictions
        </div>

        {/* Win Rate Bar */}
        <div className="w-full px-6 mt-4">
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background:
                  performance.win_rate >= 65 ? '#10b981' : performance.win_rate >= 50 ? '#f59e0b' : '#ef4444',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${performance.win_rate}%` }}
              transition={{ duration: 0.8, delay: 0.2 }}
            />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          {
            icon: TrendingUp,
            label: 'Avg Return',
            value: formatPercent(performance.avg_return),
            color: 'text-gain',
          },
          {
            icon: Target,
            label: 'Avg Confidence',
            value: `${performance.avg_confidence.toFixed(0)}%`,
            color: 'text-brand',
          },
          {
            icon: Zap,
            label: 'Best Signal',
            value: performance.best_signal_type.toUpperCase(),
            color: 'text-warning',
          },
          {
            icon: Award,
            label: 'Sharpe Ratio',
            value: performance.sharpe_ratio?.toFixed(2) ?? 'N/A',
            color: 'text-gain',
          },
        ].map(({ icon: Icon, label, value, color }) => (
          <div
            key={label}
            className="flex items-start gap-2 p-3 bg-base/40 rounded-lg border border-white/5"
          >
            <Icon className="w-3.5 h-3.5 text-gray-600 mt-0.5 flex-shrink-0" />
            <div>
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-0.5">
                {label}
              </div>
              <div className={clsx('text-sm font-mono font-bold', color)}>{value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Additional Stats */}
      {performance.max_drawdown !== undefined && (
        <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-0.5">Max Drawdown</div>
            <div className="text-sm font-mono text-loss font-semibold">
              {performance.max_drawdown.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-0.5">Profit Factor</div>
            <div className="text-sm font-mono text-gain font-semibold">
              {performance.profit_factor?.toFixed(1) ?? 'N/A'}x
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
