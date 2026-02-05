/**
 * Code Service
 * API service for managing Legal and ISO code systems
 */
import api from './api'

// Legal Code Types
export interface LegalCodeParsed {
  code: string
  prefix: string
  appendix: string
  chapter?: string
  section?: string
  item?: string
  description?: string
  is_valid: boolean
}

export interface LegalCodeSearchResult {
  code: string
  description: string
  prefix: string
  appendix: string
  category?: string
}

export interface LegalCodeGenerateResult {
  description: string
  suggested_code: string
  confidence: number
  alternatives?: string[]
}

export interface LegalCodeStats {
  total_codes: number
  by_prefix: Record<string, number>
  by_appendix: Record<string, number>
  most_used: Array<{ code: string; count: number }>
}

// ISO Code Types
export interface ISOCodeParsed {
  code: string
  system: string
  group: string
  class: string
  subclass?: string
  description?: string
  is_valid: boolean
}

export interface ISOHierarchy {
  code: string
  level: number
  parent?: string
  children: string[]
  description: string
  full_path: string[]
}

export interface ISOCodeGenerateResult {
  description: string
  suggested_code: string
  confidence: number
  hierarchy: string[]
}

// Multi-Code Types
export interface MultiCodeMappingResult {
  description: string
  sec_code?: string
  work_code?: string
  legal_code?: string
  iso_code?: string
  confidence: number
  mapping_source: string
}

export interface BatchCodeMappingResult {
  total: number
  successful: number
  failed: number
  results: MultiCodeMappingResult[]
}

export interface MultiCodeSearchResult {
  query: string
  results: Array<{
    type: 'sec' | 'legal' | 'iso' | 'work'
    code: string
    description: string
    score: number
  }>
}

export const codeService = {
  // Legal Code APIs
  parseLegalCode: async (code: string): Promise<LegalCodeParsed> => {
    const response = await api.get(`/codes/legal/parse/${encodeURIComponent(code)}`)
    return response.data
  },

  searchLegalCodes: async (params: {
    prefix?: string
    appendix?: string
    query?: string
    limit?: number
  }): Promise<LegalCodeSearchResult[]> => {
    const response = await api.get('/codes/legal/search', { params })
    return response.data
  },

  generateLegalCode: async (description: string): Promise<LegalCodeGenerateResult> => {
    const response = await api.post('/codes/legal/generate', { description })
    return response.data
  },

  getLegalStats: async (): Promise<LegalCodeStats> => {
    const response = await api.get('/codes/legal/statistics')
    return response.data
  },

  // ISO Code APIs
  parseISOCode: async (code: string): Promise<ISOCodeParsed> => {
    const response = await api.get(`/codes/iso/parse/${encodeURIComponent(code)}`)
    return response.data
  },

  generateISOCode: async (description: string): Promise<ISOCodeGenerateResult> => {
    const response = await api.post('/codes/iso/generate', { description })
    return response.data
  },

  getISOHierarchy: async (code: string): Promise<ISOHierarchy> => {
    const response = await api.get(`/codes/iso/hierarchy/${encodeURIComponent(code)}`)
    return response.data
  },

  // Multi-Code APIs
  autoMapCodes: async (
    description: string,
    secCode?: string
  ): Promise<MultiCodeMappingResult> => {
    const response = await api.post('/codes/map/auto', { description, sec_code: secCode })
    return response.data
  },

  batchMapCodes: async (
    items: Array<{ description: string; sec_code?: string }>
  ): Promise<BatchCodeMappingResult> => {
    const response = await api.post('/codes/map/batch', { items })
    return response.data
  },

  multiCodeSearch: async (query: string): Promise<MultiCodeSearchResult> => {
    const response = await api.get('/codes/search/multi', { params: { query } })
    return response.data
  },
}

export default codeService
