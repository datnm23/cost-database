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

export interface UpdateProjectData extends Partial<CreateProjectData> { }

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

    // Use any because backend response doesn't match frontend Project[] type directly
    const response = await apiClient.get<any>(`/projects/?${params}`)

    // Handle paginated response and field mapping
    const items = response.data.items || []
    return items.map((item: any) => mapBackendToFrontend(item))
  },

  // Get single project
  getProject: async (id: number) => {
    const response = await apiClient.get<any>(`/projects/${id}/`)
    return mapBackendToFrontend(response.data)
  },

  // Create project
  createProject: async (data: CreateProjectData) => {
    // Basic auto-generation of project code if not provided
    // In a real app, this should probably be a field in the form
    const project_code = data.name.toUpperCase().replace(/\s+/g, '_').substring(0, 10) + '_' + Date.now().toString().slice(-4)

    const backendData = {
      project_code: project_code,
      project_name: data.name,
      description: data.description,
      client_name: data.client_name,
      location: data.location,
      start_date: data.start_date,
      // end_date not supported by backend schema seemingly, or maybe it is? 
      // Checking schema again: CreateProject inherits ProjectBase. ProjectBase has start_date but NO end_date.
      project_type: 'commercial', // Default or need to add to frontend form? Backend requires project_type
      status: data.status
    }

    // Note: ProjectBase requires project_type. Frontend doesn't send it. 
    // We default to 'commercial' or similar if available enum.
    // Enum is: residential, commercial, industrial, infrastructure

    const response = await apiClient.post<any>('/projects/', backendData)
    return mapBackendToFrontend(response.data)
  },

  // Update project
  updateProject: async (id: number, data: UpdateProjectData) => {
    const backendData: any = {}
    if (data.name) backendData.project_name = data.name
    if (data.client_name) backendData.client_name = data.client_name
    if (data.location) backendData.location = data.location
    if (data.start_date) backendData.start_date = data.start_date
    if (data.status) backendData.status = data.status
    // description and end_date are not in backend schema?

    const response = await apiClient.put<any>(`/projects/${id}/`, backendData)
    return mapBackendToFrontend(response.data)
  },

  // Delete project
  deleteProject: async (id: number) => {
    await apiClient.delete(`/projects/${id}/`)
  },

  // Get project statistics
  getProjectStats: async (id: number) => {
    const response = await apiClient.get(`/projects/${id}/stats/`)
    return response.data
  },
}

// Helper to map backend response to frontend interface
const mapBackendToFrontend = (item: any): Project => ({
  id: item.project_id,
  name: item.project_name,
  description: '', // Not returned by backend
  client_name: item.client_name,
  location: item.location,
  start_date: item.start_date,
  end_date: undefined, // Not returned by backend
  status: item.status,
  created_at: item.created_at,
  updated_at: item.updated_at,
  created_by: 0, // Not returned by backend
  file_count: 0,
  line_item_count: 0
})
