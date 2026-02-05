import { apiClient } from './api'

export interface QuarantineLog {
  log_id: number
  description?: string
  description_normalized?: string
  source_file_id?: number
  rejection_reason?: string
  quality_score?: number
  matched_forbidden_pattern?: string
  quality_indicators?: string
  created_at?: string
}

export interface QuarantineStats {
  by_reason: Record<string, number>
  total: number
}

export interface ListParams {
  rejection_reason?: string
  source_file_id?: number
  skip?: number
  limit?: number
}

export const quarantineService = {
  list: (params?: ListParams): Promise<QuarantineLog[]> =>
    apiClient.get('/quarantine', { params }).then(res => res.data),

  getStats: (): Promise<QuarantineStats> =>
    apiClient.get('/quarantine/stats').then(res => res.data),

  get: (id: number): Promise<QuarantineLog> =>
    apiClient.get(`/quarantine/${id}`).then(res => res.data),

  delete: (id: number): Promise<{ status: string }> =>
    apiClient.delete(`/quarantine/${id}`).then(res => res.data),

  getReasons: (): Promise<string[]> =>
    apiClient.get('/quarantine/reasons/list').then(res => res.data),

  promoteToPending: (id: number): Promise<{ status: string; pending_id: number }> =>
    apiClient.post(`/quarantine/${id}/promote-to-pending`).then(res => res.data),
}
