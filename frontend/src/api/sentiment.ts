import apiClient from './client'
import { NewsArticle, SentimentData, MarketOverview } from '@/types'

export async function getNewsFeed(ticker?: string): Promise<NewsArticle[]> {
  const response = await apiClient.get<NewsArticle[]>('/sentiment/news', {
    params: ticker ? { ticker } : undefined,
  })
  return response.data
}

export async function getSentimentData(ticker: string): Promise<SentimentData> {
  const response = await apiClient.get<SentimentData>(`/sentiment/${ticker}`)
  return response.data
}

export async function getMarketOverview(): Promise<MarketOverview> {
  const response = await apiClient.get<MarketOverview>('/market/overview')
  return response.data
}

export async function getSectorData(): Promise<
  Array<{ name: string; ticker: string; change_pct: number; market_cap?: number }>
> {
  const response = await apiClient.get('/market/sectors')
  return response.data
}
