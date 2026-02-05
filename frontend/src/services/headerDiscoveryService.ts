import apiClient from './api'

export interface HeaderDiscoveryResult {
  sheet_name: string
  sheet_index: number
  header_row: number
  data_start_row: number
  column_names: string[]
  confidence_score: number
  is_merged_header: boolean
  column_type_hints: Record<string, number>
  sheets: SheetInfo[]
}

export interface SheetInfo {
  name: string
  index: number
  priority_score: number
  skip_reason: string | null
}

export interface ColumnSuggestion {
  excel_column: string
  system_field: string
  confidence: number
  sample_values: string[]
}

export const headerDiscoveryService = {
  // Get header discovery result for uploaded file
  discover: async (fileId: number, sheetName?: string): Promise<HeaderDiscoveryResult> => {
    const params = sheetName ? `?sheet_name=${encodeURIComponent(sheetName)}` : ''
    const response = await apiClient.get<HeaderDiscoveryResult>(`/files/${fileId}/discover-header${params}`)
    return response.data
  },

  // Get suggested column mappings
  getSuggestions: async (fileId: number, headerRow: number): Promise<ColumnSuggestion[]> => {
    const response = await apiClient.get<ColumnSuggestion[]>(
      `/files/${fileId}/column-suggestions?header_row=${headerRow}`
    )
    return response.data
  },

  // Get sample data for specific columns
  getSampleData: async (
    fileId: number,
    columns: string[],
    limit: number = 10
  ): Promise<{ data: any[][]; columns: string[] }> => {
    const params = new URLSearchParams()
    columns.forEach((col) => params.append('columns', col))
    params.append('limit', String(limit))

    const response = await apiClient.get<{ data: any[][]; columns: string[] }>(
      `/files/${fileId}/sample-data?${params.toString()}`
    )
    return response.data
  },
}
