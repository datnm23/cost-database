/**
 * System Service
 * API service for system health and matcher management
 */
import api from './api'

export interface MatcherHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  matcher_type: string
  embedding_service: {
    status: 'up' | 'down'
    model: string
    latency_ms?: number
  }
  faiss_index: {
    status: 'ready' | 'not_ready'
    vectors_count: number
    dimension: number
    last_updated?: string
  }
  cache: {
    status: 'enabled' | 'disabled'
    size: number
    max_size: number
    hit_rate?: number
  }
}

export interface MatcherStats {
  total_matches: number
  matches_today: number
  avg_latency_ms: number
  cache_hits: number
  cache_misses: number
  hit_rate: number
  by_match_type: Record<string, number>
  by_tier: Record<string, number>
}

export interface SystemInfo {
  version: string
  environment: string
  uptime_seconds: number
  database: {
    status: 'connected' | 'disconnected'
    pool_size: number
    active_connections: number
  }
  memory: {
    used_mb: number
    available_mb: number
    percent: number
  }
}

export const systemService = {
  /**
   * Get matcher health status
   */
  getMatcherHealth: async (): Promise<MatcherHealth> => {
    const response = await api.get('/matcher/health')
    return response.data
  },

  /**
   * Get matcher statistics
   */
  getMatcherStats: async (): Promise<MatcherStats> => {
    const response = await api.get('/matcher/stats')
    return response.data
  },

  /**
   * Rebuild the matcher index
   */
  rebuildMatcher: async (): Promise<{ message: string; duration_ms: number; vectors_indexed: number }> => {
    const response = await api.post('/matcher/rebuild')
    return response.data
  },

  /**
   * Clear the matcher cache
   */
  clearCache: async (): Promise<{ message: string; cleared: number }> => {
    const response = await api.post('/matcher/clear-cache')
    return response.data
  },

  /**
   * Get system info
   */
  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await api.get('/system/info')
    return response.data
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string; timestamp: string }> => {
    const response = await api.get('/health')
    return response.data
  },
}

export default systemService
