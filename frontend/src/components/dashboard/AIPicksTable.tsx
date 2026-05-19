import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Filter,
  ArrowUpDown,
} from 'lucide-react'
import { clsx } from 'clsx'
import { Prediction } from '@/types'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { RiskBadge, RecommendationTypeBadge, SignalBadge } from '@/components/ui/Badge'
import { formatCurrency } from '@/utils/formatters'
import { getChangeColor } from '@/utils/colors'

type FilterType = 'all' | 'primary' | 'secondary' | 'watchlist'
type SortKey = 'ticker' | 'confidence_score' | 'expected_move_pct' | 'risk_rating'
type SortDir = 'asc' | 'desc'

interface AIPicksTableProps {
  predictions: Prediction[]
  isLoading?: boolean
  onSelectPrediction?: (p: Prediction) => void
}

export default function AIPicksTable({
  predictions,
  isLoading,
  onSelectPrediction,
}: AIPicksTableProps) {
  const [filter, setFilter] = useState<FilterType>('all')
  const [sort, setSort] = useState<SortKey>('confidence_score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const filtered = useMemo(() => {
    let data = filter === 'all' ? predictions : predictions.filter((p) => p.recommendation_type === filter)

    data = [...data].sort((a, b) => {
      let av: string | number = a[sort] as string | number
      let bv: string | number = b[sort] as string | number
      if (typeof av === 'string') av = av.toLowerCase()
      if (typeof bv === 'string') bv = bv.toLowerCase()
      const cmp = av < bv ? -1 : av > bv ? 1 : 0
      return sortDir === 'asc' ? cmp : -cmp
    })

    return data
  }, [predictions, filter, sort, sortDir])

  const handleSort = (key: SortKey) => {
    if (sort === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSort(key)
      setSortDir('desc')
    }
  }

  const SortIcon = ({ col }: { col: SortKey }) =>
    sort === col ? (
      sortDir === 'asc' ? (
        <ChevronUp className="w-3 h-3" />
      ) : (
        <ChevronDown className="w-3 h-3" />
      )
    ) : (
      <ArrowUpDown className="w-3 h-3 opacity-30" />
    )

  const filterCounts: Record<FilterType, number> = {
    all: predictions.length,
    primary: predictions.filter((p) => p.recommendation_type === 'primary').length,
    secondary: predictions.filter((p) => p.recommendation_type === 'secondary').length,
    watchlist: predictions.filter((p) => p.recommendation_type === 'watchlist').length,
  }

  return (
    <Card animate noPadding>
      <div className="p-4 border-b border-white/5">
        <CardHeader className="mb-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-brand" />
            <CardTitle>AI Picks</CardTitle>
            <span className="text-xs text-gray-600 font-mono">
              ({filtered.length} results)
            </span>
          </div>
        </CardHeader>

        {/* Filter tabs */}
        <div className="flex gap-1">
          {(['all', 'primary', 'secondary', 'watchlist'] as FilterType[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                filter === f
                  ? 'bg-brand/15 text-brand border border-brand/25'
                  : 'text-gray-500 hover:text-gray-300 border border-transparent hover:bg-white/5'
              )}
            >
              {f.toUpperCase()}
              <span className={clsx('text-[10px] font-mono', filter === f ? 'text-brand/70' : 'text-gray-700')}>
                {filterCounts[f]}
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/5">
              {[
                { key: 'ticker' as SortKey, label: 'Ticker', width: 'w-32' },
                { key: 'confidence_score' as SortKey, label: 'Confidence', width: 'w-36' },
                { key: null, label: 'Risk/Reward', width: 'w-28' },
                { key: null, label: 'Catalyst', width: '' },
                { key: null, label: 'Sentiment', width: 'w-24' },
                { key: 'expected_move_pct' as SortKey, label: 'Exp. Move', width: 'w-24' },
                { key: null, label: 'Hold', width: 'w-24' },
                { key: 'risk_rating' as SortKey, label: 'Risk', width: 'w-20' },
                { key: null, label: '', width: 'w-10' },
              ].map(({ key, label, width }) => (
                <th
                  key={label || Math.random()}
                  className={clsx(
                    'px-4 py-3 text-left text-[10px] text-gray-600 uppercase tracking-wider font-medium',
                    width,
                    key && 'cursor-pointer hover:text-gray-400 transition-colors'
                  )}
                  onClick={() => key && handleSort(key)}
                >
                  <div className="flex items-center gap-1">
                    {label}
                    {key && <SortIcon col={key} />}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b border-white/5">
                  {Array.from({ length: 9 }).map((_, j) => (
                    <td key={j} className="px-4 py-4">
                      <div className="h-4 bg-white/5 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-gray-600">
                  No picks found for the selected filter.
                </td>
              </tr>
            ) : (
              filtered.map((pred) => (
                <>
                  <motion.tr
                    key={pred.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className={clsx(
                      'border-b border-white/5 transition-colors cursor-pointer',
                      expandedId === pred.id
                        ? 'bg-brand/5 border-brand/10'
                        : 'hover:bg-white/3'
                    )}
                    onClick={() => {
                      setExpandedId(expandedId === pred.id ? null : pred.id)
                      onSelectPrediction?.(pred)
                    }}
                  >
                    {/* Ticker */}
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-mono font-bold text-white text-sm">{pred.ticker}</div>
                        <RecommendationTypeBadge type={pred.recommendation_type} />
                      </div>
                    </td>

                    {/* Confidence */}
                    <td className="px-4 py-3">
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className={clsx('text-sm font-mono font-bold',
                            pred.confidence_score >= 80 ? 'text-gain' :
                            pred.confidence_score >= 65 ? 'text-brand' :
                            pred.confidence_score >= 40 ? 'text-warning' : 'text-loss'
                          )}>
                            {pred.confidence_score}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden w-24">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${pred.confidence_score}%`,
                              background: pred.confidence_score >= 80 ? '#10b981' :
                                pred.confidence_score >= 65 ? '#3b82f6' :
                                pred.confidence_score >= 40 ? '#f59e0b' : '#ef4444',
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* Risk/Reward */}
                    <td className="px-4 py-3">
                      <div className="font-mono text-sm text-gray-300">
                        1:
                        {pred.entry_zone_high > 0 && pred.stop_loss > 0
                          ? (
                              (pred.profit_target_1 - pred.entry_zone_high) /
                              (pred.entry_zone_high - pred.stop_loss)
                            ).toFixed(1)
                          : 'N/A'}
                      </div>
                    </td>

                    {/* Catalyst */}
                    <td className="px-4 py-3">
                      <p className="text-xs text-gray-400 leading-snug line-clamp-2 max-w-64">
                        {pred.catalyst_summary}
                      </p>
                    </td>

                    {/* Sentiment */}
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {pred.signal_types.slice(0, 2).map((s) => (
                          <SignalBadge key={s} signal={s} />
                        ))}
                      </div>
                    </td>

                    {/* Expected Move */}
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'font-mono text-sm font-bold',
                          getChangeColor(pred.expected_move_pct)
                        )}
                      >
                        {pred.expected_move_pct >= 0 ? '+' : ''}
                        {pred.expected_move_pct.toFixed(1)}%
                      </span>
                    </td>

                    {/* Hold Duration */}
                    <td className="px-4 py-3">
                      <span className="text-xs text-gray-500 font-mono">
                        {pred.expected_hold_duration}
                      </span>
                    </td>

                    {/* Risk */}
                    <td className="px-4 py-3">
                      <RiskBadge risk={pred.risk_rating} />
                    </td>

                    {/* Expand */}
                    <td className="px-4 py-3">
                      <ChevronRight
                        className={clsx(
                          'w-4 h-4 text-gray-600 transition-transform',
                          expandedId === pred.id && 'rotate-90'
                        )}
                      />
                    </td>
                  </motion.tr>

                  {/* Expanded Row */}
                  <AnimatePresence>
                    {expandedId === pred.id && (
                      <motion.tr
                        key={`${pred.id}-expanded`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <td colSpan={9} className="bg-base/60 border-b border-brand/10">
                          <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-3 gap-6">
                            {/* Price Levels */}
                            <div className="space-y-2">
                              <div className="text-[10px] text-gray-600 uppercase tracking-wider">
                                Price Levels
                              </div>
                              {[
                                { label: 'Entry Zone', value: `${formatCurrency(pred.entry_zone_low)} – ${formatCurrency(pred.entry_zone_high)}`, color: 'text-brand' },
                                { label: 'Stop Loss', value: formatCurrency(pred.stop_loss), color: 'text-loss' },
                                { label: 'Target 1', value: formatCurrency(pred.profit_target_1), color: 'text-gain' },
                                { label: 'Target 2', value: formatCurrency(pred.profit_target_2), color: 'text-gain/70' },
                              ].map(({ label, value, color }) => (
                                <div key={label} className="flex justify-between">
                                  <span className="text-xs text-gray-500">{label}</span>
                                  <span className={clsx('text-xs font-mono font-semibold', color)}>
                                    {value}
                                  </span>
                                </div>
                              ))}
                            </div>

                            {/* Analysis */}
                            <div className="space-y-2">
                              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">
                                Technical
                              </div>
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {pred.technical_summary}
                              </p>
                              <div className="text-[10px] text-gray-600 uppercase tracking-wider mt-3 mb-1">
                                Sentiment
                              </div>
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {pred.sentiment_summary}
                              </p>
                            </div>

                            {/* Full Explanation */}
                            <div>
                              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-2">
                                AI Explanation
                              </div>
                              <p className="text-xs text-gray-400 leading-relaxed">
                                {pred.plain_english_explanation}
                              </p>
                            </div>
                          </div>
                        </td>
                      </motion.tr>
                    )}
                  </AnimatePresence>
                </>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
