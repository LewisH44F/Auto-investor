import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { Holding, PortfolioStats } from '@/types'
import { getHoldings, getPortfolioStats } from '@/api/portfolio'

interface PortfolioState {
  holdings: Holding[]
  stats: PortfolioStats | null
  loading: boolean
  error: string | null
}

const initialState: PortfolioState = {
  holdings: [],
  stats: null,
  loading: false,
  error: null,
}

export const fetchHoldings = createAsyncThunk(
  'portfolio/fetchHoldings',
  async (_, { rejectWithValue }) => {
    try {
      return await getHoldings()
    } catch (error) {
      return rejectWithValue('Failed to fetch holdings')
    }
  }
)

export const fetchPortfolioStats = createAsyncThunk(
  'portfolio/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      return await getPortfolioStats()
    } catch (error) {
      return rejectWithValue('Failed to fetch portfolio stats')
    }
  }
)

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    addHolding: (state, action) => {
      state.holdings.push(action.payload)
    },
    removeHolding: (state, action) => {
      state.holdings = state.holdings.filter((h) => h.id !== action.payload)
    },
    updateHolding: (state, action) => {
      const index = state.holdings.findIndex((h) => h.id === action.payload.id)
      if (index !== -1) {
        state.holdings[index] = action.payload
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHoldings.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchHoldings.fulfilled, (state, action) => {
        state.loading = false
        state.holdings = action.payload
      })
      .addCase(fetchHoldings.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchPortfolioStats.fulfilled, (state, action) => {
        state.stats = action.payload
      })
  },
})

export const { addHolding, removeHolding, updateHolding, clearError } = portfolioSlice.actions
export default portfolioSlice.reducer
