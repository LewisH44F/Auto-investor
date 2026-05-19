import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { CHART_COLORS } from '@/utils/colors'
import { ModelPerformance } from '@/types'

interface SignalPerformanceProps {
  performance: ModelPerformance | null
}

const SIGNAL_LABELS: Record<string, string> = {
  technical: 'Technical',
  sentiment: 'Sentiment',
  catalyst: 'Catalyst',
  volume: 'Volume',
  momentum: 'Momentum',
  macro: 'Macro',
}

const SIGNAL_COLORS: Record<string, string> = {
  technical: '#3b82f6',
  sentiment: '#8b5cf6',
  catalyst: '#f59e0b',
  volume: '#06b6d4',
  momentum: '#10b981',
  macro: '#6b7280',
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { value: number }[]
  label?: string
}) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <div className="text-gray-300 font-semibold mb-1">{label}</div>
      <div className="text-gray-400">
        Weight:{' '}
        <span className="font-mono font-bold text-white">
          {(payload[0].value * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}

export default function SignalPerformance({ performance }: SignalPerformanceProps) {
  if (!performance) return null

  const data = Object.entries(performance.signal_weights).map(([key, weight]) => ({
    name: SIGNAL_LABELS[key] || key,
    key,
    weight,
    pct: weight * 100,
  }))

  return (
    <Card animate>
      <CardHeader>
        <CardTitle>Signal Weights</CardTitle>
        <span className="text-xs text-gray-600">AI model factor weights</span>
      </CardHeader>

      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            dataKey="name"
            tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="weight" radius={[4, 4, 0, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.key}
                fill={SIGNAL_COLORS[entry.key] || '#3b82f6'}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="grid grid-cols-3 gap-2 mt-2">
        {data.map((entry) => (
          <div key={entry.key} className="flex items-center gap-1.5">
            <div
              className="w-2.5 h-2.5 rounded-sm"
              style={{ background: SIGNAL_COLORS[entry.key] || '#3b82f6' }}
            />
            <span className="text-[10px] text-gray-500">{entry.name}</span>
            <span className="text-[10px] text-gray-700 ml-auto font-mono">
              {entry.pct.toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}
