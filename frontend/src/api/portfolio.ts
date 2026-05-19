import apiClient from './client'
import { Holding, PortfolioStats, Transaction, AddHoldingForm } from '@/types'

export async function getHoldings(): Promise<Holding[]> {
  const response = await apiClient.get<Holding[]>('/portfolio/holdings')
  return response.data
}

export async function getPortfolioStats(): Promise<PortfolioStats> {
  const response = await apiClient.get<PortfolioStats>('/portfolio/stats')
  return response.data
}

export async function addHolding(data: AddHoldingForm): Promise<Holding> {
  const response = await apiClient.post<Holding>('/portfolio/holdings', data)
  return response.data
}

export async function updateHolding(
  id: string,
  data: Partial<AddHoldingForm>
): Promise<Holding> {
  const response = await apiClient.patch<Holding>(`/portfolio/holdings/${id}`, data)
  return response.data
}

export async function removeHolding(id: string): Promise<void> {
  await apiClient.delete(`/portfolio/holdings/${id}`)
}

export async function getTransactions(holdingId?: string): Promise<Transaction[]> {
  const response = await apiClient.get<Transaction[]>('/portfolio/transactions', {
    params: holdingId ? { holding_id: holdingId } : undefined,
  })
  return response.data
}

export async function refreshHoldingPrices(): Promise<void> {
  await apiClient.post('/portfolio/refresh-prices')
}
