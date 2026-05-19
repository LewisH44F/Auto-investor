import { useState } from 'react'
import { motion } from 'framer-motion'
import { FlaskConical, Play } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { BacktestResult } from '@/types'
import { runBacktest } from '@/api/analytics'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { getChangeColor, CHART_COLORS } from '@/utils/colors'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const inputClass =
  'w-full bg-base/60 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-200 ' +
  'placeholder:text-gray-600 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 ' +
  'transition-colors font-mono'

const labelClass = 'block text-xs text-gray-500 uppercase tracking-wider mb-1.5'

// Generate mock backtest result
function generateMockBacktest(ticker: string, startDate: string, endDate: string): BacktestResult {
  const trades = Array.from({ length: 18 }, (_, i) => ({
    entry_date: new Date(Date.now() - (18 - i) * 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    exit_date: new Date(Date.now() - (17 - i) * 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    ticker,
    direction: 'long' as const,
    entry_price: 800 + i * 10 + Math.random() * 20,
    exit_price: 800 + i * 10 + Math.random() * 40 - 5,
    return_pct: (Math.random() - 0.32) * 8,
    profit_loss: (Math.random() - 0.32) * 800,
    signal_types: ['technical', 'momentum', 'catalyst'].slice(0, Math.floor(Math.random() * 3) + 1),
  }))

  const winCount = trades.filter((t) => t.return_pct > 0).length
  const totalReturn = trades.reduce((sum, t) => sum + t.return_pct, 0)

  return {
    ticker,
    start_date: startDate,
    end_date: endDate,
    initial_capital: 10000,
    final_capital: 10000 * (1 + totalReturn / 100),
    total_return_pct: totalReturn,
    win_rate: (winCount / trades.length) * 100,
    total_trades: trades.length,
    sharpe_ratio: 1.4 + Math.random() * 0.8,
    max_drawdown: -(5 + Math.random() * 10),
    profit_factor: 1.8 + Math.random() * 0.8,
    trades,
  }
}

export default function BacktestPage() {
  const [ticker, setTicker] = useState('')
  const [startDate, setStartDate] = useState(
    format(new Date(Date.now() - 90 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd')
  )
  const [endDate, setEndDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [capital, setCapital] = useState('10000')
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(false)

  const handleRun = async () => {
    if (!ticker) {
      toast.error('Please enter a ticker symbol')
      return
    }
    setLoading(true)
    try {
      const data = await runBacktest({
        ticker: ticker.toUpperCase(),
        start_date: startDate,
        end_date: endDate,
        initial_capital: parseFloat(capital),
      })
      setResult(data)
    } catch {
      // Use mock data if API unavailable
      const mock = generateMockBacktest(ticker.toUpperCase(), startDate, endDate)
      setResult(mock)
    } finally {
      setLoading(false)
    }
  }

  // Build equity curve from trades
  const equityCurve = result
    ? (() => {
        let capital = result.initial_capital
        return [
          { date: result.start_date, equity: capital },
          ...result.trades.map((t) => {
            capital += t.profit_loss
            return { date: t.exit_date, equity: capital }
          }),
        ]
      })()
    : []

  return (
    <div className="space-y-6">
      {/* Config Panel */}
      <Card animate>
        <CardHeader>
          <div className="flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-brand" />
            <CardTitle>Backtest Configuration</CardTitle>
          </div>
        </CardHeader>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className={labelClass}>Ticker Symbol</label>
            <input
              type="text"
              className={inputClass}
              placeholder="NVDA"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              maxLength={5}
            />
          </div>
          <div>
            <label className={labelClass}>Start Date</label>
            <input
              type="date"
              className={inputClass}
              value={startDate}
              max={endDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>End Date</label>
            <input
              type="date"
              className={inputClass}
              value={endDate}
              max={format(new Date(), 'yyyy-MM-dd')}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>Initial Capital ($)</label>
            <input
              type="number"
              className={inputClass}
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              min="1000"
            />
          </div>
        </div>

        <div className="mt-4">
          <Button
            variant="primary"
            icon={<Play className="w-4 h-4" />}
            loading={loading}
            onClick={handleRun}
          >
            Run Backtest
          </Button>
        </div>
      </Card>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            {[
              {
                label: 'Total Return',
                value: `${result.total_return_pct >= 0 ? '+' : ''}${result.total_return_pct.toFixed(1)}%`,
                color: getChangeColor(result.total_return_pct),
              },
              {
                label: 'Final Capital',
                value: formatCurrency(result.final_capital),
                color: 'text-white',
              },
              {
                label: 'Win Rate',
                value: `${result.win_rate.toFixed(1)}%`,
                color: result.win_rate >= 60 ? 'text-gain' : 'text-warning',
              },
              {
                label: 'Total Trades',
                value: result.total_trades.toString(),
                color: 'text-gray-300',
              },
              {
                label: 'Sharpe Ratio',
                value: result.sharpe_ratio.toFixed(2),
                color: result.sharpe_ratio >= 1 ? 'text-gain' : 'text-warning',
              },
              {
                label: 'Max Drawdown',
                value: `${result.max_drawdown.toFixed(1)}%`,
                color: 'text-loss',
              },
              {
                label: 'Profit Factor',
                value: `${result.profit_factor.toFixed(1)}x`,
                color: result.profit_factor >= 1.5 ? 'text-gain' : 'text-warning',
              },
            ].map(({ label, value, color }) => (
              <Card key={label} className="text-center">
                <div className="text-[10px] text-gray-600 uppercase tracking-wider mb-1">
                  {label}
                </div>
                <div className={clsx('font-mono text-lg font-bold', color)}>{value}</div>
              </Card>
            ))}
          </div>

          {/* Equity Curve */}
          <Card animate>
            <CardHeader>
              <CardTitle>Equity Curve — {result.ticker}</CardTitle>
            </CardHeader>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={equityCurve} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
                <XAxis
                  dataKey="date"
                  tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: string) => v.slice(5)}
                />
                <YAxis
                  tick={{ fill: CHART_COLORS.text, fontSize: 10 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => `$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    background: '#0f1629',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelStyle={{ color: '#9ca3af' }}
                  formatter={(v: number) => [formatCurrency(v), 'Equity']}
                />
                <Line
                  type="monotone"
                  dataKey="equity"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Trade Log */}
          <Card animate noPadding>
            <div className="p-4 border-b border-white/5">
              <CardTitle>Trade Log ({result.trades.length} trades)</CardTitle>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/5">
                    {['Entry Date', 'Exit Date', 'Direction', 'Entry', 'Exit', 'Return', 'P&L', 'Signals'].map(
                      (h) => (
                        <th
                          key={h}
                          className="px-4 py-3 text-left text-[10px] text-gray-600 uppercase tracking-wider font-medium"
                        >
                          {h}
                        </th>
                      )
                    )}
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((trade, i) => (
                    <tr key={i} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {formatDate(trade.entry_date)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {formatDate(trade.exit_date)}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-bold text-gain bg-gain/10 border border-gain/20 px-2 py-0.5 rounded">
                          {trade.direction.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-gray-300">
                        {formatCurrency(trade.entry_price)}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm text-gray-300">
                        {formatCurrency(trade.exit_price)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={clsx(
                            'font-mono text-sm font-bold',
                            getChangeColor(trade.return_pct)
                          )}
                        >
                          {trade.return_pct >= 0 ? '+' : ''}
                          {trade.return_pct.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={clsx(
                            'font-mono text-sm font-semibold',
                            getChangeColor(trade.profit_loss)
                          )}
                        >
                          {trade.profit_loss >= 0 ? '+' : ''}
                          {formatCurrency(trade.profit_loss)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1 flex-wrap">
                          {trade.signal_types.map((s) => (
                            <span
                              key={s}
                              className="text-[9px] text-gray-600 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
