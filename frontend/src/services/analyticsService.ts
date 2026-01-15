import apiClient from './api'

export interface DashboardStats {
  total_projects: number
  total_files: number
  total_line_items: number
  verified_items: number
  pending_items: number
  classification_accuracy: number
  recent_activity: ActivityItem[]
}

export interface ActivityItem {
  id: number
  type: string
  description: string
  timestamp: string
  user: string
}

export interface ProjectStats {
  project_id: number
  project_name: string
  total_files: number
  total_line_items: number
  verified_items: number
  pending_items: number
  classification_accuracy: number
  cost_summary: {
    total_cost: number
    by_sec_code: { sec_code: string; total: number }[]
  }
}

export interface SECDistribution {
  sec_code: string
  description: string
  count: number
  percentage: number
  total_cost: number
}

export interface ClassificationAccuracy {
  total_classified: number
  total_verified: number
  accuracy_rate: number
  by_method: {
    method: string
    count: number
    accuracy: number
  }[]
}

export const analyticsService = {
  // Get dashboard statistics
  getDashboardStats: async () => {
    const response = await apiClient.get<DashboardStats>('/analytics/dashboard')
    return response.data
  },

  // Get project statistics
  getProjectStats: async (projectId: number) => {
    const response = await apiClient.get<ProjectStats>(`/analytics/projects/${projectId}`)
    return response.data
  },

  // Get SEC code distribution
  getSECDistribution: async (projectId?: number) => {
    const params = projectId ? `?project_id=${projectId}` : ''
    const response = await apiClient.get<SECDistribution[]>(`/analytics/sec-distribution${params}`)
    return response.data
  },

  // Get classification accuracy
  getClassificationAccuracy: async (projectId?: number) => {
    const params = projectId ? `?project_id=${projectId}` : ''
    const response = await apiClient.get<ClassificationAccuracy>(`/analytics/classification-accuracy${params}`)
    return response.data
  },

  // Get cost analysis
  getCostAnalysis: async (projectId: number) => {
    const response = await apiClient.get(`/analytics/projects/${projectId}/cost-analysis`)
    return response.data
  },

  // Get trends over time
  getTrends: async (period: 'week' | 'month' | 'year' = 'month') => {
    const response = await apiClient.get(`/analytics/trends?period=${period}`)
    return response.data
  },
}
