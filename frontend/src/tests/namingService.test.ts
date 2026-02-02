import { describe, it, expect, vi, beforeEach } from 'vitest'
import { namingService } from '../services/namingService'
import apiClient from '../services/api'

// Mock the API client
vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}))

describe('namingService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('validate', () => {
    it('should call correct endpoint for validation', async () => {
      const mockResponse = {
        data: {
          name: 'Test name',
          is_valid: true,
          has_verb: true,
          has_specs: true,
          length: 20,
          parts_count: 3,
          issues: [],
          confidence_score: 85,
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.validate({
        name: 'Test name',
        sec_code: 'SEC-01',
      })

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/naming/validate', {
        name: 'Test name',
        sec_code: 'SEC-01',
      })
      expect(result.is_valid).toBe(true)
    })
  })

  describe('generate', () => {
    it('should call correct endpoint for generation', async () => {
      const mockResponse = {
        data: {
          original_description: 'Original',
          natural_name: 'Generated name',
          validation: {
            is_valid: true,
            confidence_score: 90,
          },
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.generate({
        description: 'Test description',
        sec_code: 'SEC-01',
      })

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/naming/generate', {
        description: 'Test description',
        sec_code: 'SEC-01',
      })
      expect(result.natural_name).toBe('Generated name')
    })
  })

  describe('batchValidate', () => {
    it('should call correct endpoint for batch validation', async () => {
      const mockResponse = {
        data: {
          total: 2,
          valid: 1,
          invalid: 1,
          results: [
            { name: 'Valid name', is_valid: true, confidence_score: 90, issues: [] },
            { name: 'Invalid', is_valid: false, confidence_score: 30, issues: ['No verb'] },
          ],
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.batchValidate(['Valid name', 'Invalid'])

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/naming/batch/validate?strict_mode=false',
        ['Valid name', 'Invalid']
      )
      expect(result.total).toBe(2)
      expect(result.valid).toBe(1)
    })
  })

  describe('batchGenerate', () => {
    it('should call correct endpoint for batch generation', async () => {
      const mockResponse = {
        data: {
          total: 2,
          successful: 2,
          failed: 0,
          results: [
            { original: 'Desc 1', natural_name: 'Name 1', status: 'success' },
            { original: 'Desc 2', natural_name: 'Name 2', status: 'success' },
          ],
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.batchGenerate([
        { description: 'Desc 1', sec_code: 'SEC-01' },
        { description: 'Desc 2', sec_code: 'SEC-02' },
      ])

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/naming/batch/generate', [
        { description: 'Desc 1', sec_code: 'SEC-01' },
        { description: 'Desc 2', sec_code: 'SEC-02' },
      ])
      expect(result.successful).toBe(2)
    })
  })

  describe('getVerbs', () => {
    it('should call correct endpoint for verbs dictionary', async () => {
      const mockResponse = {
        data: [
          { en_key: 'excavate', vn_verb: 'Đào', category: 'construction', examples: [] },
        ],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      const result = await namingService.getVerbs()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/naming/dictionary/verbs')
      expect(result).toHaveLength(1)
      expect(result[0].vn_verb).toBe('Đào')
    })

    it('should filter by category when provided', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: [] })

      await namingService.getVerbs('construction')

      expect(apiClient.get).toHaveBeenCalledWith(
        '/api/v1/naming/dictionary/verbs?category=construction'
      )
    })
  })

  describe('getLocations', () => {
    it('should call correct endpoint for locations dictionary', async () => {
      const mockResponse = {
        data: [
          { en_key: 'foundation', vn_location: 'móng', category: 'structural', sec_codes: ['SEC-02'] },
        ],
      }

      vi.mocked(apiClient.get).mockResolvedValue(mockResponse)

      const result = await namingService.getLocations()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/naming/dictionary/locations')
      expect(result).toHaveLength(1)
    })
  })

  describe('normalizeLineItem', () => {
    it('should call correct endpoint for single item normalization', async () => {
      const mockResponse = {
        data: {
          message: 'Success',
          line_item_id: 1,
          original_description: 'Original',
          normalized_description: 'Normalized',
          work_category: 'concrete_rebar',
          normalization_confidence: 85,
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.normalizeLineItem(1)

      expect(apiClient.post).toHaveBeenCalledWith('/line-items/1/normalize')
      expect(result.normalized_description).toBe('Normalized')
    })
  })

  describe('bulkNormalize', () => {
    it('should call correct endpoint for bulk normalization', async () => {
      const mockResponse = {
        data: {
          message: 'Success',
          total: 3,
          success: 3,
          failed: 0,
          skipped: 0,
          items: [],
        },
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const result = await namingService.bulkNormalize([1, 2, 3])

      expect(apiClient.post).toHaveBeenCalledWith('/line-items/bulk-normalize', {
        line_item_ids: [1, 2, 3],
      })
      expect(result.success).toBe(3)
    })
  })

  describe('error handling', () => {
    it('should propagate errors from API', async () => {
      const error = new Error('Network error')
      vi.mocked(apiClient.post).mockRejectedValue(error)

      await expect(namingService.validate({ name: 'test' })).rejects.toThrow('Network error')
    })
  })
})
