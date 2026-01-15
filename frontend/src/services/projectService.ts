import apiClient from './api'

export interface Project {
  id: number
  name: string
  description?: string
  client_name?: string
  location?: string
  start_date?: string
  end_date?: string
  status: string
  created_at: string
  updated_at: string
  created_by: number
  file_count?: number
  line_item_count?: number
}

export interface CreateProjectData {
  name: string
  description?: string
  client_name?: string
  location?: string
  start_date?: string
  end_date?: string
  status?: string
}

export interface UpdateProjectData extends Partial<CreateProjectData> {}

export const projectService = {
  // Get all projects
  getProjects: async (
    skip: number = 0,
    limit: number = 100,
    status?: string
  ) => {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
    })
    if (status) params.append('status', status)
    
    const response = await apiClient.get<Project[]>(`/projects?${params}`)
    return response.data
  },

  // Get single project
  getProject: async (id: number) => {
    const response = await apiClient.get<Project>(`/projects/${id}`)
    return response.data
  },

  // Create project
  createProject: async (data: CreateProjectData) => {
    const response = await apiClient.post<Project>('/projects', data)
    return response.data
  },

  // Update project
  updateProject: async (id: number, data: UpdateProjectData) => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data)
    return response.data
  },

  // Delete project
  deleteProject: async (id: number) => {
    await apiClient.delete(`/projects/${id}`)
  },

  // Get project statistics
  getProjectStats: async (id: number) => {
    const response = await apiClient.get(`/projects/${id}/stats`)
    return response.data
  },
}
