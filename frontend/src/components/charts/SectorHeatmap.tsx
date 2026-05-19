import { motion } from 'framer-motion'
import { clsx } from 'clsx'
import Card, { CardTitle } from '@/components/ui/Card'
import { getSectorColor, getChangeColor } from '@/utils/colors'
import { useMarketOverview } from '@/hooks/useMarketData'

const SECTOR_NAMES: Record<string, string> = {
  XLK: 'Technology',
  XLF: 'Financials',
  XLE: 'Energy',
  XLV: 'Healthcare',
  XLY: 'Cons. Disc.',
  XLP: 'Cons. Stap.',
  XLI: 'Industrials',
  XLU: 'Utilities',
  XLRE: 'Real Estate',
  XLB: 'Materials',
  XLC: 'Comm. Svc.',
}

export default function SectorHeatmap() {
  const { data: market } = useMarketOverview()
  const sectors = market?.trending_sectors ?? []

  const sorted = [...sectors].sort((a, b) => b.change_pct - a.change_pct)

  return (
    <Card animate noPadding>
      <div className="p-4 border-b border-white/5">
        <CardTitle>Sector Heatmap</CardTitle>
      </div>
      <div className="p-3">
        <div className="grid grid-cols-3 gap-2">
          {sorted.map((sector, i) => (
            <motion.div
              key={sector.ticker}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: i * 0.04 }}
              className="relative rounded-xl p-3 flex flex-col cursor-default overflow-hidden"
              style={{
                background: getSectorColor(sector.change_pct),
                border: `1px solid ${
                  sector.change_pct > 0
                    ? 'rgba(16,185,129,0.2)'
                    : sector.change_pct < 0
                    ? 'rgba(239,68,68,0.2)'
                    : 'rgba(255,255,255,0.05)'
                }`,
              }}
            >
              <div className="font-mono text-xs font-bold text-white/90 mb-1">
                {sector.ticker}
              </div>
              <div className="text-[10px] text-white/50 mb-2 leading-tight">
                {sector.name || SECTOR_NAMES[sector.ticker] || sector.ticker}
              </div>
              <div
                className={clsx(
                  'font-mono text-sm font-black',
                  getChangeColor(sector.change_pct)
                )}
              >
                {sector.change_pct >= 0 ? '+' : ''}
                {sector.change_pct.toFixed(2)}%
              </div>
            </motion.div>
          ))}
        </div>

        {/* Scale legend */}
        <div className="flex items-center justify-between mt-4 px-1">
          <div className="flex items-center gap-1">
            <div className="w-12 h-2 rounded-l-full bg-gradient-to-r from-red-600/80 to-red-400/40" />
            <div className="w-6 h-2 bg-gray-700/40" />
            <div className="w-12 h-2 rounded-r-full bg-gradient-to-r from-green-400/40 to-green-600/80" />
          </div>
          <div className="flex gap-4 text-[9px] text-gray-700">
            <span>-3%+</span>
            <span>Flat</span>
            <span>+3%+</span>
          </div>
        </div>
      </div>
    </Card>
  )
}
