import { format, formatDistanceToNow, parseISO } from 'date-fns'

export function formatCurrency(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatPercent(value: number, decimals = 2, showSign = true): string {
  const formatted = Math.abs(value).toFixed(decimals)
  if (showSign) {
    return value >= 0 ? `+${formatted}%` : `-${formatted}%`
  }
  return `${formatted}%`
}

export function formatPnl(value: number): string {
  const prefix = value >= 0 ? '+' : '-'
  return `${prefix}${formatCurrency(Math.abs(value))}`
}

export function formatVolume(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)}B`
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(0)}K`
  }
  return value.toString()
}

export function formatDate(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy')
  } catch {
    return dateStr
  }
}

export function formatDateTime(dateStr: string): string {
  try {
    return format(parseISO(dateStr), 'MMM d, yyyy HH:mm')
  } catch {
    return dateStr
  }
}

export function formatTimeAgo(dateStr: string): string {
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true })
  } catch {
    return dateStr
  }
}

export function formatMarketTime(): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(new Date())
}

export function getMarketStatus(): 'OPEN' | 'CLOSED' | 'PRE-MARKET' | 'AFTER-HOURS' {
  const now = new Date()
  const nyTime = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }))
  const day = nyTime.getDay()
  const hours = nyTime.getHours()
  const minutes = nyTime.getMinutes()
  const timeInMinutes = hours * 60 + minutes

  // Weekend
  if (day === 0 || day === 6) return 'CLOSED'

  const preMarketStart = 4 * 60      // 4:00 AM
  const marketOpen = 9 * 60 + 30    // 9:30 AM
  const marketClose = 16 * 60        // 4:00 PM
  const afterHoursEnd = 20 * 60      // 8:00 PM

  if (timeInMinutes < preMarketStart) return 'CLOSED'
  if (timeInMinutes < marketOpen) return 'PRE-MARKET'
  if (timeInMinutes < marketClose) return 'OPEN'
  if (timeInMinutes < afterHoursEnd) return 'AFTER-HOURS'
  return 'CLOSED'
}

export function formatSentimentScore(score: number): string {
  if (score >= 0.5) return 'Very Bullish'
  if (score >= 0.2) return 'Bullish'
  if (score >= -0.2) return 'Neutral'
  if (score >= -0.5) return 'Bearish'
  return 'Very Bearish'
}

export function clampValue(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max)
}

export function formatConfidence(value: number): string {
  return `${Math.round(value)}%`
}

export function formatShares(shares: number): string {
  return shares % 1 === 0 ? shares.toFixed(0) : shares.toFixed(2)
}
