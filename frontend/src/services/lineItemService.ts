import apiClient from './api'

export interface LineItem {
  line_item_id: number
  file_id: number
  project_id: number
  row_number?: number
  description: string
  normalized_description?: string
  normalization_confidence?: number
  work_category?: string
  quantity?: number
  unit?: string
  unit_price?: number
  amount?: number
  sec_code?: string
  confidence_score?: number
  classification_method?: string
  needs_review?: boolean
  validation_issues?: string[]
}

export interface SECCode {
  sec_code: string  // Changed from 'code' to 'sec_code'
  sec_name_vi: string  // Changed from 'description'
  sec_name_en?: string
  level: number
  parent_code?: string  // Changed from 'parent_id'
  is_active: boolean
}

export interface ClassificationResult {
  line_item_id: number
  sec_code: string
  confidence: number
  method: string
}

export interface BulkUpdateData {
  line_item_ids: number[]
  sec_code?: string
  needs_review?: boolean
  notes?: string
}

export const lineItemService = {
  // Get line items (with filters)
  getLineItems: async (params: {
    file_id?: number
    project_id?: number
    sec_code?: string
    needs_review?: boolean
    skip?: number
    limit?: number
  }) => {
    const queryParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value.toString())
      }
    })

    const response = await apiClient.get<{ items: LineItem[], total: number }>(`/line-items?${queryParams}`)
    // Return items array, not the whole response
    return response.data.items || []
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

    const response = await apiClient.get<{ sec_codes: SECCode[], total: number }>(`/sec-codes?${params}`)
    // Return sec_codes array, not the whole response
    return response.data.sec_codes || []
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
