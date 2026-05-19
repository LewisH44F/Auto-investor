import apiClient from './client'
import { Prediction, ModelPerformance, PaginatedResponse, ConfidenceHistory } from '@/types'

export interface PredictionHistoryParams {
  page?: number
  per_page?: number
  ticker?: string
  start_date?: string
  end_date?: string
  recommendation_type?: string
}

export async function getTonightsPredictions(): Promise<Prediction[]> {
  const response = await apiClient.get<Prediction[]>('/predictions/tonight')
  return response.data
}

export async function getPredictionHistory(
  params: PredictionHistoryParams = {}
): Promise<PaginatedResponse<Prediction>> {
  const response = await apiClient.get<PaginatedResponse<Prediction>>('/predictions/history', {
    params,
  })
  return response.data
}

export async function getPredictionById(id: string): Promise<Prediction> {
  const response = await apiClient.get<Prediction>(`/predictions/${id}`)
  return response.data
}

export async function getModelPerformance(): Promise<ModelPerformance> {
  const response = await apiClient.get<ModelPerformance>('/predictions/performance')
  return response.data
}

export async function triggerManualScan(): Promise<{ message: string; job_id: string }> {
  const response = await apiClient.post<{ message: string; job_id: string }>(
    '/predictions/scan'
  )
  return response.data
}

export async function getConfidenceHistory(days = 30): Promise<ConfidenceHistory[]> {
  const response = await apiClient.get<ConfidenceHistory[]>('/predictions/confidence-history', {
    params: { days },
  })
  return response.data
}
