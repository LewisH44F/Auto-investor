import { clsx } from 'clsx'
import { getSentimentColor, getSentimentBg } from '@/utils/colors'
import { SentimentData } from '@/types'
import { formatSentimentScore } from '@/utils/formatters'

interface SentimentBarProps {
  data: SentimentData
}

interface BarRowProps {
  label: string
  score: number
  count?: number
}

function BarRow({ label, score, count }: BarRowProps) {
  // score is -1 to 1, normalize to 0-100 for display
  const pct = ((score + 1) / 2) * 100
  const color = score > 0.3 ? '#10b981' : score > -0.3 ? '#f59e0b' : '#ef4444'

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500 w-14">{label}</span>
          {count !== undefined && (
            <span className="text-[10px] text-gray-700 font-mono">({count})</span>
          )}
        </div>
        <span className={clsx('text-xs font-mono font-bold', getSentimentColor(score))}>
          {score > 0 ? '+' : ''}{score.toFixed(2)}
        </span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            background: color,
            boxShadow: `0 0 6px ${color}60`,
          }}
        />
      </div>
    </div>
  )
}

export default function SentimentBar({ data }: SentimentBarProps) {
  return (
    <div className="space-y-4">
      {/* Overall Score */}
      <div className="flex items-center justify-between py-2 px-3 bg-base/40 rounded-lg border border-white/5">
        <span className="text-xs text-gray-500 uppercase tracking-wider">Overall Sentiment</span>
        <div className="flex items-center gap-2">
          <span className={clsx('text-sm font-mono font-bold', getSentimentColor(data.overall_score))}>
            {data.overall_score > 0 ? '+' : ''}{data.overall_score.toFixed(2)}
          </span>
          <span className={clsx('text-[10px] px-2 py-0.5 rounded-md border', getSentimentBg(data.overall_score))}>
            {formatSentimentScore(data.overall_score)}
          </span>
        </div>
      </div>

      {/* Individual sources */}
      <div className="space-y-3">
        <BarRow label="News" score={data.news_score} count={data.news_count} />
        <BarRow label="Reddit" score={data.reddit_score} />
        <BarRow label="Analysts" score={data.analyst_score} />
      </div>

      {/* Scale */}
      <div className="flex items-center justify-between text-[9px] text-gray-700 px-1">
        <span>VERY BEARISH</span>
        <span>NEUTRAL</span>
        <span>VERY BULLISH</span>
      </div>
    </div>
  )
}
