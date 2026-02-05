/**
 * Synonym Service
 * API service for managing synonyms for master items
 */
import api from './api'

export interface Synonym {
  synonym_id: number
  master_id: number
  synonym_text: string
  synonym_type: 'alias' | 'abbreviation' | 'regional' | 'english'
  source: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SynonymCreate {
  synonym_text: string
  synonym_type: 'alias' | 'abbreviation' | 'regional' | 'english'
  source?: string
}

export interface SynonymStats {
  total_synonyms: number
  by_type: Record<string, number>
  by_source: Record<string, number>
  items_with_synonyms: number
  avg_synonyms_per_item: number
}

export interface SynonymWithMaster extends Synonym {
  master_work_code: string
  master_description: string
}

export const synonymService = {
  /**
   * Get synonyms for a master item
   */
  getSynonyms: async (masterId: number): Promise<Synonym[]> => {
    const response = await api.get(`/synonyms/master-items/${masterId}/synonyms`)
    return response.data
  },

  /**
   * Add a synonym to a master item
   */
  addSynonym: async (masterId: number, data: SynonymCreate): Promise<Synonym> => {
    const response = await api.post(`/synonyms/master-items/${masterId}/synonyms`, data)
    return response.data
  },

  /**
   * Delete a synonym
   */
  deleteSynonym: async (synonymId: number): Promise<void> => {
    await api.delete(`/synonyms/${synonymId}`)
  },

  /**
   * Update a synonym
   */
  updateSynonym: async (
    synonymId: number,
    data: { synonym_text?: string; synonym_type?: string; is_active?: boolean }
  ): Promise<Synonym> => {
    const response = await api.put(`/synonyms/${synonymId}`, data)
    return response.data
  },

  /**
   * List all synonyms with pagination
   */
  listAll: async (params?: {
    skip?: number
    limit?: number
    type?: string
    search?: string
  }): Promise<SynonymWithMaster[]> => {
    const response = await api.get('/synonyms/', { params })
    return response.data
  },

  /**
   * Get synonym statistics
   */
  getStatistics: async (): Promise<SynonymStats> => {
    const response = await api.get('/synonyms/statistics')
    return response.data
  },

  /**
   * Rebuild synonym cache
   */
  rebuildCache: async (): Promise<{ message: string; synonyms_cached: number }> => {
    const response = await api.post('/synonyms/rebuild-cache')
    return response.data
  },

  /**
   * Import synonyms from CSV
   */
  importFromCSV: async (file: File): Promise<{
    imported: number
    skipped: number
    errors: string[]
  }> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/synonyms/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  /**
   * Search synonyms
   */
  search: async (query: string): Promise<SynonymWithMaster[]> => {
    const response = await api.get('/synonyms/search', { params: { query } })
    return response.data
  },
}

export default synonymService
