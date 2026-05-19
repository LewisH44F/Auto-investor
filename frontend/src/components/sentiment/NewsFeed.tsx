import { useState } from 'react'
import { clsx } from 'clsx'
import { ExternalLink, Newspaper } from 'lucide-react'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import { useNewsFeed } from '@/hooks/useSentiment'
import { getSentimentBg } from '@/utils/colors'
import { formatTimeAgo } from '@/utils/formatters'
import { SpinnerOverlay } from '@/components/ui/Spinner'
import { NewsArticle } from '@/types'

const CATALYST_VARIANTS: Record<string, 'brand' | 'gain' | 'warning' | 'loss' | 'default'> = {
  earnings: 'gain',
  analyst: 'brand',
  product: 'brand',
  macro: 'warning',
  operations: 'warning',
  market: 'default',
}

function NewsItem({ article }: { article: NewsArticle }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className="py-3 border-b border-white/5 last:border-0 cursor-pointer hover:bg-white/2 -mx-4 px-4 transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {/* Tags row */}
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            {article.ticker && (
              <span className="font-mono text-[10px] font-bold text-brand bg-brand/10 border border-brand/20 px-1.5 py-0.5 rounded">
                {article.ticker}
              </span>
            )}
            <Badge
              variant={CATALYST_VARIANTS[article.catalyst_type] || 'default'}
              size="xs"
            >
              {article.catalyst_type.toUpperCase()}
            </Badge>
          </div>

          {/* Headline */}
          <h4 className="text-sm text-gray-200 leading-snug font-medium line-clamp-2 mb-1.5">
            {article.headline}
          </h4>

          {/* Summary if expanded */}
          {expanded && (
            <p className="text-xs text-gray-500 leading-relaxed mb-2 mt-1">
              {article.summary}
            </p>
          )}

          {/* Meta row */}
          <div className="flex items-center gap-3">
            <span className="text-[10px] text-gray-600 font-medium">{article.source}</span>
            <span className="text-[10px] text-gray-700">
              {formatTimeAgo(article.published_at)}
            </span>
            {/* Sentiment pill */}
            <span
              className={clsx(
                'text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-full border',
                getSentimentBg(article.sentiment_score)
              )}
            >
              {article.sentiment_score > 0 ? '+' : ''}
              {article.sentiment_score.toFixed(2)}
            </span>
          </div>
        </div>

        {/* External link */}
        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="flex-shrink-0 p-1.5 rounded-lg text-gray-700 hover:text-gray-400 hover:bg-white/5 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  )
}

interface NewsFeedProps {
  ticker?: string
  maxItems?: number
}

export default function NewsFeed({ ticker, maxItems }: NewsFeedProps) {
  const { data: news, isLoading } = useNewsFeed(ticker)
  const displayNews = maxItems ? news?.slice(0, maxItems) : news

  return (
    <Card animate noPadding className="flex flex-col">
      <div className="p-4 border-b border-white/5 flex-shrink-0">
        <CardHeader className="mb-0">
          <div className="flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-brand" />
            <CardTitle>{ticker ? `${ticker} News` : 'Market News'}</CardTitle>
          </div>
          {news && (
            <span className="text-[10px] text-gray-600 font-mono">{news.length} articles</span>
          )}
        </CardHeader>
      </div>

      <div className="flex-1 overflow-y-auto px-4 max-h-[500px]">
        {isLoading ? (
          <SpinnerOverlay message="Loading news..." />
        ) : !displayNews?.length ? (
          <div className="py-12 text-center text-gray-600 text-sm">
            No recent news found.
          </div>
        ) : (
          <div>
            {displayNews.map((article) => (
              <NewsItem key={article.id} article={article} />
            ))}
          </div>
        )}
      </div>
    </Card>
  )
}
