import { clsx } from 'clsx'
import { Activity, TrendingUp, TrendingDown } from 'lucide-react'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { useMarketOverview } from '@/hooks/useMarketData'
import { getChangeColor, getMarketConditionColor, getSectorColor } from '@/utils/colors'
import { SpinnerOverlay } from '@/components/ui/Spinner'

function VixGauge({ vix }: { vix: number }) {
  const max = 50
  const pct = Math.min((vix / max) * 100, 100)
  const color =
    vix > 30 ? '#ef4444' : vix > 20 ? '#f59e0b' : vix > 15 ? '#3b82f6' : '#10b981'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider">Fear Index (VIX)</span>
        <span className={clsx('font-mono text-sm font-bold', vix > 25 ? 'text-loss' : vix > 18 ? 'text-warning' : 'text-gain')}>
          {vix.toFixed(1)}
        </span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}60` }}
        />
      </div>
      <div className="flex justify-between text-[9px] text-gray-700">
        <span>FEARLESS</span>
        <span>NEUTRAL</span>
        <span>FEAR</span>
        <span>PANIC</span>
      </div>
    </div>
  )
}

interface IndexDisplayProps {
  label: string
  value: number
  level?: number
}

function IndexDisplay({ label, value, level }: IndexDisplayProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] text-gray-600 uppercase tracking-wider">{label}</span>
      <div className="flex items-center gap-1.5">
        {value >= 0 ? (
          <TrendingUp className="w-3.5 h-3.5 text-gain" />
        ) : (
          <TrendingDown className="w-3.5 h-3.5 text-loss" />
        )}
        <span className={clsx('font-mono text-base font-bold', getChangeColor(value))}>
          {value >= 0 ? '+' : ''}{value.toFixed(2)}%
        </span>
      </div>
      {level && (
        <span className="text-[10px] font-mono text-gray-600">
          {level.toLocaleString(undefined, { minimumFractionDigits: 2 })}
        </span>
      )}
    </div>
  )
}

export default function MarketOverview() {
  const { data: market, isLoading } = useMarketOverview()

  if (isLoading || !market) {
    return (
      <Card>
        <SpinnerOverlay message="Loading market data..." />
      </Card>
    )
  }

  const conditionColor = getMarketConditionColor(market.market_condition)

  return (
    <Card animate>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand" />
          <CardTitle>Market Overview</CardTitle>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="default"
            size="xs"
            className={clsx('border', conditionColor)}
            dot
          >
            {market.market_condition}
          </Badge>
        </div>
      </CardHeader>

      <div className="space-y-4">
        {/* Index Row */}
        <div className="grid grid-cols-3 gap-4 pb-4 border-b border-white/5">
          <IndexDisplay label="NASDAQ" value={market.nasdaq_change_pct} />
          <IndexDisplay label="S&P 500" value={market.spy_change_pct} />
          <IndexDisplay label="QQQ" value={market.qqq_change_pct} />
        </div>

        {/* VIX Gauge */}
        <div className="pb-4 border-b border-white/5">
          <VixGauge vix={market.vix} />
        </div>

        {/* Sector Heatmap */}
        <div>
          <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">
            Sector Performance
          </div>
          <div className="grid grid-cols-6 gap-1">
            {market.trending_sectors.map((sector) => (
              <div
                key={sector.ticker}
                className="relative rounded p-1.5 flex flex-col items-center text-center overflow-hidden cursor-default"
                style={{
                  background: getSectorColor(sector.change_pct),
                  border: `1px solid ${sector.change_pct > 0 ? 'rgba(16,185,129,0.2)' : sector.change_pct < 0 ? 'rgba(239,68,68,0.2)' : 'rgba(255,255,255,0.05)'}`,
                }}
              >
                <span className="text-[9px] font-bold text-white/90 font-mono">
                  {sector.ticker}
                </span>
                <span
                  className={clsx(
                    'text-[9px] font-mono font-semibold',
                    getChangeColor(sector.change_pct)
                  )}
                >
                  {sector.change_pct >= 0 ? '+' : ''}{sector.change_pct.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Card>
  )
}
