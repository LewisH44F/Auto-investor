import { useQuery } from '@tanstack/react-query'
import { getMarketOverview, getSectorData } from '@/api/sentiment'
import { MarketOverview } from '@/types'
import { getMarketStatus } from '@/utils/formatters'

const MOCK_MARKET_OVERVIEW: MarketOverview = {
  nasdaq_change_pct: 0.82,
  spy_change_pct: 0.54,
  qqq_change_pct: 0.91,
  vix: 18.3,
  vix_change: -1.2,
  trending_sectors: [
    { name: 'Technology', ticker: 'XLK', change_pct: 1.4 },
    { name: 'Financials', ticker: 'XLF', change_pct: 0.6 },
    { name: 'Energy', ticker: 'XLE', change_pct: -0.8 },
    { name: 'Healthcare', ticker: 'XLV', change_pct: 0.3 },
    { name: 'Cons. Disc.', ticker: 'XLY', change_pct: 1.1 },
    { name: 'Cons. Stap.', ticker: 'XLP', change_pct: -0.2 },
    { name: 'Industrials', ticker: 'XLI', change_pct: 0.7 },
    { name: 'Utilities', ticker: 'XLU', change_pct: -0.4 },
    { name: 'Real Estate', ticker: 'XLRE', change_pct: -0.9 },
    { name: 'Materials', ticker: 'XLB', change_pct: 0.2 },
    { name: 'Comm. Svc.', ticker: 'XLC', change_pct: 1.2 },
  ],
  market_condition: 'BULLISH',
  market_status: getMarketStatus(),
  timestamp: new Date().toISOString(),
}

export function useMarketOverview() {
  return useQuery({
    queryKey: ['market', 'overview'],
    queryFn: async () => {
      try {
        return await getMarketOverview()
      } catch {
        return MOCK_MARKET_OVERVIEW
      }
    },
    refetchInterval: 60_000, // every minute
    staleTime: 30_000,
    placeholderData: MOCK_MARKET_OVERVIEW,
  })
}

export function useSectorData() {
  return useQuery({
    queryKey: ['market', 'sectors'],
    queryFn: async () => {
      try {
        return await getSectorData()
      } catch {
        return MOCK_MARKET_OVERVIEW.trending_sectors
      }
    },
    refetchInterval: 60_000,
    staleTime: 30_000,
    placeholderData: MOCK_MARKET_OVERVIEW.trending_sectors,
  })
}
