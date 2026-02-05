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

export interface ColumnMappingResult {
  columnMapping: Record<string, string>
  headerRow: number
  dataStartRow: number
  sheetName: string
  saveAsTemplate?: boolean
  templateName?: string
}

export interface SystemField {
  key: string
  label: string
  labelVi: string
  required: boolean
  icon: string
  keywords: string[]
}

export interface ValidationWarning {
  field: string
  type: 'missing_required' | 'empty_values' | 'type_mismatch'
  message: string
  severity: 'error' | 'warning'
}

export interface SelectOption {
  value: string
  label: string
  score: number
  disabled: boolean
}
