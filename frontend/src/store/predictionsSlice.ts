import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { Prediction, ModelPerformance } from '@/types'
import { getTonightsPredictions, getModelPerformance } from '@/api/predictions'

interface PredictionsState {
  tonights: Prediction[]
  performance: ModelPerformance | null
  loading: boolean
  error: string | null
  lastFetched: string | null
}

const initialState: PredictionsState = {
  tonights: [],
  performance: null,
  loading: false,
  error: null,
  lastFetched: null,
}

export const fetchTonightsPredictions = createAsyncThunk(
  'predictions/fetchTonights',
  async (_, { rejectWithValue }) => {
    try {
      return await getTonightsPredictions()
    } catch (error) {
      return rejectWithValue('Failed to fetch predictions')
    }
  }
)

export const fetchModelPerformance = createAsyncThunk(
  'predictions/fetchPerformance',
  async (_, { rejectWithValue }) => {
    try {
      return await getModelPerformance()
    } catch (error) {
      return rejectWithValue('Failed to fetch model performance')
    }
  }
)

const predictionsSlice = createSlice({
  name: 'predictions',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setPredictions: (state, action) => {
      state.tonights = action.payload
      state.lastFetched = new Date().toISOString()
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTonightsPredictions.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchTonightsPredictions.fulfilled, (state, action) => {
        state.loading = false
        state.tonights = action.payload
        state.lastFetched = new Date().toISOString()
      })
      .addCase(fetchTonightsPredictions.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchModelPerformance.fulfilled, (state, action) => {
        state.performance = action.payload
      })
  },
})

export const { clearError, setPredictions } = predictionsSlice.actions
export default predictionsSlice.reducer
