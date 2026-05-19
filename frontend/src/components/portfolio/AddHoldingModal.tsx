import { useState } from 'react'
import Modal from '@/components/ui/Modal'
import Button from '@/components/ui/Button'
import { AddHoldingForm } from '@/types'
import { clsx } from 'clsx'
import { format } from 'date-fns'

interface AddHoldingModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: AddHoldingForm) => Promise<void>
  loading?: boolean
}

const inputClass =
  'w-full bg-base/60 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-200 ' +
  'placeholder:text-gray-600 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 ' +
  'transition-colors font-mono'

const labelClass = 'block text-xs text-gray-500 uppercase tracking-wider mb-1.5'

export default function AddHoldingModal({
  open,
  onClose,
  onSubmit,
  loading = false,
}: AddHoldingModalProps) {
  const [form, setForm] = useState<AddHoldingForm>({
    ticker: '',
    shares: 0,
    purchase_price: 0,
    purchase_date: format(new Date(), 'yyyy-MM-dd'),
    notes: '',
  })
  const [errors, setErrors] = useState<Partial<Record<keyof AddHoldingForm, string>>>({})

  const update = <K extends keyof AddHoldingForm>(key: K, value: AddHoldingForm[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }))
    }
  }

  const validate = (): boolean => {
    const newErrors: Partial<Record<keyof AddHoldingForm, string>> = {}
    if (!form.ticker.trim()) newErrors.ticker = 'Ticker is required'
    if (form.shares <= 0) newErrors.shares = 'Shares must be greater than 0'
    if (form.purchase_price <= 0) newErrors.purchase_price = 'Purchase price must be greater than 0'
    if (!form.purchase_date) newErrors.purchase_date = 'Purchase date is required'
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    await onSubmit({ ...form, ticker: form.ticker.toUpperCase() })
    setForm({
      ticker: '',
      shares: 0,
      purchase_price: 0,
      purchase_date: format(new Date(), 'yyyy-MM-dd'),
      notes: '',
    })
  }

  return (
    <Modal open={open} onClose={onClose} title="Add New Holding" size="md">
      <form onSubmit={handleSubmit} className="p-6 space-y-4">
        {/* Ticker */}
        <div>
          <label className={labelClass}>Ticker Symbol</label>
          <input
            type="text"
            className={clsx(inputClass, errors.ticker && 'border-loss/50')}
            placeholder="e.g. NVDA"
            value={form.ticker}
            onChange={(e) => update('ticker', e.target.value.toUpperCase())}
            maxLength={5}
            autoFocus
          />
          {errors.ticker && (
            <p className="text-xs text-loss mt-1">{errors.ticker}</p>
          )}
        </div>

        {/* Shares + Price */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Shares</label>
            <input
              type="number"
              step="0.001"
              min="0"
              className={clsx(inputClass, errors.shares && 'border-loss/50')}
              placeholder="0"
              value={form.shares || ''}
              onChange={(e) => update('shares', parseFloat(e.target.value) || 0)}
            />
            {errors.shares && (
              <p className="text-xs text-loss mt-1">{errors.shares}</p>
            )}
          </div>
          <div>
            <label className={labelClass}>Purchase Price ($)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              className={clsx(inputClass, errors.purchase_price && 'border-loss/50')}
              placeholder="0.00"
              value={form.purchase_price || ''}
              onChange={(e) => update('purchase_price', parseFloat(e.target.value) || 0)}
            />
            {errors.purchase_price && (
              <p className="text-xs text-loss mt-1">{errors.purchase_price}</p>
            )}
          </div>
        </div>

        {/* Total Cost Preview */}
        {form.shares > 0 && form.purchase_price > 0 && (
          <div className="flex justify-between items-center py-2 px-3 bg-brand/8 border border-brand/15 rounded-lg">
            <span className="text-xs text-gray-500">Total Cost</span>
            <span className="font-mono text-sm font-bold text-brand">
              ${(form.shares * form.purchase_price).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </span>
          </div>
        )}

        {/* Purchase Date */}
        <div>
          <label className={labelClass}>Purchase Date</label>
          <input
            type="date"
            className={clsx(inputClass, errors.purchase_date && 'border-loss/50')}
            value={form.purchase_date}
            max={format(new Date(), 'yyyy-MM-dd')}
            onChange={(e) => update('purchase_date', e.target.value)}
          />
          {errors.purchase_date && (
            <p className="text-xs text-loss mt-1">{errors.purchase_date}</p>
          )}
        </div>

        {/* Notes */}
        <div>
          <label className={labelClass}>Notes (optional)</label>
          <textarea
            className={clsx(inputClass, 'resize-none h-20')}
            placeholder="Why did you buy? Any relevant context..."
            value={form.notes}
            onChange={(e) => update('notes', e.target.value)}
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <Button
            type="button"
            variant="secondary"
            fullWidth
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            fullWidth
            loading={loading}
          >
            Add Holding
          </Button>
        </div>
      </form>
    </Modal>
  )
}
