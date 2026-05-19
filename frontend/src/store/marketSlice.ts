import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { MarketOverview } from '@/types'
import { getMarketOverview } from '@/api/sentiment'

interface MarketState {
  overview: MarketOverview | null
  loading: boolean
  error: string | null
  lastUpdated: string | null
}

const initialState: MarketState = {
  overview: null,
  loading: false,
  error: null,
  lastUpdated: null,
}

export const fetchMarketOverview = createAsyncThunk(
  'market/fetchOverview',
  async (_, { rejectWithValue }) => {
    try {
      return await getMarketOverview()
    } catch (error) {
      return rejectWithValue('Failed to fetch market overview')
    }
  }
)

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setOverview: (state, action) => {
      state.overview = action.payload
      state.lastUpdated = new Date().toISOString()
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMarketOverview.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchMarketOverview.fulfilled, (state, action) => {
        state.loading = false
        state.overview = action.payload
        state.lastUpdated = new Date().toISOString()
      })
      .addCase(fetchMarketOverview.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  },
})

export const { setOverview, clearError } = marketSlice.actions
export default marketSlice.reducer
