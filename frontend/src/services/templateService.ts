/**
 * Template Service
 * API service for managing column mapping templates
 */
import api from './api'

// ============ Types ============

export type TemplateVisibility = 'private' | 'team' | 'public'
export type MatchType = 'exact' | 'fuzzy' | 'manual'
export type UsageAction = 'auto_applied' | 'user_selected' | 'user_modified'

export interface Template {
  template_id: number
  name: string
  description: string | null
  column_mapping: Record<string, string>
  header_row_hint: number
  sheet_name_pattern: string | null
  fingerprint: string
  fingerprint_components: FingerprintComponents | null
  use_count: number
  last_used_at: string | null
  match_success_rate: number
  created_by: number | null
  visibility: TemplateVisibility
  is_system: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TemplateCreate {
  name: string
  description?: string
  column_mapping: Record<string, string>
  header_row_hint?: number
  sheet_name_pattern?: string
  visibility?: TemplateVisibility
}

export interface TemplateUpdate {
  name?: string
  description?: string
  column_mapping?: Record<string, string>
  header_row_hint?: number
  sheet_name_pattern?: string
  visibility?: TemplateVisibility
  is_active?: boolean
}

export interface TemplateListResponse {
  templates: Template[]
  total: number
  skip: number
  limit: number
}

export interface FingerprintComponents {
  column_count: number
  column_keywords: string[]
  column_order_hash: string
  data_type_signature: string | null
}

export interface FingerprintRequest {
  column_names: string[]
  sample_data?: unknown[][]
}

export interface FingerprintResponse {
  fingerprint: string
  components: FingerprintComponents
}

export interface TemplateMatchRequest {
  column_names: string[]
  sheet_name?: string
  min_similarity?: number
  limit?: number
}

export interface TemplateMatchResult {
  template: Template
  similarity_score: number
  match_type: MatchType
  matched_columns: Record<string, string>
  unmatched_columns: string[]
}

export interface TemplateMatchResponse {
  best_match: TemplateMatchResult | null
  alternatives: TemplateMatchResult[]
  input_fingerprint: string
  message: string
}

export interface TemplateUsageCreate {
  template_id: number
  file_id?: number
  match_score?: number
  match_type: MatchType
  was_successful?: boolean
  columns_mapped?: number
  columns_total?: number
  action: UsageAction
}

export interface TemplateUsageResponse {
  log_id: number
  template_id: number
  file_id: number | null
  match_score: number | null
  match_type: MatchType
  was_successful: boolean
  columns_mapped: number | null
  columns_total: number | null
  user_id: number | null
  action: UsageAction
  created_at: string
}

export interface TemplateStatistics {
  total_templates: number
  active_templates: number
  system_templates: number
  user_templates: number
  total_uses: number
  successful_uses: number
  average_success_rate: number
  most_used_templates: Array<{
    template_id: number
    name: string
    use_count: number
  }>
  recent_uses: TemplateUsageResponse[]
}

// ============ Service ============

export const templateService = {
  /**
   * List all templates with pagination
   */
  list: async (params?: {
    skip?: number
    limit?: number
    visibility?: TemplateVisibility
    include_inactive?: boolean
  }): Promise<TemplateListResponse> => {
    const response = await api.get('/templates/', { params })
    return response.data
  },

  /**
   * Get a template by ID
   */
  get: async (templateId: number): Promise<Template> => {
    const response = await api.get(`/templates/${templateId}`)
    return response.data
  },

  /**
   * Create a new template
   */
  create: async (data: TemplateCreate): Promise<Template> => {
    const response = await api.post('/templates/', data)
    return response.data
  },

  /**
   * Update an existing template
   */
  update: async (templateId: number, data: TemplateUpdate): Promise<Template> => {
    const response = await api.put(`/templates/${templateId}`, data)
    return response.data
  },

  /**
   * Delete a template (soft delete by default)
   */
  delete: async (templateId: number, hard: boolean = false): Promise<void> => {
    await api.delete(`/templates/${templateId}`, { params: { hard } })
  },

  /**
   * Generate fingerprint from column names
   */
  generateFingerprint: async (data: FingerprintRequest): Promise<FingerprintResponse> => {
    const response = await api.post('/templates/fingerprint', data)
    return response.data
  },

  /**
   * Find matching templates for given column structure
   */
  findMatches: async (data: TemplateMatchRequest): Promise<TemplateMatchResponse> => {
    const response = await api.post('/templates/match', data)
    return response.data
  },

  /**
   * Log template usage
   */
  logUsage: async (data: TemplateUsageCreate): Promise<TemplateUsageResponse> => {
    const response = await api.post('/templates/usage', data)
    return response.data
  },

  /**
   * Get template statistics
   */
  getStatistics: async (): Promise<TemplateStatistics> => {
    const response = await api.get('/templates/statistics/')
    return response.data
  },

  /**
   * Activate a template
   */
  activate: async (templateId: number): Promise<Template> => {
    return templateService.update(templateId, { is_active: true })
  },

  /**
   * Deactivate a template
   */
  deactivate: async (templateId: number): Promise<Template> => {
    return templateService.update(templateId, { is_active: false })
  },

  /**
   * Duplicate a template with a new name
   */
  duplicate: async (templateId: number, newName: string): Promise<Template> => {
    const original = await templateService.get(templateId)
    return templateService.create({
      name: newName,
      description: original.description || undefined,
      column_mapping: original.column_mapping,
      header_row_hint: original.header_row_hint,
      sheet_name_pattern: original.sheet_name_pattern || undefined,
      visibility: 'private',
    })
  },
}

export default templateService
