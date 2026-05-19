export function getChangeColor(value: number): string {
  if (value > 0) return 'text-gain'
  if (value < 0) return 'text-loss'
  return 'text-gray-400'
}

export function getChangeBg(value: number): string {
  if (value > 0) return 'bg-gain/10 text-gain'
  if (value < 0) return 'bg-loss/10 text-loss'
  return 'bg-gray-700/50 text-gray-400'
}

export function getConfidenceColor(score: number): string {
  if (score >= 80) return 'text-gain'
  if (score >= 65) return 'text-brand'
  if (score >= 40) return 'text-warning'
  return 'text-loss'
}

export function getConfidenceBgColor(score: number): string {
  if (score >= 80) return '#10b981'
  if (score >= 65) return '#3b82f6'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

export function getConfidenceGradient(score: number): string {
  if (score >= 80) return 'from-gain to-gain/70'
  if (score >= 65) return 'from-brand to-brand/70'
  if (score >= 40) return 'from-warning to-warning/70'
  return 'from-loss to-loss/70'
}

export function getRiskColor(risk: string): string {
  switch (risk.toLowerCase()) {
    case 'low': return 'text-gain bg-gain/10 border-gain/20'
    case 'medium': return 'text-warning bg-warning/10 border-warning/20'
    case 'high': return 'text-loss bg-loss/10 border-loss/20'
    default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
  }
}

export function getRecommendationColor(rec: string): string {
  switch (rec.toLowerCase()) {
    case 'hold': return 'text-brand bg-brand/10 border-brand/20'
    case 'buy_more':
    case 'buy more': return 'text-gain bg-gain/10 border-gain/20'
    case 'average_down':
    case 'average down': return 'text-warning bg-warning/10 border-warning/20'
    case 'sell': return 'text-loss bg-loss/10 border-loss/20'
    default: return 'text-gray-400 bg-gray-400/10 border-gray-400/20'
  }
}

export function getSentimentColor(score: number): string {
  if (score >= 0.5) return 'text-gain'
  if (score >= 0.2) return 'text-gain/70'
  if (score >= -0.2) return 'text-gray-400'
  if (score >= -0.5) return 'text-loss/70'
  return 'text-loss'
}

export function getSentimentBg(score: number): string {
  if (score >= 0.5) return 'bg-gain/20 text-gain'
  if (score >= 0.2) return 'bg-gain/10 text-gain/80'
  if (score >= -0.2) return 'bg-gray-700/50 text-gray-400'
  if (score >= -0.5) return 'bg-loss/10 text-loss/80'
  return 'bg-loss/20 text-loss'
}

export function getMarketConditionColor(condition: string): string {
  switch (condition.toUpperCase()) {
    case 'BULLISH': return 'text-gain bg-gain/10 border-gain/30'
    case 'BEARISH': return 'text-loss bg-loss/10 border-loss/30'
    case 'VOLATILE': return 'text-warning bg-warning/10 border-warning/30'
    case 'NEUTRAL': return 'text-gray-400 bg-gray-700/30 border-gray-600/30'
    default: return 'text-gray-400 bg-gray-700/30 border-gray-600/30'
  }
}

export function getMarketStatusColor(status: string): string {
  switch (status) {
    case 'OPEN': return 'text-gain'
    case 'PRE-MARKET': return 'text-warning'
    case 'AFTER-HOURS': return 'text-brand'
    case 'CLOSED': return 'text-gray-500'
    default: return 'text-gray-500'
  }
}

export function getSectorColor(changePct: number): string {
  const intensity = Math.min(Math.abs(changePct) / 3, 1) // normalize to 0-1 for ±3%
  if (changePct > 0) {
    const green = Math.round(16 + intensity * (185 - 16))
    return `rgba(16, ${green}, 129, ${0.3 + intensity * 0.5})`
  } else if (changePct < 0) {
    const red = Math.round(239 - intensity * 50)
    return `rgba(${red}, 68, 68, ${0.3 + intensity * 0.5})`
  }
  return 'rgba(107, 114, 128, 0.3)'
}

export const CHART_COLORS = {
  primary: '#3b82f6',
  gain: '#10b981',
  loss: '#ef4444',
  warning: '#f59e0b',
  ema21: '#fbbf24',
  ema50: '#f97316',
  volume: '#3b82f680',
  grid: 'rgba(255,255,255,0.05)',
  text: 'rgba(255,255,255,0.5)',
}

export const PIE_COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ec4899',
  '#06b6d4',
  '#f97316',
  '#84cc16',
  '#14b8a6',
  '#a855f7',
]
