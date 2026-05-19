import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// Request interceptor - attach auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string; detail?: string }>) => {
    if (error.response) {
      const status = error.response.status
      const message =
        error.response.data?.message ||
        error.response.data?.detail ||
        'An error occurred'

      if (status === 401) {
        localStorage.removeItem('auth_token')
        toast.error('Session expired. Please log in again.')
      } else if (status === 429) {
        toast.error('Rate limit exceeded. Please wait a moment.')
      } else if (status >= 500) {
        toast.error('Server error. Please try again later.')
      } else if (status !== 404) {
        // Don't toast 404 errors globally, let components handle them
        console.error('API Error:', message)
      }
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message)
    }

    return Promise.reject(error)
  }
)

export default apiClient
