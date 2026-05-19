import { NavLink, useLocation } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  Zap,
  Briefcase,
  BarChart2,
  FlaskConical,
  Settings,
  TrendingUp,
  Circle,
} from 'lucide-react'
import { getMarketStatus } from '@/utils/formatters'
import { getMarketStatusColor } from '@/utils/colors'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/picks', label: "Tonight's Picks", icon: Zap },
  { path: '/portfolio', label: 'Portfolio', icon: Briefcase },
  { path: '/analytics', label: 'Analytics', icon: BarChart2 },
  { path: '/backtest', label: 'Backtest', icon: FlaskConical },
  { path: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  const location = useLocation()
  const marketStatus = getMarketStatus()
  const statusColor = getMarketStatusColor(marketStatus)

  const statusDotColor = {
    OPEN: 'bg-gain',
    'PRE-MARKET': 'bg-warning',
    'AFTER-HOURS': 'bg-brand',
    CLOSED: 'bg-gray-500',
  }[marketStatus]

  return (
    <aside className="flex flex-col w-60 min-h-screen bg-surface border-r border-white/5 flex-shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/5">
        <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-brand/20 border border-brand/30 shadow-glow-blue">
          <TrendingUp className="w-5 h-5 text-brand" />
        </div>
        <div>
          <div className="text-sm font-bold text-white leading-tight">AutoInvestor</div>
          <div className="text-[10px] text-brand font-medium tracking-widest uppercase">AI System</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => {
          const isActive =
            path === '/' ? location.pathname === '/' : location.pathname.startsWith(path)

          return (
            <NavLink
              key={path}
              to={path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                'transition-all duration-150 group',
                isActive
                  ? 'bg-brand/15 text-brand border border-brand/25 shadow-glow-blue/10'
                  : 'text-gray-500 hover:text-gray-200 hover:bg-white/5 border border-transparent'
              )}
            >
              <Icon
                className={clsx(
                  'w-4 h-4 flex-shrink-0 transition-colors',
                  isActive ? 'text-brand' : 'text-gray-600 group-hover:text-gray-300'
                )}
              />
              <span>{label}</span>
              {path === '/picks' && (
                <span className="ml-auto flex h-4 w-4 items-center justify-center rounded-full bg-brand/20 text-[9px] font-bold text-brand">
                  3
                </span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Market Status */}
      <div className="px-4 py-4 border-t border-white/5">
        <div className="flex items-center gap-2 px-3 py-2.5 rounded-lg bg-base/50 border border-white/5">
          <div className="relative flex items-center">
            <Circle className={clsx('w-2 h-2 fill-current', statusColor)} />
            {marketStatus === 'OPEN' && (
              <span className="absolute inset-0 rounded-full animate-ping opacity-75 bg-gain w-2 h-2" />
            )}
          </div>
          <div>
            <div className={clsx('text-xs font-bold font-mono', statusColor)}>
              {marketStatus}
            </div>
            <div className="text-[10px] text-gray-600">NYSE / NASDAQ</div>
          </div>
          <div className="ml-auto">
            <div className={clsx('w-1.5 h-1.5 rounded-full', statusDotColor, marketStatus === 'OPEN' && 'animate-pulse')} />
          </div>
        </div>

        <div className="mt-3 px-1">
          <div className="text-[10px] text-gray-600 text-center">
            v1.0 · AutoInvestor Intelligence
          </div>
        </div>
      </div>
    </aside>
  )
}
