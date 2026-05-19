import { motion } from 'framer-motion'
import MarketOverview from '@/components/dashboard/MarketOverview'
import BestTradeOfDay from '@/components/dashboard/BestTradeOfDay'
import AIPicksTable from '@/components/dashboard/AIPicksTable'
import NewsFeed from '@/components/sentiment/NewsFeed'
import { useTonightsPredictions } from '@/hooks/usePredictions'

export default function DashboardPage() {
  const { data: predictions, isLoading } = useTonightsPredictions()

  const primaryPick = predictions?.find((p) => p.recommendation_type === 'primary') ?? null

  return (
    <div className="space-y-6">
      {/* Market Overview - full width */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <MarketOverview />
      </motion.div>

      {/* Middle: Best Trade + News */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Best Trade of Day - 60% */}
        <div className="lg:col-span-3">
          <BestTradeOfDay prediction={primaryPick} isLoading={isLoading} />
        </div>

        {/* News Feed - 40% */}
        <div className="lg:col-span-2">
          <NewsFeed maxItems={6} />
        </div>
      </div>

      {/* AI Picks Table - full width */}
      <AIPicksTable predictions={predictions ?? []} isLoading={isLoading} />
    </div>
  )
}
