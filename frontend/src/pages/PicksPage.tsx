import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { RefreshCw, Zap } from 'lucide-react'
import AIPicksTable from '@/components/dashboard/AIPicksTable'
import PriceChart from '@/components/charts/PriceChart'
import ConvictionMeter from '@/components/dashboard/ConvictionMeter'
import NewsFeed from '@/components/sentiment/NewsFeed'
import { RiskBadge, SignalBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import { useTonightsPredictions, useTriggerScan } from '@/hooks/usePredictions'
import { Prediction } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import { getChangeColor } from '@/utils/colors'
import { clsx } from 'clsx'

export default function PicksPage() {
  const { data: predictions, isLoading, refetch } = useTonightsPredictions()
  const [selected, setSelected] = useState<Prediction | null>(null)
  const triggerScan = useTriggerScan()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Tonight's AI Picks</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {predictions?.length ?? 0} setups analyzed for tomorrow's session
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="w-3.5 h-3.5" />}
            onClick={() => refetch()}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Zap className="w-3.5 h-3.5" />}
            loading={triggerScan.isPending}
            onClick={() => triggerScan.mutate()}
          >
            Run Scan
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main Table */}
        <div className="xl:col-span-2">
          <AIPicksTable
            predictions={predictions ?? []}
            isLoading={isLoading}
            onSelectPrediction={setSelected}
          />
        </div>

        {/* Side Panel */}
        <div className="xl:col-span-1 space-y-4">
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.2 }}
                className="space-y-4"
              >
                {/* Selected Prediction Card */}
                <Card>
                  <div className="flex items-center gap-3 mb-4">
                    <div>
                      <div className="text-3xl font-black font-mono text-white">
                        {selected.ticker}
                      </div>
                      {selected.company_name && (
                        <div className="text-xs text-gray-600">{selected.company_name}</div>
                      )}
                    </div>
                    <div className="ml-auto">
                      <ConvictionMeter score={selected.confidence_score} size="sm" showLabel={false} />
                    </div>
                  </div>

                  {/* Key Stats */}
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    {[
                      { label: 'Expected Move', value: `${selected.expected_move_pct >= 0 ? '+' : ''}${selected.expected_move_pct.toFixed(1)}%`, color: getChangeColor(selected.expected_move_pct) },
                      { label: 'Hold Duration', value: selected.expected_hold_duration, color: 'text-gray-300' },
                      { label: 'Entry Low', value: formatCurrency(selected.entry_zone_low), color: 'text-brand' },
                      { label: 'Entry High', value: formatCurrency(selected.entry_zone_high), color: 'text-brand' },
                      { label: 'Stop Loss', value: formatCurrency(selected.stop_loss), color: 'text-loss' },
                      { label: 'Target 1', value: formatCurrency(selected.profit_target_1), color: 'text-gain' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="bg-base/40 rounded-lg p-2.5">
                        <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-0.5">
                          {label}
                        </div>
                        <div className={clsx('text-sm font-mono font-semibold', color)}>
                          {value}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    <RiskBadge risk={selected.risk_rating} />
                    {selected.signal_types.map((s) => (
                      <SignalBadge key={s} signal={s} />
                    ))}
                  </div>

                  {/* Explanation */}
                  <div className="bg-base/60 border border-white/5 rounded-lg p-3">
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {selected.plain_english_explanation}
                    </p>
                  </div>
                </Card>

                {/* Price Chart */}
                <PriceChart
                  ticker={selected.ticker}
                  entryLow={selected.entry_zone_low}
                  entryHigh={selected.entry_zone_high}
                  stopLoss={selected.stop_loss}
                  target1={selected.profit_target_1}
                />

                {/* Ticker News */}
                <NewsFeed ticker={selected.ticker} maxItems={4} />
              </motion.div>
            ) : (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex flex-col items-center justify-center py-20 text-center"
              >
                <div className="w-12 h-12 rounded-xl bg-surface border border-white/5 flex items-center justify-center mb-3">
                  <Zap className="w-6 h-6 text-gray-700" />
                </div>
                <p className="text-sm text-gray-600">
                  Select a pick from the table to see details
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
