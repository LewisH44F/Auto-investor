import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getHoldings,
  getPortfolioStats,
  addHolding,
  removeHolding,
  getTransactions,
  refreshHoldingPrices,
} from '@/api/portfolio'
import { AddHoldingForm, Holding, PortfolioStats } from '@/types'
import toast from 'react-hot-toast'

const MOCK_HOLDINGS: Holding[] = [
  {
    id: '1',
    ticker: 'NVDA',
    company_name: 'NVIDIA Corporation',
    shares: 15,
    purchase_price: 820.0,
    current_price: 883.25,
    unrealized_pnl: 948.75,
    unrealized_pnl_pct: 7.71,
    ai_recommendation: 'hold',
    conviction_score: 87,
    last_assessed: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    reasoning: 'Strong momentum continuing. Hold through the current AI catalyst cycle. Next catalyst is earnings in 3 weeks.',
    sector: 'Technology',
    purchase_date: '2024-08-15',
  },
  {
    id: '2',
    ticker: 'AAPL',
    company_name: 'Apple Inc.',
    shares: 25,
    purchase_price: 195.0,
    current_price: 212.40,
    unrealized_pnl: 435.0,
    unrealized_pnl_pct: 8.92,
    ai_recommendation: 'hold',
    conviction_score: 72,
    last_assessed: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    reasoning: 'Services revenue growth strong. iPhone cycle starting. Maintain position heading into product announcements.',
    sector: 'Technology',
    purchase_date: '2024-07-20',
  },
  {
    id: '3',
    ticker: 'TSLA',
    company_name: 'Tesla Inc.',
    shares: 10,
    purchase_price: 285.0,
    current_price: 248.15,
    unrealized_pnl: -368.5,
    unrealized_pnl_pct: -12.93,
    ai_recommendation: 'average_down',
    conviction_score: 58,
    last_assessed: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
    reasoning: 'Price weakness creating opportunity to lower cost basis. Cybertruck ramp and energy storage growth provide long-term upside. Consider averaging down at current levels.',
    sector: 'Consumer Discretionary',
    purchase_date: '2024-09-10',
  },
  {
    id: '4',
    ticker: 'META',
    company_name: 'Meta Platforms',
    shares: 8,
    purchase_price: 520.0,
    current_price: 489.50,
    unrealized_pnl: -244.0,
    unrealized_pnl_pct: -5.87,
    ai_recommendation: 'hold',
    conviction_score: 74,
    last_assessed: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
    reasoning: 'Near-term weakness tied to overall market rotation from growth. Fundamentals intact. Ad revenue growth accelerating. Hold through consolidation.',
    sector: 'Communication Services',
    purchase_date: '2024-10-05',
  },
]

const MOCK_STATS: PortfolioStats = {
  total_value: 18845.25,
  total_invested: 18074.0,
  total_unrealized_pnl: 771.25,
  total_unrealized_pnl_pct: 4.27,
  cash_available: 5000.0,
  win_rate: 68.5,
  total_positions: 4,
  day_change: 243.8,
  day_change_pct: 1.31,
}

export function useHoldings() {
  return useQuery({
    queryKey: ['portfolio', 'holdings'],
    queryFn: async () => {
      try {
        return await getHoldings()
      } catch {
        return MOCK_HOLDINGS
      }
    },
    staleTime: 60_000,
    refetchInterval: 5 * 60_000,
    placeholderData: MOCK_HOLDINGS,
  })
}

export function usePortfolioStats() {
  return useQuery({
    queryKey: ['portfolio', 'stats'],
    queryFn: async () => {
      try {
        return await getPortfolioStats()
      } catch {
        return MOCK_STATS
      }
    },
    staleTime: 60_000,
    refetchInterval: 5 * 60_000,
    placeholderData: MOCK_STATS,
  })
}

export function useTransactions(holdingId?: string) {
  return useQuery({
    queryKey: ['portfolio', 'transactions', holdingId],
    queryFn: () => getTransactions(holdingId),
    staleTime: 5 * 60_000,
  })
}

export function useAddHolding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AddHoldingForm) => addHolding(data),
    onSuccess: () => {
      toast.success('Holding added successfully!')
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
    onError: () => {
      toast.error('Failed to add holding. Please try again.')
    },
  })
}

export function useRemoveHolding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => removeHolding(id),
    onSuccess: () => {
      toast.success('Holding removed.')
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
    onError: () => {
      toast.error('Failed to remove holding.')
    },
  })
}

export function useRefreshPrices() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: refreshHoldingPrices,
    onSuccess: () => {
      toast.success('Prices refreshed!')
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
    },
    onError: () => {
      toast.error('Failed to refresh prices.')
    },
  })
}
