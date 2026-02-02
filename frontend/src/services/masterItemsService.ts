/**
 * Master Items Service
 * API service for managing master work items
 */
import api from './api'

export interface MasterItem {
  master_id: number
  work_code: string
  description: string
  description_normalized: string | null
  sec_code: string
  category: string | null
  unit_standard: string
  ref_unit_price_min: number | null
  ref_unit_price_avg: number | null
  ref_unit_price_max: number | null
  occurrence_count: number
  source_files: string | null
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface MasterStatistics {
  total_master_items: number
  verified_items: number
  unverified_items: number
  by_sec_code: Record<string, number>
  by_material_grade?: Record<string, number>
}

export interface WorkCodeGenerateRequest {
  description: string
  sec_code: string
  unit?: string
  include_grade?: boolean
}

export interface WorkCodeGenerateResponse {
  work_code: string
  description: string
  sec_code: string
  material_grade: string | null
  is_valid: boolean
  parsed: {
    sec_prefix: string
    category: string
    sub_category: string | null
    sequence: string
  } | null
}

export interface BuildMasterRequest {
  file_id: number
  min_confidence?: number
  skip_unclassified?: boolean
}

export interface BuildMasterResponse {
  total_items: number
  added: number
  updated: number
  skipped: number
  by_sec_code: Record<string, number>
}

export interface SearchByCodeResponse {
  pattern: string
  count: number
  items: MasterItem[]
}

export const masterItemsService = {
  /**
   * List master items with filters
   */
  list: async (params?: {
    skip?: number
    limit?: number
    sec_code?: string
    search?: string
    verified_only?: boolean
  }): Promise<MasterItem[]> => {
    const response = await api.get('/master-items/', { params })
    return response.data
  },

  /**
   * Get master statistics
   */
  getStatistics: async (): Promise<MasterStatistics> => {
    const response = await api.get('/master-items/statistics')
    return response.data
  },

  /**
   * Get specific master item
   */
  get: async (masterId: number): Promise<MasterItem> => {
    const response = await api.get(`/master-items/${masterId}`)
    return response.data
  },

  /**
   * Create new master item
   */
  create: async (data: {
    description: string
    sec_code: string
    unit: string
    unit_price?: number
  }): Promise<MasterItem> => {
    const response = await api.post('/master-items/', data)
    return response.data
  },

  /**
   * Update master item
   */
  update: async (
    masterId: number,
    data: {
      description?: string
      sec_code?: string
      unit_standard?: string
      is_verified?: boolean
    }
  ): Promise<MasterItem> => {
    const response = await api.put(`/master-items/${masterId}`, data)
    return response.data
  },

  /**
   * Delete master item (soft delete)
   */
  delete: async (masterId: number): Promise<void> => {
    await api.delete(`/master-items/${masterId}`)
  },

  /**
   * Generate work code (preview only)
   */
  generateCode: async (
    data: WorkCodeGenerateRequest
  ): Promise<WorkCodeGenerateResponse> => {
    const response = await api.post('/master-items/generate-code', data)
    return response.data
  },

  /**
   * Build master database from BOQ file
   */
  buildFromFile: async (
    data: BuildMasterRequest
  ): Promise<BuildMasterResponse> => {
    const response = await api.post('/master-items/build', data)
    return response.data
  },

  /**
   * Regenerate all work codes
   */
  rebuildAll: async (dryRun: boolean = true): Promise<{
    dry_run: boolean
    total: number
    updated: number
    skipped: number
    previews: Array<{
      old: string
      new: string
      description: string
    }>
  }> => {
    const response = await api.post('/master-items/rebuild-all', null, {
      params: { dry_run: dryRun },
    })
    return response.data
  },

  /**
   * Search by work code pattern
   */
  searchByCode: async (pattern: string): Promise<SearchByCodeResponse> => {
    const response = await api.get('/master-items/search/by-code', {
      params: { code_pattern: pattern },
    })
    return response.data
  },

  /**
   * Export to CSV
   */
  exportCSV: async (): Promise<{
    filename: string
    path: string
    message: string
  }> => {
    const response = await api.get('/master-items/export/csv')
    return response.data
  },
}
