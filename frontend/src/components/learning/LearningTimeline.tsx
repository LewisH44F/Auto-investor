import { clsx } from 'clsx'
import { CheckCircle2, XCircle, Clock } from 'lucide-react'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { ConfidenceHistory } from '@/types'
import { formatDate } from '@/utils/formatters'
import { getChangeColor } from '@/utils/colors'

interface LearningTimelineProps {
  history: ConfidenceHistory[]
}

export default function LearningTimeline({ history }: LearningTimelineProps) {
  const recent = [...history].reverse().slice(0, 12)

  return (
    <Card animate>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-brand" />
          <CardTitle>Prediction History</CardTitle>
        </div>
      </CardHeader>

      <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
        {recent.map((item, i) => (
          <div
            key={i}
            className={clsx(
              'flex items-center gap-3 p-3 rounded-lg border transition-colors',
              item.was_correct
                ? 'bg-gain/5 border-gain/10'
                : 'bg-loss/5 border-loss/10'
            )}
          >
            {/* Icon */}
            {item.was_correct ? (
              <CheckCircle2 className="w-4 h-4 text-gain flex-shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-loss flex-shrink-0" />
            )}

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-white">{item.ticker}</span>
                <span className="text-[10px] text-gray-600">{formatDate(item.date)}</span>
              </div>
              <div className="flex items-center gap-3 mt-0.5">
                <span className="text-[10px] text-gray-600">
                  Confidence:{' '}
                  <span className="text-brand font-mono">{item.confidence.toFixed(0)}%</span>
                </span>
              </div>
            </div>

            {/* Return */}
            <div className="text-right">
              <div className={clsx('font-mono text-sm font-bold', getChangeColor(item.actual_return))}>
                {item.actual_return >= 0 ? '+' : ''}{item.actual_return.toFixed(1)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}
