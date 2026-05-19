import { Shield, AlertTriangle, TrendingDown } from 'lucide-react'
import { motion } from 'framer-motion'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

interface NoTradeDayProps {
  reason?: string
  marketCondition?: string
}

export default function NoTradeDay({ reason, marketCondition = 'VOLATILE' }: NoTradeDayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="flex flex-col items-center justify-center py-12 text-center relative overflow-hidden">
        {/* Background subtle pattern */}
        <div
          className="absolute inset-0 opacity-[0.03] pointer-events-none"
          style={{
            backgroundImage: `repeating-linear-gradient(
              45deg,
              transparent,
              transparent 10px,
              rgba(255,255,255,0.5) 10px,
              rgba(255,255,255,0.5) 11px
            )`,
          }}
        />

        {/* Shield Icon */}
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-full bg-gray-700/30 border border-gray-600/30 flex items-center justify-center">
            <Shield className="w-10 h-10 text-gray-500" />
          </div>
          <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-warning/20 border border-warning/30 flex items-center justify-center">
            <AlertTriangle className="w-3.5 h-3.5 text-warning" />
          </div>
        </div>

        <h2 className="text-xl font-bold text-white mb-2">
          No Strong Setup Detected
        </h2>
        <p className="text-sm text-gray-500 mb-1">
          for tomorrow's trading session
        </p>

        <div className="flex items-center gap-2 my-4">
          <Badge variant="warning" size="sm" dot>
            {marketCondition}
          </Badge>
          <Badge variant="default" size="sm">
            CAPITAL PRESERVATION MODE
          </Badge>
        </div>

        <p className="text-sm text-gray-400 max-w-sm leading-relaxed mb-6">
          {reason ||
            'The AI system requires a minimum confidence threshold of 70% before recommending a position. Current market conditions do not present a high-probability setup.'}
        </p>

        {/* Philosophy quote */}
        <div className="bg-base/60 border border-white/5 rounded-lg px-6 py-4 max-w-sm">
          <div className="flex items-center justify-center gap-2 mb-2">
            <TrendingDown className="w-4 h-4 text-gray-600" />
            <span className="text-xs text-gray-600 uppercase tracking-wider">
              Market Wisdom
            </span>
          </div>
          <p className="text-xs text-gray-500 italic leading-relaxed">
            "Protecting capital is a valid — and often the best — trade decision.
            The best traders know when not to trade."
          </p>
        </div>

        {/* Conditions */}
        <div className="grid grid-cols-3 gap-4 mt-6 w-full max-w-sm">
          {[
            { label: 'VIX', value: 'Elevated', color: 'text-warning' },
            { label: 'Setups', value: '0 / 50', color: 'text-gray-400' },
            { label: 'Next Scan', value: '6:00 PM', color: 'text-brand' },
          ].map(({ label, value, color }) => (
            <div key={label} className="text-center">
              <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
                {label}
              </div>
              <div className={`text-sm font-mono font-semibold ${color}`}>{value}</div>
            </div>
          ))}
        </div>
      </Card>
    </motion.div>
  )
}
