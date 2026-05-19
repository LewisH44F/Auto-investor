import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import { PIE_COLORS } from '@/utils/colors'
import { formatCurrency } from '@/utils/formatters'
import { Holding } from '@/types'

interface PortfolioAllocationChartProps {
  holdings: Holding[]
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean
  payload?: { name: string; value: number; payload: { pct: number } }[]
}) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <div className="font-mono font-bold text-white mb-1">{payload[0].name}</div>
      <div className="text-gray-400">
        {formatCurrency(payload[0].value)}
        <span className="ml-2 text-gray-600">({payload[0].payload.pct.toFixed(1)}%)</span>
      </div>
    </div>
  )
}

export default function PortfolioAllocationChart({ holdings }: PortfolioAllocationChartProps) {
  const totalValue = holdings.reduce((sum, h) => sum + h.current_price * h.shares, 0)

  const data = holdings.map((h) => ({
    name: h.ticker,
    value: h.current_price * h.shares,
    pct: ((h.current_price * h.shares) / totalValue) * 100,
  }))

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    name,
    pct,
  }: {
    cx: number
    cy: number
    midAngle: number
    innerRadius: number
    outerRadius: number
    name: string
    pct: number
  }) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    if (pct < 8) return null

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={10}
        fontWeight="bold"
        fontFamily="JetBrains Mono, monospace"
      >
        {name}
      </text>
    )
  }

  return (
    <Card animate>
      <CardHeader>
        <CardTitle>Allocation</CardTitle>
      </CardHeader>

      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={3}
            dataKey="value"
            labelLine={false}
            label={renderCustomLabel}
          >
            {data.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={PIE_COLORS[index % PIE_COLORS.length]}
                stroke="rgba(0,0,0,0.3)"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="grid grid-cols-2 gap-1.5 mt-2">
        {data.map((entry, i) => (
          <div key={entry.name} className="flex items-center gap-2">
            <div
              className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
              style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}
            />
            <span className="text-xs text-gray-400 font-mono">{entry.name}</span>
            <span className="text-xs text-gray-600 ml-auto font-mono">
              {entry.pct.toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </Card>
  )
}
