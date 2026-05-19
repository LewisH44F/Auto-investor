import { useState, useMemo } from 'react'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush,
  ReferenceLine,
  ReferenceArea,
} from 'recharts'
import { clsx } from 'clsx'
import Card, { CardTitle } from '@/components/ui/Card'
import { CHART_COLORS } from '@/utils/colors'
import { formatCurrency, formatVolume } from '@/utils/formatters'
import { ChartDataPoint } from '@/types'
import { SpinnerOverlay } from '@/components/ui/Spinner'

// Generate mock price history
function generateMockData(_ticker: string, period: PeriodKey): ChartDataPoint[] {
  const periodDays = { '1D': 1, '5D': 5, '1M': 21, '3M': 63, '1Y': 252 }
  const days = periodDays[period]
  const points: ChartDataPoint[] = []
  let price = 883.25

  const now = new Date()
  for (let i = days; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const change = (Math.random() - 0.48) * price * 0.025
    const open = price
    const close = price + change
    const high = Math.max(open, close) + Math.random() * price * 0.01
    const low = Math.min(open, close) - Math.random() * price * 0.01
    const volume = 20_000_000 + Math.random() * 30_000_000

    points.push({
      date: date.toISOString().split('T')[0],
      open,
      high,
      low,
      close,
      volume,
    })
    price = close
  }
  return points
}

type PeriodKey = '1D' | '5D' | '1M' | '3M' | '1Y'

// Calculate EMA
function calcEMA(data: number[], period: number): (number | null)[] {
  const k = 2 / (period + 1)
  const result: (number | null)[] = []
  let ema = data[0]

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else if (i === period - 1) {
      ema = data.slice(0, period).reduce((a, b) => a + b, 0) / period
      result.push(ema)
    } else {
      ema = data[i] * k + ema * (1 - k)
      result.push(ema)
    }
  }
  return result
}

interface PriceChartProps {
  ticker: string
  entryLow?: number
  entryHigh?: number
  stopLoss?: number
  target1?: number
  isLoading?: boolean
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
    <div className="bg-surface border border-white/10 rounded-lg p-3 shadow-xl text-xs">
      <div className="text-gray-400 mb-2 font-medium">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 justify-between gap-6">
          <span className="text-gray-500">{p.name}</span>
          <span className="font-mono font-semibold" style={{ color: p.color }}>
            {p.name === 'Volume'
              ? formatVolume(p.value)
              : formatCurrency(p.value)}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function PriceChart({
  ticker,
  entryLow,
  entryHigh,
  stopLoss,
  target1,
  isLoading,
}: PriceChartProps) {
  const [period, setPeriod] = useState<PeriodKey>('1M')
  const PERIODS: PeriodKey[] = ['1D', '5D', '1M', '3M', '1Y']

  const rawData = useMemo(() => generateMockData(ticker, period), [ticker, period])

  const chartData = useMemo(() => {
    const closes = rawData.map((d) => d.close)
    const ema21 = calcEMA(closes, 21)
    const ema50 = calcEMA(closes, 50)

    return rawData.map((d, i) => ({
      ...d,
      ema21: ema21[i],
      ema50: ema50[i],
      volumeColor: d.close >= d.open ? CHART_COLORS.gain : CHART_COLORS.loss,
    }))
  }, [rawData])

  if (isLoading) {
    return (
      <Card>
        <SpinnerOverlay message="Loading chart..." />
      </Card>
    )
  }

  return (
    <Card noPadding animate>
      <div className="p-4 flex items-center justify-between border-b border-white/5">
        <CardTitle>{ticker} Price Chart</CardTitle>
        <div className="flex gap-0.5">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={clsx(
                'px-2.5 py-1 text-xs font-medium rounded-md transition-all',
                period === p
                  ? 'bg-brand/20 text-brand border border-brand/30'
                  : 'text-gray-600 hover:text-gray-300 hover:bg-white/5'
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="p-2">
        {/* Main price chart */}
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
            <XAxis
              dataKey="date"
              tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: string) =>
                period === '1D' ? v.slice(11, 16) : v.slice(5)
              }
            />
            <YAxis
              yAxisId="price"
              orientation="right"
              tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${v.toFixed(0)}`}
              domain={['auto', 'auto']}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Entry zone overlay */}
            {entryLow && entryHigh && (
              <ReferenceArea
                yAxisId="price"
                y1={entryLow}
                y2={entryHigh}
                fill="#3b82f6"
                fillOpacity={0.08}
                stroke="#3b82f6"
                strokeOpacity={0.3}
                strokeDasharray="4 2"
              />
            )}

            {/* Stop loss line */}
            {stopLoss && (
              <ReferenceLine
                yAxisId="price"
                y={stopLoss}
                stroke="#ef4444"
                strokeDasharray="4 2"
                strokeOpacity={0.7}
                label={{ value: 'SL', fill: '#ef4444', fontSize: 9, position: 'right' }}
              />
            )}

            {/* Target 1 line */}
            {target1 && (
              <ReferenceLine
                yAxisId="price"
                y={target1}
                stroke="#10b981"
                strokeDasharray="4 2"
                strokeOpacity={0.7}
                label={{ value: 'T1', fill: '#10b981', fontSize: 9, position: 'right' }}
              />
            )}

            {/* EMA 21 */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="ema21"
              stroke={CHART_COLORS.ema21}
              strokeWidth={1.5}
              dot={false}
              name="EMA 21"
              connectNulls
            />

            {/* EMA 50 */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="ema50"
              stroke={CHART_COLORS.ema50}
              strokeWidth={1.5}
              strokeDasharray="5 3"
              dot={false}
              name="EMA 50"
              connectNulls
            />

            {/* Close price line */}
            <Line
              yAxisId="price"
              type="monotone"
              dataKey="close"
              stroke="#ffffff"
              strokeWidth={2}
              dot={false}
              name="Price"
            />

            <Brush
              dataKey="date"
              height={20}
              stroke="rgba(255,255,255,0.1)"
              fill="#0a0e1a"
              travellerWidth={4}
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Volume chart */}
        <ResponsiveContainer width="100%" height={60}>
          <ComposedChart data={chartData} margin={{ top: 0, right: 10, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" hide />
            <YAxis hide domain={['auto', 'auto']} />
            <Bar dataKey="volume" name="Volume" fill={CHART_COLORS.volume} radius={[1, 1, 0, 0]} />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex items-center gap-4 px-4 pb-2 mt-1">
          {[
            { label: 'Price', color: '#ffffff', dash: false },
            { label: 'EMA 21', color: CHART_COLORS.ema21, dash: false },
            { label: 'EMA 50', color: CHART_COLORS.ema50, dash: true },
          ].map(({ label, color, dash }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div
                className="w-5 h-0.5"
                style={{
                  background: color,
                  borderTop: dash ? `1px dashed ${color}` : `1px solid ${color}`,
                  height: 1,
                }}
              />
              <span className="text-[10px] text-gray-600">{label}</span>
            </div>
          ))}
          {entryLow && entryHigh && (
            <div className="flex items-center gap-1.5">
              <div className="w-5 h-3 bg-brand/20 border border-brand/40 rounded-sm" />
              <span className="text-[10px] text-gray-600">Entry Zone</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
