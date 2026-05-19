export interface Prediction {
  id: string
  ticker: string
  confidence_score: number // 0-100
  upside_probability: number // 0-100
  downside_risk: number // 0-100
  volatility_score: number
  momentum_score: number
  catalyst_summary: string
  technical_summary: string
  sentiment_summary: string
  entry_zone_low: number
  entry_zone_high: number
  stop_loss: number
  profit_target_1: number
  profit_target_2: number
  expected_move_pct: number
  expected_hold_duration: 'overnight' | '2-5 days' | '1 week' | '2 weeks'
  risk_rating: 'low' | 'medium' | 'high'
  recommendation_type: 'primary' | 'secondary' | 'watchlist'
  plain_english_explanation: string
  prediction_date: string
  signal_types: string[]
  company_name?: string
  sector?: string
  current_price?: number
}

export interface Holding {
  id: string
  ticker: string
  company_name?: string
  shares: number
  purchase_price: number
  current_price: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  ai_recommendation: 'hold' | 'sell' | 'buy_more' | 'average_down'
  conviction_score: number
  last_assessed: string
  reasoning: string
  sector?: string
  purchase_date?: string
}

export interface NewsArticle {
  id: string
  ticker?: string
  headline: string
  summary: string
  source: string
  published_at: string
  sentiment_score: number // -1 to 1
  impact_score: number // 0-1
  catalyst_type: string
  url?: string
}

export interface MarketOverview {
  nasdaq_change_pct: number
  spy_change_pct: number
  qqq_change_pct: number
  vix: number
  vix_change: number
  trending_sectors: Array<{ name: string; ticker: string; change_pct: number }>
  market_condition: 'BULLISH' | 'BEARISH' | 'NEUTRAL' | 'VOLATILE'
  market_status: 'OPEN' | 'CLOSED' | 'PRE-MARKET' | 'AFTER-HOURS'
  timestamp: string
}

export interface ModelPerformance {
  win_rate: number
  total_predictions: number
  avg_confidence: number
  avg_return: number
  best_signal_type: string
  signal_weights: Record<string, number>
  sharpe_ratio?: number
  max_drawdown?: number
  profit_factor?: number
}

export interface SignalPerformance {
  signal_type: string
  win_rate: number
  total_signals: number
  avg_return: number
  weight: number
}

export interface BacktestResult {
  ticker: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return_pct: number
  win_rate: number
  total_trades: number
  sharpe_ratio: number
  max_drawdown: number
  profit_factor: number
  trades: BacktestTrade[]
}

export interface BacktestTrade {
  entry_date: string
  exit_date: string
  ticker: string
  direction: 'long' | 'short'
  entry_price: number
  exit_price: number
  return_pct: number
  profit_loss: number
  signal_types: string[]
}

export interface ConfidenceHistory {
  date: string
  confidence: number
  actual_return: number
  was_correct: boolean
  ticker: string
}

export interface Transaction {
  id: string
  ticker: string
  type: 'buy' | 'sell'
  shares: number
  price: number
  total: number
  date: string
  notes?: string
}

export interface PortfolioStats {
  total_value: number
  total_invested: number
  total_unrealized_pnl: number
  total_unrealized_pnl_pct: number
  cash_available: number
  win_rate: number
  total_positions: number
  day_change: number
  day_change_pct: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface ApiError {
  message: string
  code?: string
  status?: number
}

export interface SentimentData {
  ticker: string
  news_score: number
  reddit_score: number
  analyst_score: number
  overall_score: number
  news_count: number
  updated_at: string
}

export interface ChartDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface AddHoldingForm {
  ticker: string
  shares: number
  purchase_price: number
  purchase_date: string
  notes?: string
}

export interface NotificationSettings {
  email_enabled: boolean
  email_address?: string
  discord_enabled: boolean
  discord_webhook?: string
  telegram_enabled: boolean
  telegram_chat_id?: string
  notify_on_picks: boolean
  notify_on_alerts: boolean
}

export interface AppSettings {
  confidence_threshold: number
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive'
  trading_profile: 'swing_trader' | 'day_trader' | 'investor'
  notifications: NotificationSettings
  api_keys: {
    alpha_vantage?: string
    polygon?: string
  }
}
