import { apiClient } from './api'

export interface PendingItem {
  pending_id: number
  description: string
  description_normalized?: string
  sec_code?: string
  unit_standard?: string
  source_file_id?: number
  original_description?: string
  quality_score?: number
  quality_reasons?: string
  quality_indicators?: string
  status: string
  reviewed_by?: number
  reviewed_at?: string
  review_notes?: string
  master_id?: number
  created_at?: string
  updated_at?: string
}

export interface PendingItemStats {
  pending: number
  approved: number
  rejected: number
  total: number
}

export interface ApprovalRequest {
  reviewer_id: number
  notes?: string
}

export interface ApprovalResponse {
  status: string
  master_id?: number
  work_code?: string
}

export interface ListParams {
  status?: string
  min_score?: number
  max_score?: number
  sec_code?: string
  skip?: number
  limit?: number
}

export const pendingItemsService = {
  list: (params?: ListParams): Promise<PendingItem[]> =>
    apiClient.get('/pending-items', { params }).then(res => res.data),

  getStats: (): Promise<PendingItemStats> =>
    apiClient.get('/pending-items/stats').then(res => res.data),

  get: (id: number): Promise<PendingItem> =>
    apiClient.get(`/pending-items/${id}`).then(res => res.data),

  update: (id: number, data: Partial<PendingItem>): Promise<PendingItem> =>
    apiClient.put(`/pending-items/${id}`, data).then(res => res.data),

  approve: (id: number, data: ApprovalRequest): Promise<ApprovalResponse> =>
    apiClient.post(`/pending-items/${id}/approve`, data).then(res => res.data),

  reject: (id: number, data: ApprovalRequest): Promise<{ status: string }> =>
    apiClient.post(`/pending-items/${id}/reject`, data).then(res => res.data),

  bulkApprove: (ids: number[], reviewer_id: number): Promise<{ approved: number; total: number }> =>
    apiClient.post('/pending-items/bulk-approve', { pending_ids: ids, reviewer_id }).then(res => res.data),

  bulkReject: (ids: number[], reviewer_id: number): Promise<{ rejected: number; total: number }> =>
    apiClient.post('/pending-items/bulk-reject', { pending_ids: ids, reviewer_id }).then(res => res.data),
}
