import { configureStore } from '@reduxjs/toolkit'
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux'
import marketReducer from './marketSlice'
import portfolioReducer from './portfolioSlice'
import predictionsReducer from './predictionsSlice'
import settingsReducer from './settingsSlice'

export const store = configureStore({
  reducer: {
    market: marketReducer,
    portfolio: portfolioReducer,
    predictions: predictionsReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector
