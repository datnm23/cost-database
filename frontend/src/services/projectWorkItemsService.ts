import { apiClient } from './api'

export interface ProjectWorkItem {
  pwi_id: number
  project_id: number
  file_id: number
  line_item_id?: number
  original_description: string
  normalized_description?: string
  temp_code: string
  master_work_item_id?: number
  wbs_context?: string
  wbs_level?: number
  quality_score?: number
  gate_status: 'GREEN' | 'YELLOW' | 'RED'
  unit?: string
  quantity?: number
  unit_price?: number
  amount?: number
  resolution_status: 'UNRESOLVED' | 'MATCHED' | 'APPROVED' | 'MERGED'
  resolved_by?: number
  resolved_at?: string
  ai_structured_output?: string
  created_at?: string
  updated_at?: string
}

export interface ProjectWorkItemStats {
  total: number
  unresolved: number
  matched: number
  approved: number
  merged: number
  by_gate_status: Record<string, number>
}

export interface ResolveRequest {
  master_work_item_id: number
  reviewer_id: number
  edited_description?: string
  notes?: string
}

export interface ResolveResponse {
  status: string
  pwi_id: number
  master_work_item_id?: number
  synonym_created: boolean
}

export interface ListParams {
  project_id?: number
  gate_status?: string
  resolution_status?: string
  skip?: number
  limit?: number
}

export const projectWorkItemsService = {
  list: (params?: ListParams): Promise<ProjectWorkItem[]> =>
    apiClient.get('/project-work-items', { params }).then(res => res.data),

  getStats: (project_id?: number): Promise<ProjectWorkItemStats> =>
    apiClient.get('/project-work-items/stats', { params: { project_id } }).then(res => res.data),

  get: (id: number): Promise<ProjectWorkItem> =>
    apiClient.get(`/project-work-items/${id}`).then(res => res.data),

  resolve: (id: number, data: ResolveRequest): Promise<ResolveResponse> =>
    apiClient.post(`/project-work-items/${id}/resolve`, data).then(res => res.data),

  bulkResolve: (
    resolutions: Array<{ pwi_id: number; master_work_item_id: number; edited_description?: string }>,
    reviewer_id: number
  ): Promise<{ resolved: number; total: number; errors: any[] }> =>
    apiClient.post('/project-work-items/bulk-resolve', { resolutions, reviewer_id }).then(res => res.data),
}
