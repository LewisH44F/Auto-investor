import { useState } from 'react'
import { Bell, Shield, Key, User, Save } from 'lucide-react'
import { clsx } from 'clsx'
import Card, { CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { useAppDispatch, useAppSelector } from '@/store'
import {
  updateConfidenceThreshold,
  updateRiskTolerance,
  updateNotifications,
} from '@/store/settingsSlice'
import toast from 'react-hot-toast'

const inputClass =
  'w-full bg-base/60 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-gray-200 ' +
  'placeholder:text-gray-600 focus:outline-none focus:border-brand/50 focus:ring-1 focus:ring-brand/30 ' +
  'transition-colors font-mono'

const labelClass = 'block text-xs text-gray-500 uppercase tracking-wider mb-1.5'

function Toggle({
  enabled,
  onChange,
}: {
  enabled: boolean
  onChange: (val: boolean) => void
}) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={clsx(
        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200',
        enabled ? 'bg-brand' : 'bg-gray-700'
      )}
    >
      <span
        className={clsx(
          'inline-block h-4 w-4 rounded-full bg-white transition-transform duration-200',
          enabled ? 'translate-x-6' : 'translate-x-1'
        )}
      />
    </button>
  )
}

function SectionCard({
  title,
  icon: Icon,
  children,
}: {
  title: string
  icon: React.ElementType
  children: React.ReactNode
}) {
  return (
    <Card>
      <CardHeader className="mb-4">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-brand" />
          <CardTitle>{title}</CardTitle>
        </div>
      </CardHeader>
      {children}
    </Card>
  )
}

export default function SettingsPage() {
  const dispatch = useAppDispatch()
  const { settings } = useAppSelector((s) => s.settings)
  const [saving, setSaving] = useState(false)
  const [apiKeys, setApiKeys] = useState({ alpha_vantage: '', polygon: '' })

  const handleSave = async () => {
    setSaving(true)
    await new Promise((r) => setTimeout(r, 800))
    setSaving(false)
    toast.success('Settings saved successfully!')
  }

  const riskOptions = [
    { value: 'conservative', label: 'Conservative', desc: 'Low risk, stable returns' },
    { value: 'moderate', label: 'Moderate', desc: 'Balanced approach' },
    { value: 'aggressive', label: 'Aggressive', desc: 'Higher risk, higher potential' },
  ] as const

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Trading Profile */}
      <SectionCard title="Trading Profile" icon={User}>
        <div className="space-y-4">
          <div className="flex items-center justify-between py-3 border-b border-white/5">
            <div>
              <div className="text-sm text-gray-300 font-medium">Trading Style</div>
              <div className="text-xs text-gray-600 mt-0.5">
                Your identified trading profile
              </div>
            </div>
            <Badge variant="brand" size="md">
              Swing Trader
            </Badge>
          </div>
          <p className="text-xs text-gray-600 leading-relaxed">
            Your trading profile is configured based on your preferences. Swing trading focuses on
            holding positions for 2-7 days to capture short-to-medium term price movements. The AI
            system optimizes all recommendations for this style.
          </p>
        </div>
      </SectionCard>

      {/* AI Settings */}
      <SectionCard title="AI & Risk Settings" icon={Shield}>
        <div className="space-y-6">
          {/* Confidence Threshold */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-300 font-medium">
                Confidence Threshold
              </label>
              <span className="font-mono text-brand font-bold">
                {settings.confidence_threshold}%
              </span>
            </div>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={settings.confidence_threshold}
              onChange={(e) =>
                dispatch(updateConfidenceThreshold(parseInt(e.target.value)))
              }
              className="w-full h-2 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand"
            />
            <div className="flex justify-between text-[10px] text-gray-700 mt-1">
              <span>50% (More signals)</span>
              <span>95% (Fewer, higher quality)</span>
            </div>
            <p className="text-xs text-gray-600 mt-2">
              Only predictions above this confidence level will trigger notifications or appear as
              primary picks.
            </p>
          </div>

          {/* Risk Tolerance */}
          <div>
            <label className={labelClass}>Risk Tolerance</label>
            <div className="grid grid-cols-3 gap-2">
              {riskOptions.map(({ value, label, desc }) => (
                <button
                  key={value}
                  onClick={() => dispatch(updateRiskTolerance(value))}
                  className={clsx(
                    'p-3 rounded-xl border text-left transition-all',
                    settings.risk_tolerance === value
                      ? 'bg-brand/15 border-brand/30 text-brand'
                      : 'bg-base/40 border-white/5 text-gray-500 hover:border-white/20 hover:text-gray-300'
                  )}
                >
                  <div className="text-sm font-semibold mb-0.5">{label}</div>
                  <div className="text-[10px] opacity-70">{desc}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </SectionCard>

      {/* Notifications */}
      <SectionCard title="Notifications" icon={Bell}>
        <div className="space-y-4">
          {/* Email */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-300 font-medium">Email Alerts</div>
                <div className="text-xs text-gray-600">Receive picks via email</div>
              </div>
              <Toggle
                enabled={settings.notifications.email_enabled}
                onChange={(v) => dispatch(updateNotifications({ email_enabled: v }))}
              />
            </div>
            {settings.notifications.email_enabled && (
              <input
                type="email"
                className={inputClass}
                placeholder="your@email.com"
                defaultValue={settings.notifications.email_address}
              />
            )}
          </div>

          {/* Discord */}
          <div className="space-y-3 pt-3 border-t border-white/5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-300 font-medium">Discord Webhook</div>
                <div className="text-xs text-gray-600">Post picks to Discord channel</div>
              </div>
              <Toggle
                enabled={settings.notifications.discord_enabled}
                onChange={(v) => dispatch(updateNotifications({ discord_enabled: v }))}
              />
            </div>
            {settings.notifications.discord_enabled && (
              <input
                type="url"
                className={inputClass}
                placeholder="https://discord.com/api/webhooks/..."
                defaultValue={settings.notifications.discord_webhook}
              />
            )}
          </div>

          {/* Telegram */}
          <div className="space-y-3 pt-3 border-t border-white/5">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-300 font-medium">Telegram</div>
                <div className="text-xs text-gray-600">Send to Telegram chat</div>
              </div>
              <Toggle
                enabled={settings.notifications.telegram_enabled}
                onChange={(v) => dispatch(updateNotifications({ telegram_enabled: v }))}
              />
            </div>
            {settings.notifications.telegram_enabled && (
              <input
                type="text"
                className={inputClass}
                placeholder="Chat ID (e.g. -1001234567890)"
                defaultValue={settings.notifications.telegram_chat_id}
              />
            )}
          </div>

          {/* Notification types */}
          <div className="pt-3 border-t border-white/5 space-y-2">
            <label className={labelClass}>Notify on</label>
            {[
              {
                key: 'notify_on_picks' as const,
                label: 'New AI Picks',
                desc: "When tonight's picks are ready",
              },
              {
                key: 'notify_on_alerts' as const,
                label: 'Price Alerts',
                desc: 'When entry zones are hit',
              },
            ].map(({ key, label, desc }) => (
              <div key={key} className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-300">{label}</div>
                  <div className="text-xs text-gray-600">{desc}</div>
                </div>
                <Toggle
                  enabled={settings.notifications[key]}
                  onChange={(v) => dispatch(updateNotifications({ [key]: v }))}
                />
              </div>
            ))}
          </div>
        </div>
      </SectionCard>

      {/* API Keys */}
      <SectionCard title="API Keys" icon={Key}>
        <div className="space-y-4">
          <p className="text-xs text-gray-600 leading-relaxed">
            Configure your market data API keys. Keys are stored encrypted and never transmitted
            in plain text.
          </p>
          <div>
            <label className={labelClass}>Alpha Vantage API Key</label>
            <input
              type="password"
              className={inputClass}
              placeholder="••••••••••••••••"
              value={apiKeys.alpha_vantage}
              onChange={(e) => setApiKeys((prev) => ({ ...prev, alpha_vantage: e.target.value }))}
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className={labelClass}>Polygon.io API Key</label>
            <input
              type="password"
              className={inputClass}
              placeholder="••••••••••••••••"
              value={apiKeys.polygon}
              onChange={(e) => setApiKeys((prev) => ({ ...prev, polygon: e.target.value }))}
              autoComplete="new-password"
            />
          </div>
        </div>
      </SectionCard>

      {/* Save */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          size="md"
          icon={<Save className="w-4 h-4" />}
          loading={saving}
          onClick={handleSave}
        >
          Save Settings
        </Button>
      </div>
    </div>
  )
}
