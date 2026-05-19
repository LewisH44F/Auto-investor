import { ArrowUpRight, ArrowDownRight, Target, Clock, TrendingUp, ChevronRight } from 'lucide-react'
import { clsx } from 'clsx'
import { Prediction } from '@/types'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Badge, { RiskBadge, SignalBadge } from '@/components/ui/Badge'
import ConvictionMeter from './ConvictionMeter'
import { formatCurrency, formatPercent } from '@/utils/formatters'
import NoTradeDay from './NoTradeDay'

interface BestTradeOfDayProps {
  prediction: Prediction | null
  isLoading?: boolean
}

export default function BestTradeOfDay({ prediction, isLoading }: BestTradeOfDayProps) {
  if (isLoading) {
    return (
      <Card className="animate-pulse">
        <div className="h-64 bg-white/5 rounded-lg" />
      </Card>
    )
  }

  if (!prediction) {
    return <NoTradeDay />
  }

  const riskReward =
    prediction.profit_target_1 > 0 && prediction.entry_zone_high > 0
      ? (
          (prediction.profit_target_1 - prediction.entry_zone_high) /
          (prediction.entry_zone_high - prediction.stop_loss)
        ).toFixed(1)
      : 'N/A'

  return (
    <Card animate className="relative overflow-hidden">
      {/* Background glow */}
      <div
        className="absolute inset-0 opacity-5 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse at top left, #3b82f6 0%, transparent 60%)`,
        }}
      />

      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-brand animate-pulse" />
          <CardTitle>Best Trade for Tomorrow</CardTitle>
        </div>
        <Badge variant="gain" dot size="xs">LIVE ANALYSIS</Badge>
      </CardHeader>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left: Meter + Ticker */}
        <div className="flex flex-col items-center gap-4 lg:w-52 flex-shrink-0">
          <ConvictionMeter score={prediction.confidence_score} size="lg" animated />

          <div className="text-center">
            <div className="text-5xl font-black font-mono text-white tracking-tighter">
              {prediction.ticker}
            </div>
            {prediction.company_name && (
              <div className="text-xs text-gray-500 mt-1 truncate max-w-[160px]">
                {prediction.company_name}
              </div>
            )}
            <div className="flex items-center justify-center gap-2 mt-3">
              <RiskBadge risk={prediction.risk_rating} />
              <Badge variant={prediction.recommendation_type === 'primary' ? 'gain' : 'brand'} size="xs">
                {prediction.recommendation_type.toUpperCase()}
              </Badge>
            </div>
          </div>
        </div>

        {/* Right: Trade Details */}
        <div className="flex-1 space-y-4">
          {/* Expected Move - Hero Stat */}
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                Expected Move
              </div>
              <div
                className={clsx(
                  'text-4xl font-black font-mono',
                  prediction.expected_move_pct >= 0 ? 'text-gain' : 'text-loss'
                )}
              >
                {prediction.expected_move_pct >= 0 ? '+' : ''}
                {prediction.expected_move_pct.toFixed(1)}%
              </div>
            </div>
            <div className="ml-auto flex flex-col items-end">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                Hold Duration
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-brand" />
                <span className="text-sm font-mono text-gray-200">
                  {prediction.expected_hold_duration}
                </span>
              </div>
            </div>
          </div>

          {/* Price Levels */}
          <div className="grid grid-cols-2 gap-3">
            {/* Entry Zone */}
            <div className="bg-brand/8 border border-brand/15 rounded-lg p-3">
              <div className="text-[10px] text-brand/70 uppercase tracking-wider mb-1.5">
                Entry Zone
              </div>
              <div className="font-mono text-sm text-gray-200">
                {formatCurrency(prediction.entry_zone_low)} –{' '}
                {formatCurrency(prediction.entry_zone_high)}
              </div>
            </div>

            {/* Stop Loss */}
            <div className="bg-loss/8 border border-loss/15 rounded-lg p-3">
              <div className="flex items-center gap-1 mb-1.5">
                <ArrowDownRight className="w-3 h-3 text-loss/70" />
                <span className="text-[10px] text-loss/70 uppercase tracking-wider">Stop Loss</span>
              </div>
              <div className="font-mono text-sm text-loss">
                {formatCurrency(prediction.stop_loss)}
              </div>
            </div>

            {/* Target 1 */}
            <div className="bg-gain/8 border border-gain/15 rounded-lg p-3">
              <div className="flex items-center gap-1 mb-1.5">
                <Target className="w-3 h-3 text-gain/70" />
                <span className="text-[10px] text-gain/70 uppercase tracking-wider">
                  Target 1
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-gain">
                  {formatCurrency(prediction.profit_target_1)}
                </span>
                <span className="text-[10px] text-gain/60 font-mono">
                  {formatPercent(
                    ((prediction.profit_target_1 - prediction.entry_zone_high) /
                      prediction.entry_zone_high) *
                      100
                  )}
                </span>
              </div>
            </div>

            {/* Target 2 */}
            <div className="bg-gain/5 border border-gain/10 rounded-lg p-3">
              <div className="flex items-center gap-1 mb-1.5">
                <ArrowUpRight className="w-3 h-3 text-gain/50" />
                <span className="text-[10px] text-gain/50 uppercase tracking-wider">
                  Target 2
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-gain/70">
                  {formatCurrency(prediction.profit_target_2)}
                </span>
                <span className="text-[10px] text-gain/40 font-mono">
                  {formatPercent(
                    ((prediction.profit_target_2 - prediction.entry_zone_high) /
                      prediction.entry_zone_high) *
                      100
                  )}
                </span>
              </div>
            </div>
          </div>

          {/* Risk/Reward */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-xs text-gray-500">Risk/Reward:</span>
              <span className="text-sm font-mono font-semibold text-white">
                1:{riskReward}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Upside:</span>
              <span className="text-sm font-mono text-gain font-semibold">
                {prediction.upside_probability}%
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Downside:</span>
              <span className="text-sm font-mono text-loss font-semibold">
                {prediction.downside_risk}%
              </span>
            </div>
          </div>

          {/* Signal Types */}
          <div className="flex flex-wrap gap-1.5">
            {prediction.signal_types.map((s) => (
              <SignalBadge key={s} signal={s} />
            ))}
          </div>
        </div>
      </div>

      {/* Catalyst Summary */}
      <div className="mt-5 pt-4 border-t border-white/5">
        <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">
          Catalyst Summary
        </div>
        <p className="text-sm text-gray-400 leading-relaxed mb-3">
          {prediction.catalyst_summary}
        </p>

        {/* Plain English */}
        <div className="bg-base/60 border border-white/5 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 rounded-full bg-brand/20 flex items-center justify-center flex-shrink-0">
              <ChevronRight className="w-2.5 h-2.5 text-brand" />
            </div>
            <span className="text-xs text-brand font-semibold uppercase tracking-wider">
              AI Analysis
            </span>
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">
            {prediction.plain_english_explanation}
          </p>
        </div>
      </div>
    </Card>
  )
}
