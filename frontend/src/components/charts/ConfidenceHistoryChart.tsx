import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import Card, { CardTitle } from '@/components/ui/Card'
import { CHART_COLORS } from '@/utils/colors'
import { ConfidenceHistory } from '@/types'
import { format, parseISO } from 'date-fns'

interface ConfidenceHistoryChartProps {
  data: ConfidenceHistory[]
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-white/10 rounded-lg p-3 shadow-xl text-xs space-y-1.5">
      <div className="text-gray-400 font-medium mb-2">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center justify-between gap-6">
          <span className="text-gray-500">{p.name}</span>
          <span className="font-mono font-semibold" style={{ color: p.color }}>
            {p.name === 'Confidence' ? `${p.value.toFixed(0)}%` : `${p.value >= 0 ? '+' : ''}${p.value.toFixed(1)}%`}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function ConfidenceHistoryChart({ data }: ConfidenceHistoryChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    date: format(parseISO(d.date), 'MMM d'),
    actualColor: d.actual_return >= 0 ? '#10b981' : '#ef4444',
  }))

  const winRate =
    data.length > 0
      ? ((data.filter((d) => d.was_correct).length / data.length) * 100).toFixed(1)
      : '0'

  return (
    <Card animate noPadding>
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <CardTitle>Confidence vs Outcomes (30 Days)</CardTitle>
        <div className="flex items-center gap-3">
          <div className="text-xs text-gray-500">
            Win Rate:{' '}
            <span className="font-mono font-bold text-gain">{winRate}%</span>
          </div>
        </div>
      </div>

      <div className="p-4">
        <ResponsiveContainer width="100%" height={250}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis
              dataKey="date"
              tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              yAxisId="confidence"
              orientation="left"
              domain={[0, 100]}
              tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `${v}%`}
            />
            <YAxis
              yAxisId="return"
              orientation="right"
              tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine yAxisId="confidence" y={70} stroke="#3b82f6" strokeDasharray="4 2" strokeOpacity={0.4} />
            <ReferenceLine yAxisId="return" y={0} stroke="rgba(255,255,255,0.1)" />

            {/* Actual return bars */}
            <Bar
              yAxisId="return"
              dataKey="actual_return"
              name="Actual Return"
              fill="#10b981"
              radius={[2, 2, 0, 0]}
              fillOpacity={0.7}
            />

            {/* Confidence line */}
            <Line
              yAxisId="confidence"
              type="monotone"
              dataKey="confidence"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 3 }}
              name="Confidence"
            />
          </ComposedChart>
        </ResponsiveContainer>

        <div className="flex items-center gap-4 mt-2">
          {[
            { color: '#3b82f6', label: 'Confidence Score', dash: false },
            { color: '#10b981', label: 'Actual Return %', dash: false },
            { color: '#3b82f680', label: '70% Threshold', dash: true },
          ].map(({ color, label, dash }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div
                className="w-4 h-0.5"
                style={{ background: color, borderTop: dash ? `1px dashed ${color}` : undefined }}
              />
              <span className="text-[10px] text-gray-600">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}
