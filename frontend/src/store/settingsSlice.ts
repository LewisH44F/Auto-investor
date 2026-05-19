import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { AppSettings } from '@/types'

const defaultSettings: AppSettings = {
  confidence_threshold: 70,
  risk_tolerance: 'moderate',
  trading_profile: 'swing_trader',
  notifications: {
    email_enabled: false,
    discord_enabled: false,
    telegram_enabled: false,
    notify_on_picks: true,
    notify_on_alerts: true,
  },
  api_keys: {},
}

interface SettingsState {
  settings: AppSettings
  saving: boolean
}

const initialState: SettingsState = {
  settings: defaultSettings,
  saving: false,
}

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    updateSettings: (state, action: PayloadAction<Partial<AppSettings>>) => {
      state.settings = { ...state.settings, ...action.payload }
    },
    updateConfidenceThreshold: (state, action: PayloadAction<number>) => {
      state.settings.confidence_threshold = action.payload
    },
    updateRiskTolerance: (
      state,
      action: PayloadAction<AppSettings['risk_tolerance']>
    ) => {
      state.settings.risk_tolerance = action.payload
    },
    updateNotifications: (
      state,
      action: PayloadAction<Partial<AppSettings['notifications']>>
    ) => {
      state.settings.notifications = {
        ...state.settings.notifications,
        ...action.payload,
      }
    },
    setSaving: (state, action: PayloadAction<boolean>) => {
      state.saving = action.payload
    },
    loadSettings: (state, action: PayloadAction<AppSettings>) => {
      state.settings = action.payload
    },
  },
})

export const {
  updateSettings,
  updateConfidenceThreshold,
  updateRiskTolerance,
  updateNotifications,
  setSaving,
  loadSettings,
} = settingsSlice.actions
export default settingsSlice.reducer
