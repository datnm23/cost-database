import apiClient from './api'

export interface BOQFile {
  id: number
  project_id: number
  filename: string
  file_path: string
  file_size: number
  upload_date: string
  uploaded_by: number
  processing_status: string
  total_rows?: number
  processed_rows?: number
  error_message?: string
  metadata?: any
}

export interface FileStructure {
  columns: string[]
  sample_data: any[][]
  total_rows: number
  has_headers: boolean
}

export interface ProcessFileData {
  column_mapping: Record<string, string>
  has_headers?: boolean
  sheet_name?: string
}

export const fileService = {
  // Upload file
  uploadFile: async (projectId: number, file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post<BOQFile>(
      `/files/upload?project_id=${projectId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            onProgress(progress)
          }
        },
      }
    )
    return response.data
  },

  // Analyze file structure
  analyzeStructure: async (fileId: number, sheetName?: string) => {
    const params = sheetName ? `?sheet_name=${encodeURIComponent(sheetName)}` : ''
    const response = await apiClient.get<FileStructure>(`/files/${fileId}/analyze${params}`)
    return response.data
  },

  // Process file
  processFile: async (fileId: number, data: ProcessFileData) => {
    const response = await apiClient.post<BOQFile>(`/files/${fileId}/process`, data)
    return response.data
  },

  // Get file by ID
  getFile: async (fileId: number) => {
    const response = await apiClient.get<BOQFile>(`/files/${fileId}`)
    return response.data
  },

  // Get files for project
  getProjectFiles: async (projectId: number) => {
    const response = await apiClient.get<BOQFile[]>(`/files/project/${projectId}`)
    return response.data
  },

  // Delete file
  deleteFile: async (fileId: number) => {
    await apiClient.delete(`/files/${fileId}`)
  },

  // Get processing status
  getProcessingStatus: async (fileId: number) => {
    const response = await apiClient.get(`/files/${fileId}/status`)
    return response.data
  },
}
