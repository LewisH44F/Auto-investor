import apiClient from './client'
import { BacktestResult, SignalPerformance, ChartDataPoint } from '@/types'

export interface BacktestParams {
  ticker: string
  start_date: string
  end_date: string
  initial_capital?: number
}

export async function runBacktest(params: BacktestParams): Promise<BacktestResult> {
  const response = await apiClient.post<BacktestResult>('/analytics/backtest', params)
  return response.data
}

export async function getSignalPerformance(): Promise<SignalPerformance[]> {
  const response = await apiClient.get<SignalPerformance[]>('/analytics/signal-performance')
  return response.data
}

export async function getPriceHistory(
  ticker: string,
  period: '1D' | '5D' | '1M' | '3M' | '1Y'
): Promise<ChartDataPoint[]> {
  const response = await apiClient.get<ChartDataPoint[]>(`/analytics/price-history/${ticker}`, {
    params: { period },
  })
  return response.data
}
