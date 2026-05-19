import { motion } from 'framer-motion'
import WinRateCard from '@/components/learning/WinRateCard'
import SignalPerformance from '@/components/learning/SignalPerformance'
import ConfidenceHistoryChart from '@/components/charts/ConfidenceHistoryChart'
import LearningTimeline from '@/components/learning/LearningTimeline'
import SectorHeatmap from '@/components/charts/SectorHeatmap'
import { useModelPerformance, useConfidenceHistory } from '@/hooks/usePredictions'

export default function AnalyticsPage() {
  const { data: performance, isLoading: perfLoading } = useModelPerformance()
  const { data: history } = useConfidenceHistory(30)

  return (
    <div className="space-y-6">
      {/* Header Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <WinRateCard performance={performance ?? null} isLoading={perfLoading} />
        <SignalPerformance performance={performance ?? null} />
        <SectorHeatmap />
      </div>

      {/* Confidence History Chart */}
      {history && <ConfidenceHistoryChart data={history} />}

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {history && <LearningTimeline history={history} />}

        {/* Model Stats Table */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
          className="bg-surface border border-white/5 rounded-xl p-4 shadow-card"
        >
          <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">
            Model Metrics
          </div>
          <div className="space-y-3">
            {performance &&
              [
                {
                  label: 'Total Predictions',
                  value: performance.total_predictions.toLocaleString(),
                  color: 'text-gray-300',
                },
                {
                  label: 'Win Rate',
                  value: `${performance.win_rate.toFixed(1)}%`,
                  color: 'text-gain',
                },
                {
                  label: 'Average Return',
                  value: `+${performance.avg_return.toFixed(1)}%`,
                  color: 'text-gain',
                },
                {
                  label: 'Avg Confidence',
                  value: `${performance.avg_confidence.toFixed(0)}%`,
                  color: 'text-brand',
                },
                {
                  label: 'Sharpe Ratio',
                  value: performance.sharpe_ratio?.toFixed(2) ?? 'N/A',
                  color: 'text-gain',
                },
                {
                  label: 'Max Drawdown',
                  value: `${performance.max_drawdown?.toFixed(1) ?? 'N/A'}%`,
                  color: 'text-loss',
                },
                {
                  label: 'Profit Factor',
                  value: `${performance.profit_factor?.toFixed(1) ?? 'N/A'}x`,
                  color: 'text-gain',
                },
                {
                  label: 'Best Signal',
                  value: performance.best_signal_type.toUpperCase(),
                  color: 'text-warning',
                },
              ].map(({ label, value, color }) => (
                <div
                  key={label}
                  className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                >
                  <span className="text-xs text-gray-500">{label}</span>
                  <span className={`font-mono text-sm font-semibold ${color}`}>{value}</span>
                </div>
              ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
