import { useQuery } from '@tanstack/react-query'
import { getNewsFeed, getSentimentData } from '@/api/sentiment'
import { NewsArticle, SentimentData } from '@/types'

const MOCK_NEWS: NewsArticle[] = [
  {
    id: '1',
    ticker: 'NVDA',
    headline: 'NVIDIA Reports Record Data Center Revenue, Surpasses Analyst Estimates',
    summary: 'NVIDIA posted $22.6B in data center revenue, up 427% year-over-year, driven by surging demand for H100 GPUs from hyperscalers.',
    source: 'Reuters',
    published_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    sentiment_score: 0.89,
    impact_score: 0.95,
    catalyst_type: 'earnings',
    url: 'https://reuters.com',
  },
  {
    id: '2',
    ticker: 'META',
    headline: 'Meta\'s Threads Hits 200M Monthly Active Users, Monetization Ahead of Schedule',
    summary: 'Meta\'s Twitter competitor Threads reached 200M MAU milestone 14 months after launch. Management signals monetization beginning Q1 2025.',
    source: 'Bloomberg',
    published_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    sentiment_score: 0.72,
    impact_score: 0.78,
    catalyst_type: 'product',
    url: 'https://bloomberg.com',
  },
  {
    id: '3',
    headline: 'Fed Officials Signal Patience on Rate Cuts as Inflation Stays Sticky',
    summary: 'Multiple Fed board members indicated the central bank is in no rush to cut rates, citing persistent services inflation above the 2% target.',
    source: 'WSJ',
    published_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
    sentiment_score: -0.45,
    impact_score: 0.85,
    catalyst_type: 'macro',
    url: 'https://wsj.com',
  },
  {
    id: '4',
    ticker: 'AMD',
    headline: 'AMD MI300X GPU Demand Tracking Ahead of Q4 Estimates, Analyst Says',
    summary: 'Morgan Stanley analyst notes channel checks show AMD MI300X GPU orders accelerating, raising price target to $195 from $165.',
    source: 'CNBC',
    published_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    sentiment_score: 0.65,
    impact_score: 0.72,
    catalyst_type: 'analyst',
    url: 'https://cnbc.com',
  },
  {
    id: '5',
    ticker: 'AAPL',
    headline: 'Apple Intelligence Features Drive 15% Upgrade Cycle Acceleration in Key Markets',
    summary: 'Early data from carrier sources indicate iPhone 16 series is seeing stronger-than-typical upgrade rates in markets where Apple Intelligence is available.',
    source: 'Barron\'s',
    published_at: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString(),
    sentiment_score: 0.58,
    impact_score: 0.68,
    catalyst_type: 'product',
    url: 'https://barrons.com',
  },
  {
    id: '6',
    headline: 'S&P 500 Hits New All-Time High as Tech Sector Leads Broad Market Rally',
    summary: 'The S&P 500 closed at a new record high, with the technology sector up 2.1% leading all sectors on positive AI infrastructure spending outlook.',
    source: 'FT',
    published_at: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
    sentiment_score: 0.76,
    impact_score: 0.80,
    catalyst_type: 'market',
    url: 'https://ft.com',
  },
  {
    id: '7',
    ticker: 'TSLA',
    headline: 'Tesla Cybertruck Production Ramp Faces Quality Control Challenges',
    summary: 'Reports emerge of elevated Cybertruck return rates as Tesla addresses manufacturing quality issues at Gigafactory Texas.',
    source: 'The Information',
    published_at: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    sentiment_score: -0.62,
    impact_score: 0.71,
    catalyst_type: 'operations',
    url: 'https://theinformation.com',
  },
]

const MOCK_SENTIMENT: SentimentData = {
  ticker: 'NVDA',
  news_score: 0.85,
  reddit_score: 0.72,
  analyst_score: 0.91,
  overall_score: 0.83,
  news_count: 47,
  updated_at: new Date().toISOString(),
}

export function useNewsFeed(ticker?: string) {
  return useQuery({
    queryKey: ['sentiment', 'news', ticker],
    queryFn: async () => {
      try {
        return await getNewsFeed(ticker)
      } catch {
        return ticker ? MOCK_NEWS.filter((n) => n.ticker === ticker) : MOCK_NEWS
      }
    },
    staleTime: 5 * 60_000,
    refetchInterval: 10 * 60_000,
    placeholderData: MOCK_NEWS,
  })
}

export function useSentimentData(ticker: string) {
  return useQuery({
    queryKey: ['sentiment', 'data', ticker],
    queryFn: async () => {
      try {
        return await getSentimentData(ticker)
      } catch {
        return { ...MOCK_SENTIMENT, ticker }
      }
    },
    staleTime: 5 * 60_000,
    enabled: !!ticker,
  })
}
