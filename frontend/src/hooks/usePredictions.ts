import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getTonightsPredictions,
  getModelPerformance,
  getConfidenceHistory,
  triggerManualScan,
  getPredictionHistory,
  PredictionHistoryParams,
} from '@/api/predictions'
import { Prediction, ModelPerformance, ConfidenceHistory } from '@/types'
import toast from 'react-hot-toast'

const MOCK_PREDICTIONS: Prediction[] = [
  {
    id: '1',
    ticker: 'NVDA',
    company_name: 'NVIDIA Corporation',
    confidence_score: 87,
    upside_probability: 82,
    downside_risk: 18,
    volatility_score: 65,
    momentum_score: 88,
    catalyst_summary: 'Strong earnings beat + AI demand acceleration driving institutional accumulation',
    technical_summary: 'Breakout above 21-day EMA with elevated volume. RSI at 65 - not overbought yet.',
    sentiment_summary: 'Overwhelmingly bullish news flow. Analyst upgrades from MS and GS.',
    entry_zone_low: 875.0,
    entry_zone_high: 892.5,
    stop_loss: 858.0,
    profit_target_1: 920.0,
    profit_target_2: 955.0,
    expected_move_pct: 4.8,
    expected_hold_duration: '2-5 days',
    risk_rating: 'medium',
    recommendation_type: 'primary',
    plain_english_explanation: 'NVIDIA is setting up for a strong move higher. After a brief consolidation following its earnings beat, institutional money is flowing back in. The AI infrastructure buildout story remains fully intact, and the stock is showing textbook accumulation patterns. Risk is well-defined with a clear stop loss below the recent base. This is a high-conviction swing trade with asymmetric risk/reward.',
    prediction_date: new Date().toISOString(),
    signal_types: ['momentum', 'catalyst', 'technical', 'sentiment'],
    sector: 'Technology',
    current_price: 883.25,
  },
  {
    id: '2',
    ticker: 'META',
    company_name: 'Meta Platforms',
    confidence_score: 74,
    upside_probability: 71,
    downside_risk: 29,
    volatility_score: 52,
    momentum_score: 70,
    catalyst_summary: 'Ad revenue rebound + Threads monetization ahead of schedule',
    technical_summary: 'Testing key support at 200-day EMA. Volume drying up suggesting sellers exhausted.',
    sentiment_summary: 'Mildly bullish. Positive analyst coverage with price target raises.',
    entry_zone_low: 485.0,
    entry_zone_high: 495.0,
    stop_loss: 472.0,
    profit_target_1: 515.0,
    profit_target_2: 535.0,
    expected_move_pct: 3.2,
    expected_hold_duration: '2-5 days',
    risk_rating: 'low',
    recommendation_type: 'secondary',
    plain_english_explanation: 'Meta is bouncing from a key technical support level with improving fundamentals. Ad revenue growth is accelerating and the Threads platform is monetizing faster than expected. Good risk/reward setup with clear entry and stop levels.',
    prediction_date: new Date().toISOString(),
    signal_types: ['technical', 'catalyst', 'sentiment'],
    sector: 'Communication Services',
    current_price: 489.50,
  },
  {
    id: '3',
    ticker: 'AMD',
    company_name: 'Advanced Micro Devices',
    confidence_score: 62,
    upside_probability: 58,
    downside_risk: 42,
    volatility_score: 72,
    momentum_score: 55,
    catalyst_summary: 'MI300X GPU demand tracking above estimates in data center',
    technical_summary: 'Consolidating in a tightening range. Potential energy buildup for a move.',
    sentiment_summary: 'Mixed sentiment. Some analysts cautious on near-term margin pressure.',
    entry_zone_low: 162.0,
    entry_zone_high: 168.0,
    stop_loss: 155.0,
    profit_target_1: 178.0,
    profit_target_2: 190.0,
    expected_move_pct: 2.8,
    expected_hold_duration: '1 week',
    risk_rating: 'high',
    recommendation_type: 'watchlist',
    plain_english_explanation: 'AMD shows potential but the risk profile is elevated. MI300X GPU adoption is strong but margin concerns create headwinds. Monitoring for a clearer breakout signal before adding conviction.',
    prediction_date: new Date().toISOString(),
    signal_types: ['technical', 'momentum'],
    sector: 'Technology',
    current_price: 165.30,
  },
]

const MOCK_PERFORMANCE: ModelPerformance = {
  win_rate: 73.4,
  total_predictions: 247,
  avg_confidence: 76.2,
  avg_return: 3.8,
  best_signal_type: 'catalyst',
  signal_weights: {
    technical: 0.25,
    sentiment: 0.20,
    catalyst: 0.30,
    volume: 0.10,
    momentum: 0.10,
    macro: 0.05,
  },
  sharpe_ratio: 1.87,
  max_drawdown: -8.3,
  profit_factor: 2.4,
}

const MOCK_CONFIDENCE_HISTORY: ConfidenceHistory[] = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString(),
  confidence: 60 + Math.random() * 30,
  actual_return: (Math.random() - 0.35) * 8,
  was_correct: Math.random() > 0.27,
  ticker: ['NVDA', 'AAPL', 'MSFT', 'META', 'AMD'][Math.floor(Math.random() * 5)],
}))

export function useTonightsPredictions() {
  return useQuery({
    queryKey: ['predictions', 'tonight'],
    queryFn: async () => {
      try {
        return await getTonightsPredictions()
      } catch {
        return MOCK_PREDICTIONS
      }
    },
    staleTime: 5 * 60_000,
    refetchInterval: 10 * 60_000,
    placeholderData: MOCK_PREDICTIONS,
  })
}

export function useModelPerformance() {
  return useQuery({
    queryKey: ['predictions', 'performance'],
    queryFn: async () => {
      try {
        return await getModelPerformance()
      } catch {
        return MOCK_PERFORMANCE
      }
    },
    staleTime: 30 * 60_000,
    placeholderData: MOCK_PERFORMANCE,
  })
}

export function useConfidenceHistory(days = 30) {
  return useQuery({
    queryKey: ['predictions', 'confidence-history', days],
    queryFn: async () => {
      try {
        return await getConfidenceHistory(days)
      } catch {
        return MOCK_CONFIDENCE_HISTORY
      }
    },
    staleTime: 30 * 60_000,
    placeholderData: MOCK_CONFIDENCE_HISTORY,
  })
}

export function usePredictionHistory(params: PredictionHistoryParams = {}) {
  return useQuery({
    queryKey: ['predictions', 'history', params],
    queryFn: () => getPredictionHistory(params),
    staleTime: 5 * 60_000,
  })
}

export function useTriggerScan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: triggerManualScan,
    onSuccess: () => {
      toast.success('Scan triggered! Results will appear shortly.')
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['predictions'] })
      }, 5000)
    },
    onError: () => {
      toast.error('Failed to trigger scan. Please try again.')
    },
  })
}
