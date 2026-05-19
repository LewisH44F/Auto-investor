import { TrendingUp, TrendingDown, DollarSign, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { formatCurrency, formatPercent } from '@/utils/formatters'
import { getChangeColor } from '@/utils/colors'
import { PortfolioStats } from '@/types'
import { SpinnerOverlay } from '@/components/ui/Spinner'

interface PortfolioSummaryProps {
  stats: PortfolioStats | null
  isLoading?: boolean
  onRefresh?: () => void
}

export default function PortfolioSummary({ stats, isLoading, onRefresh }: PortfolioSummaryProps) {
  if (isLoading || !stats) {
    return (
      <Card>
        <SpinnerOverlay message="Loading portfolio..." />
      </Card>
    )
  }

  const pnlPositive = stats.total_unrealized_pnl >= 0
  const dayPositive = stats.day_change >= 0

  return (
    <Card animate>
      <CardHeader>
        <div className="flex items-center gap-2">
          <DollarSign className="w-4 h-4 text-brand" />
          <CardTitle>Portfolio Summary</CardTitle>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg text-gray-600 hover:text-gray-300 hover:bg-white/5 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        )}
      </CardHeader>

      {/* Main Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Value */}
        <div className="lg:col-span-2 bg-base/40 rounded-xl p-4 border border-white/5">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            Total Portfolio Value
          </div>
          <div className="text-3xl font-black font-mono text-white mb-1">
            {formatCurrency(stats.total_value)}
          </div>
          <div className={clsx('flex items-center gap-1.5 text-sm font-mono', getChangeColor(stats.day_change_pct))}>
            {dayPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>
              {dayPositive ? '+' : ''}{formatCurrency(stats.day_change)} ({formatPercent(stats.day_change_pct)}) today
            </span>
          </div>
        </div>

        {/* Unrealized P&L */}
        <div
          className={clsx(
            'rounded-xl p-4 border',
            pnlPositive ? 'bg-gain/8 border-gain/15' : 'bg-loss/8 border-loss/15'
          )}
        >
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            Unrealized P&L
          </div>
          <div className={clsx('text-2xl font-black font-mono', pnlPositive ? 'text-gain' : 'text-loss')}>
            {pnlPositive ? '+' : ''}{formatCurrency(stats.total_unrealized_pnl)}
          </div>
          <div className={clsx('text-xs font-mono mt-1', pnlPositive ? 'text-gain/70' : 'text-loss/70')}>
            {formatPercent(stats.total_unrealized_pnl_pct)} return
          </div>
        </div>

        {/* Win Rate */}
        <div className="bg-brand/8 border border-brand/15 rounded-xl p-4">
          <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
            Win Rate
          </div>
          <div className="text-2xl font-black font-mono text-brand">
            {stats.win_rate.toFixed(1)}%
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {stats.total_positions} active positions
          </div>
        </div>
      </div>

      {/* Secondary stats */}
      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-white/5">
        <div>
          <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
            Total Invested
          </div>
          <div className="font-mono text-sm text-gray-300">
            {formatCurrency(stats.total_invested)}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
            Cash Available
          </div>
          <div className="font-mono text-sm text-gain">
            {formatCurrency(stats.cash_available)}
          </div>
        </div>
        <div>
          <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
            Positions
          </div>
          <div className="font-mono text-sm text-gray-300">{stats.total_positions}</div>
        </div>
      </div>
    </Card>
  )
}
