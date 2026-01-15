import apiClient from './api'

export interface LineItem {
  id: number
  file_id: number
  item_number?: string
  description: string
  quantity?: number
  unit?: string
  unit_price?: number
  total_price?: number
  sec_code?: string
  sec_code_id?: number
  classification_confidence?: number
  classification_method?: string
  is_verified: boolean
  notes?: string
  metadata?: any
  created_at: string
  updated_at: string
}

export interface SECCode {
  id: number
  code: string
  description: string
  level: number
  parent_id?: number
  is_active: boolean
  metadata?: any
}

export interface ClassificationResult {
  line_item_id: number
  sec_code: string
  confidence: number
  method: string
}

export interface BulkUpdateData {
  line_item_ids: number[]
  sec_code_id?: number
  is_verified?: boolean
  notes?: string
}

export const lineItemService = {
  // Get line items (with filters)
  getLineItems: async (params: {
    file_id?: number
    project_id?: number
    sec_code?: string
    is_verified?: boolean
    skip?: number
    limit?: number
  }) => {
    const queryParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString())
      }
    })
    
    const response = await apiClient.get<LineItem[]>(`/line-items?${queryParams}`)
    return response.data
  },

  // Get single line item
  getLineItem: async (id: number) => {
    const response = await apiClient.get<LineItem>(`/line-items/${id}`)
    return response.data
  },

  // Update line item
  updateLineItem: async (id: number, data: Partial<LineItem>) => {
    const response = await apiClient.put<LineItem>(`/line-items/${id}`, data)
    return response.data
  },

  // Bulk update line items
  bulkUpdate: async (data: BulkUpdateData) => {
    const response = await apiClient.post('/line-items/bulk-update', data)
    return response.data
  },

  // Classify line item
  classifyLineItem: async (id: number) => {
    const response = await apiClient.post<ClassificationResult>(`/line-items/${id}/classify`)
    return response.data
  },

  // Reclassify with feedback
  reclassifyWithFeedback: async (id: number, correctSecCode: string) => {
    const response = await apiClient.post(`/line-items/${id}/reclassify`, {
      correct_sec_code: correctSecCode,
    })
    return response.data
  },

  // Delete line item
  deleteLineItem: async (id: number) => {
    await apiClient.delete(`/line-items/${id}`)
  },
}

export const secCodeService = {
  // Get all SEC codes
  getSECCodes: async (level?: number, parentId?: number) => {
    const params = new URLSearchParams()
    if (level !== undefined) params.append('level', level.toString())
    if (parentId !== undefined) params.append('parent_id', parentId.toString())
    
    const response = await apiClient.get<SECCode[]>(`/sec-codes?${params}`)
    return response.data
  },

  // Get SEC code hierarchy
  getSECHierarchy: async () => {
    const response = await apiClient.get('/sec-codes/hierarchy')
    return response.data
  },

  // Get children of SEC code
  getSECChildren: async (codeId: number) => {
    const response = await apiClient.get<SECCode[]>(`/sec-codes/${codeId}/children`)
    return response.data
  },

  // Search SEC codes
  searchSECCodes: async (query: string) => {
    const response = await apiClient.get<SECCode[]>(`/sec-codes/search?q=${encodeURIComponent(query)}`)
    return response.data
  },
}
