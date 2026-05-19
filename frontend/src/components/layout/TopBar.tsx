import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'
import { formatMarketTime } from '@/utils/formatters'
import { getMarketStatusColor, getChangeColor } from '@/utils/colors'
import { getMarketStatus } from '@/utils/formatters'
import { useMarketOverview } from '@/hooks/useMarketData'
import Button from '@/components/ui/Button'
import { useQueryClient } from '@tanstack/react-query'

const PAGE_TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/picks': "Tonight's Picks",
  '/portfolio': 'Portfolio',
  '/analytics': 'Analytics',
  '/backtest': 'Backtest',
  '/settings': 'Settings',
}

export default function TopBar() {
  const location = useLocation()
  const [time, setTime] = useState(formatMarketTime())
  const [notifications] = useState(3)
  const { data: market } = useMarketOverview()
  const queryClient = useQueryClient()
  const [refreshing, setRefreshing] = useState(false)

  const title = PAGE_TITLES[location.pathname] || 'Dashboard'
  const marketStatus = getMarketStatus()
  const statusColor = getMarketStatusColor(marketStatus)

  useEffect(() => {
    const interval = setInterval(() => {
      setTime(formatMarketTime())
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleRefresh = async () => {
    setRefreshing(true)
    await queryClient.invalidateQueries()
    setTimeout(() => setRefreshing(false), 1000)
  }

  return (
    <header className="flex items-center justify-between h-14 px-6 bg-surface border-b border-white/5 flex-shrink-0">
      {/* Page Title */}
      <div>
        <h1 className="text-lg font-semibold text-white">{title}</h1>
      </div>

      {/* Center - Market Stats */}
      <div className="hidden md:flex items-center gap-6">
        {/* Time */}
        <div className="flex items-center gap-2">
          <span className={clsx('text-xs font-bold font-mono', statusColor)}>
            {marketStatus}
          </span>
          <span className="text-sm font-mono text-gray-400">{time} ET</span>
        </div>

        {/* Divider */}
        <div className="w-px h-4 bg-white/10" />

        {/* NASDAQ */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-500 font-medium">NDX</span>
          <span
            className={clsx(
              'text-sm font-mono font-semibold',
              getChangeColor(market?.nasdaq_change_pct ?? 0)
            )}
          >
            {(market?.nasdaq_change_pct ?? 0) >= 0 ? '+' : ''}
            {(market?.nasdaq_change_pct ?? 0).toFixed(2)}%
          </span>
        </div>

        {/* SPY */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-500 font-medium">SPY</span>
          <span
            className={clsx(
              'text-sm font-mono font-semibold',
              getChangeColor(market?.spy_change_pct ?? 0)
            )}
          >
            {(market?.spy_change_pct ?? 0) >= 0 ? '+' : ''}
            {(market?.spy_change_pct ?? 0).toFixed(2)}%
          </span>
        </div>

        {/* VIX */}
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-500 font-medium">VIX</span>
          <span
            className={clsx(
              'text-sm font-mono font-semibold',
              (market?.vix ?? 20) > 25
                ? 'text-loss'
                : (market?.vix ?? 20) > 18
                ? 'text-warning'
                : 'text-gain'
            )}
          >
            {(market?.vix ?? 18.3).toFixed(1)}
          </span>
        </div>
      </div>

      {/* Right - Actions */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          icon={<RefreshCw className={clsx('w-4 h-4', refreshing && 'animate-spin')} />}
          onClick={handleRefresh}
          className="text-gray-500 hover:text-gray-300"
        />
        <div className="relative">
          <Button
            variant="ghost"
            size="sm"
            icon={<Bell className="w-4 h-4" />}
            className="text-gray-500 hover:text-gray-300"
          />
          {notifications > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand text-[9px] font-bold text-white">
              {notifications}
            </span>
          )}
        </div>
      </div>
    </header>
  )
}
