import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { store } from '@/store'
import Layout from '@/components/layout/Layout'
import DashboardPage from '@/pages/DashboardPage'
import PortfolioPage from '@/pages/PortfolioPage'
import PicksPage from '@/pages/PicksPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import BacktestPage from '@/pages/BacktestPage'
import SettingsPage from '@/pages/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      retryDelay: 2000,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
    mutations: {
      retry: 0,
    },
  },
})

export default function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="picks" element={<PicksPage />} />
              <Route path="portfolio" element={<PortfolioPage />} />
              <Route path="analytics" element={<AnalyticsPage />} />
              <Route path="backtest" element={<BacktestPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Routes>
        </BrowserRouter>

        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: '#0f1629',
              color: '#e5e7eb',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '12px',
              fontSize: '13px',
              fontFamily: 'Inter, sans-serif',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#0f1629',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#0f1629',
              },
            },
          }}
        />
      </QueryClientProvider>
    </Provider>
  )
}
