import { useState } from 'react'
import { Plus, RefreshCw } from 'lucide-react'
import PortfolioSummary from '@/components/portfolio/PortfolioSummary'
import HoldingCard from '@/components/portfolio/HoldingCard'
import AddHoldingModal from '@/components/portfolio/AddHoldingModal'
import PortfolioAllocationChart from '@/components/charts/PortfolioAllocationChart'
import Button from '@/components/ui/Button'
import Card, { CardTitle } from '@/components/ui/Card'
import {
  useHoldings,
  usePortfolioStats,
  useAddHolding,
  useRemoveHolding,
  useRefreshPrices,
} from '@/hooks/usePortfolio'
import { useTransactions } from '@/hooks/usePortfolio'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { clsx } from 'clsx'

export default function PortfolioPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const { data: holdings, isLoading: holdingsLoading } = useHoldings()
  const { data: stats, isLoading: statsLoading } = usePortfolioStats()
  const { data: transactions } = useTransactions()
  const addHolding = useAddHolding()
  const removeHolding = useRemoveHolding()
  const refreshPrices = useRefreshPrices()

  return (
    <div className="space-y-6">
      {/* Summary */}
      <PortfolioSummary
        stats={stats ?? null}
        isLoading={statsLoading}
        onRefresh={() => refreshPrices.mutate()}
      />

      {/* Holdings + Allocation */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Holdings ({holdings?.length ?? 0})
        </h2>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            icon={<RefreshCw className="w-3.5 h-3.5" />}
            loading={refreshPrices.isPending}
            onClick={() => refreshPrices.mutate()}
          >
            Refresh Prices
          </Button>
          <Button
            variant="primary"
            size="sm"
            icon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setModalOpen(true)}
          >
            Add Holding
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Holdings Grid */}
        <div className="lg:col-span-3">
          {holdingsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-72 bg-surface rounded-xl animate-pulse" />
              ))}
            </div>
          ) : !holdings?.length ? (
            <div className="bg-surface border border-white/5 rounded-xl p-12 text-center">
              <p className="text-gray-600 text-sm">No holdings yet. Add your first position.</p>
              <Button
                variant="primary"
                size="sm"
                className="mt-4"
                icon={<Plus className="w-3.5 h-3.5" />}
                onClick={() => setModalOpen(true)}
              >
                Add Holding
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {holdings.map((holding, i) => (
                <HoldingCard
                  key={holding.id}
                  holding={holding}
                  delay={i}
                  onRemove={(id) => removeHolding.mutate(id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Allocation Chart */}
        <div className="lg:col-span-1 space-y-4">
          {holdings && holdings.length > 0 && (
            <PortfolioAllocationChart holdings={holdings} />
          )}
        </div>
      </div>

      {/* Transaction History */}
      {transactions && transactions.length > 0 && (
        <Card animate noPadding>
          <div className="p-4 border-b border-white/5">
            <CardTitle>Transaction History</CardTitle>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {['Date', 'Ticker', 'Type', 'Shares', 'Price', 'Total'].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-[10px] text-gray-600 uppercase tracking-wider font-medium"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 20).map((tx) => (
                  <tr key={tx.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                    <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                      {formatDate(tx.date)}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm font-bold text-white">
                      {tx.ticker}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'text-xs font-bold px-2 py-0.5 rounded border',
                          tx.type === 'buy'
                            ? 'text-gain bg-gain/10 border-gain/20'
                            : 'text-loss bg-loss/10 border-loss/20'
                        )}
                      >
                        {tx.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm text-gray-300">{tx.shares}</td>
                    <td className="px-4 py-3 font-mono text-sm text-gray-300">
                      {formatCurrency(tx.price)}
                    </td>
                    <td className="px-4 py-3 font-mono text-sm font-semibold text-gray-200">
                      {formatCurrency(tx.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add Holding Modal */}
      <AddHoldingModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={async (data) => {
          await addHolding.mutateAsync(data)
          setModalOpen(false)
        }}
        loading={addHolding.isPending}
      />
    </div>
  )
}
