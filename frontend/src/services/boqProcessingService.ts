/**
 * BOQ Processing Service
 * API service for processing BOQ files with hybrid matching
 */
import api from './api'

export interface MatchResult {
  line_item_id: number
  original_description: string
  normalized_description: string
  match_status: 'matched' | 'new' | 'review_needed'
  matched_master_id?: number
  matched_work_code?: string
  matched_description?: string
  similarity_score?: number
  match_type?: 'exact' | 'fuzzy' | 'semantic' | 'keyword'
  tier_used?: string
  alternatives?: Array<{
    master_id: number
    work_code: string
    description: string
    score: number
  }>
  confidence?: number
}

export interface ProcessingResult {
  file_id: number
  file_name: string
  total_items: number
  matched: number
  new_items: number
  review_needed: number
  processing_time_ms: number
  results: MatchResult[]
}

export interface ProcessingDetails {
  file_id: number
  file_name: string
  processed_at: string
  summary: {
    total: number
    matched: number
    new_items: number
    review_needed: number
    match_rate: number
  }
  by_tier: Record<string, number>
  by_match_type: Record<string, number>
  results: MatchResult[]
}

export interface ProcessingOptions {
  min_similarity?: number
  use_semantic?: boolean
  auto_add_new?: boolean
  processing_method?: '3_tier' | 'ai_only'
}

export interface AddNewItemsResult {
  added: number
  skipped: number
  items: Array<{
    line_item_id: number
    master_id: number
    work_code: string
  }>
}

export interface MatchDescriptionResult {
  description: string
  normalized: string
  matches: Array<{
    master_id: number
    work_code: string
    description: string
    score: number
    match_type: string
  }>
  best_match?: {
    master_id: number
    work_code: string
    description: string
    score: number
  }
}

export const boqProcessingService = {
  /**
   * Process a BOQ file with hybrid matching
   */
  processBoq: async (
    fileId: number,
    options?: ProcessingOptions
  ): Promise<ProcessingResult> => {
    const response = await api.post(`/master-items/process-boq`, {
      file_id: fileId,
      ...options,
    })
    return response.data
  },

  /**
   * Get processing details for a file
   */
  getProcessingDetails: async (fileId: number): Promise<ProcessingDetails> => {
    const response = await api.get(`/master-items/process-boq/${fileId}/details`)
    return response.data
  },

  /**
   * Add new items from processing to master database
   */
  addNewItems: async (
    fileId: number,
    itemIds: number[]
  ): Promise<AddNewItemsResult> => {
    const response = await api.post(`/master-items/process-boq/${fileId}/add-new`, {
      item_ids: itemIds,
    })
    return response.data
  },

  /**
   * Match a single description against master database
   */
  matchDescription: async (
    description: string,
    options?: { limit?: number; min_score?: number }
  ): Promise<MatchDescriptionResult> => {
    const response = await api.post('/master-items/match-description', {
      description,
      ...options,
    })
    return response.data
  },

  /**
   * Export processing results to Excel (returns file info)
   */
  exportResults: async (fileId: number): Promise<{ filename: string; path: string }> => {
    const response = await api.get(`/master-items/process-boq/${fileId}/export`)
    return response.data
  },

  /**
   * Download processing results as Excel file
   * Triggers browser download
   */
  downloadResults: async (fileId: number): Promise<void> => {
    const response = await api.get(`/master-items/process-boq/${fileId}/export/download`, {
      responseType: 'blob',
    })

    // Get filename from Content-Disposition header or generate one
    const contentDisposition = response.headers['content-disposition']
    let filename = `BOQ_Processing_Result_${fileId}.xlsx`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
      }
    }

    // Create blob and trigger download
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * Download line items export as Excel file
   */
  downloadLineItems: async (fileId: number): Promise<void> => {
    const response = await api.get(`/master-items/line-items/${fileId}/export`, {
      responseType: 'blob',
    })

    const filename = `Line_Items_${fileId}.xlsx`
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * Download with original format preserved
   */
  downloadWithOriginalFormat: async (fileId: number): Promise<void> => {
    const response = await api.get(`/master-items/line-items/${fileId}/export/original`, {
      responseType: 'blob',
    })

    const filename = `BOQ_With_Results_${fileId}.xlsx`
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * Get list of processed files
   */
  getProcessedFiles: async (): Promise<
    Array<{
      file_id: number
      file_name: string
      processed_at: string
      total_items: number
      match_rate: number
    }>
  > => {
    const response = await api.get('/master-items/process-boq/files')
    return response.data
  },
}

export default boqProcessingService
