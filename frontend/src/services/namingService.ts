import apiClient from './api'

// Types
export interface ValidationRequest {
  name: string
  sec_code?: string
  strict_mode?: boolean
}

export interface ValidationResponse {
  name: string
  is_valid: boolean
  has_verb: boolean
  has_specs: boolean
  length: number
  parts_count: number
  issues: string[]
  suggestions?: string[]
  confidence_score: number
}

export interface GenerateRequest {
  description: string
  sec_code: string
  material_grade?: string
  material_spec?: Record<string, unknown>
}

export interface GenerateResponse {
  original_description: string
  natural_name: string
  material_spec?: Record<string, unknown>
  validation: ValidationResponse
}

export interface BatchValidateResult {
  name: string
  is_valid: boolean
  confidence_score: number
  issues: string[]
}

export interface BatchValidateResponse {
  total: number
  valid: number
  invalid: number
  results: BatchValidateResult[]
}

export interface BatchGenerateItem {
  description: string
  sec_code: string
  material_grade?: string
}

export interface BatchGenerateResult {
  original: string
  natural_name?: string
  material_spec?: Record<string, unknown>
  is_valid?: boolean
  status: 'success' | 'error'
  error?: string
}

export interface BatchGenerateResponse {
  total: number
  successful: number
  failed: number
  results: BatchGenerateResult[]
}

export interface VerbDictionaryItem {
  en_key: string
  vn_verb: string
  category: string
  examples: string[]
}

export interface LocationDictionaryItem {
  en_key: string
  vn_location: string
  category: string
  sec_codes: string[]
}

export interface NamingExample {
  sec_code: string
  natural_name: string
  parts: string[]
  has_verb: boolean
  has_specs: boolean
}

export interface NormalizeResult {
  message: string
  line_item_id: number
  original_description: string
  normalized_description: string
  work_category: string
  normalization_confidence: number
}

export interface BulkNormalizeResult {
  message: string
  total: number
  success: number
  failed: number
  skipped: number
  items: Array<{
    line_item_id: number
    normalized_description: string
    work_category: string
    confidence: number
  }>
}

// Service
export const namingService = {
  // Validate a natural name
  validate: async (request: ValidationRequest): Promise<ValidationResponse> => {
    const response = await apiClient.post<ValidationResponse>('/api/v1/naming/validate', request)
    return response.data
  },

  // Generate a natural name from description
  generate: async (request: GenerateRequest): Promise<GenerateResponse> => {
    const response = await apiClient.post<GenerateResponse>('/api/v1/naming/generate', request)
    return response.data
  },

  // Batch validate multiple names
  batchValidate: async (names: string[], strictMode = false): Promise<BatchValidateResponse> => {
    const response = await apiClient.post<BatchValidateResponse>(
      `/api/v1/naming/batch/validate?strict_mode=${strictMode}`,
      names
    )
    return response.data
  },

  // Batch generate natural names
  batchGenerate: async (items: BatchGenerateItem[]): Promise<BatchGenerateResponse> => {
    const response = await apiClient.post<BatchGenerateResponse>('/api/v1/naming/batch/generate', items)
    return response.data
  },

  // Get verb dictionary
  getVerbs: async (category?: string): Promise<VerbDictionaryItem[]> => {
    const params = category ? `?category=${category}` : ''
    const response = await apiClient.get<VerbDictionaryItem[]>(`/api/v1/naming/dictionary/verbs${params}`)
    return response.data
  },

  // Get location dictionary
  getLocations: async (): Promise<LocationDictionaryItem[]> => {
    const response = await apiClient.get<LocationDictionaryItem[]>('/api/v1/naming/dictionary/locations')
    return response.data
  },

  // Get naming template for SEC code
  getTemplate: async (secCode: string): Promise<{ sec_code: string; template: string }> => {
    const response = await apiClient.get<{ sec_code: string; template: string }>(
      `/api/v1/naming/templates/${secCode}`
    )
    return response.data
  },

  // Get naming examples
  getExamples: async (secCode?: string, limit = 20): Promise<{ total: number; examples: NamingExample[] }> => {
    const params = new URLSearchParams()
    if (secCode) params.append('sec_code', secCode)
    params.append('limit', limit.toString())

    const response = await apiClient.get<{ total: number; examples: NamingExample[] }>(
      `/api/v1/naming/examples?${params}`
    )
    return response.data
  },

  // Normalize a single line item
  normalizeLineItem: async (lineItemId: number): Promise<NormalizeResult> => {
    const response = await apiClient.post<NormalizeResult>(`/line-items/${lineItemId}/normalize`)
    return response.data
  },

  // Bulk normalize line items
  bulkNormalize: async (lineItemIds: number[]): Promise<BulkNormalizeResult> => {
    const response = await apiClient.post<BulkNormalizeResult>('/line-items/bulk-normalize', {
      line_item_ids: lineItemIds
    })
    return response.data
  },
}

export default namingService
