import { Tag, Select, Tooltip, Space } from 'antd'
import {
  CodeOutlined,
  FileTextOutlined,
  ColumnWidthOutlined,
  NumberOutlined,
  DollarOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
} from '@ant-design/icons'
import { SystemField, SelectOption } from './types'

const { Option } = Select

interface MappingFieldRowProps {
  field: SystemField
  columns: string[]
  selectedColumn: string | undefined
  columnTypeHints: Record<string, number>
  selectedColumns: Set<string>
  sampleData: any[][]
  onSelect: (fieldKey: string, column: string | undefined) => void
}

const iconMap: Record<string, React.ReactNode> = {
  CodeOutlined: <CodeOutlined />,
  FileTextOutlined: <FileTextOutlined />,
  ColumnWidthOutlined: <ColumnWidthOutlined />,
  NumberOutlined: <NumberOutlined />,
  DollarOutlined: <DollarOutlined />,
  CalculatorOutlined: <CalculatorOutlined />,
}

function getSortedOptions(
  columns: string[],
  field: SystemField,
  columnTypeHints: Record<string, number>,
  selectedColumns: Set<string>
): SelectOption[] {
  return columns
    .map((col) => {
      const colLower = col.toLowerCase()
      let score = 0

      // Check backend hint
      if (columnTypeHints[field.key] !== undefined) {
        const hintedCol = columns[columnTypeHints[field.key]]
        if (hintedCol === col) score += 100
      }

      // Check keyword match
      for (const keyword of field.keywords) {
        if (colLower.includes(keyword.toLowerCase())) {
          score += 50
          break
        }
      }

      // Penalize already selected
      if (selectedColumns.has(col)) score -= 200

      return { value: col, label: col, score, disabled: selectedColumns.has(col) }
    })
    .sort((a, b) => b.score - a.score)
}

function calculateConfidence(
  column: string | undefined,
  field: SystemField,
  columnTypeHints: Record<string, number>,
  columns: string[]
): number {
  if (!column) return 0

  let confidence = 0
  const colLower = column.toLowerCase()

  // Backend hint match
  if (columnTypeHints[field.key] !== undefined) {
    const hintedCol = columns[columnTypeHints[field.key]]
    if (hintedCol === column) confidence += 50
  }

  // Keyword match
  for (const keyword of field.keywords) {
    if (colLower.includes(keyword.toLowerCase())) {
      confidence += 40
      break
    }
  }

  // Exact keyword match bonus
  for (const keyword of field.keywords) {
    if (colLower === keyword.toLowerCase()) {
      confidence += 10
      break
    }
  }

  return Math.min(confidence, 100)
}

function getSampleValues(
  column: string,
  columns: string[],
  sampleData: any[][]
): string[] {
  const colIndex = columns.indexOf(column)
  if (colIndex < 0) return []

  return sampleData
    .slice(0, 3)
    .map((row) => String(row[colIndex] ?? ''))
    .filter((v) => v.trim() !== '')
}

export default function MappingFieldRow({
  field,
  columns,
  selectedColumn,
  columnTypeHints,
  selectedColumns,
  sampleData,
  onSelect,
}: MappingFieldRowProps) {
  const sortedOptions = getSortedOptions(columns, field, columnTypeHints, selectedColumns)
  const confidence = calculateConfidence(selectedColumn, field, columnTypeHints, columns)
  const sampleValues = selectedColumn ? getSampleValues(selectedColumn, columns, sampleData) : []

  const getConfidenceTag = () => {
    if (!selectedColumn) {
      return (
        <Tag icon={<WarningOutlined />} color="default">
          Not mapped
        </Tag>
      )
    }

    if (confidence >= 80) {
      return (
        <Tag icon={<CheckCircleOutlined />} color="success">
          Match: {confidence}%
        </Tag>
      )
    } else if (confidence >= 50) {
      return (
        <Tag icon={<QuestionCircleOutlined />} color="warning">
          Match: {confidence}%
        </Tag>
      )
    } else {
      return (
        <Tag icon={<QuestionCircleOutlined />} color="default">
          Match: {confidence}%
        </Tag>
      )
    }
  }

  const sampleTooltip =
    sampleValues.length > 0
      ? `Sample values: ${sampleValues.join(', ')}`
      : 'No sample values available'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '12px 16px',
        borderBottom: '1px solid #f0f0f0',
        gap: 16,
      }}
    >
      {/* Left side - System field info */}
      <div style={{ flex: '0 0 200px' }}>
        <Space>
          {iconMap[field.icon] || <FileTextOutlined />}
          <span style={{ fontWeight: 500 }}>
            {field.label}
            {field.required && <span style={{ color: '#ff4d4f', marginLeft: 4 }}>*</span>}
          </span>
        </Space>
        <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
          ({field.labelVi})
        </div>
      </div>

      {/* Right side - Column selection */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 12 }}>
        <Tooltip title={selectedColumn ? sampleTooltip : undefined}>
          <Select
            style={{ flex: 1, maxWidth: 300 }}
            placeholder="Select column..."
            value={selectedColumn}
            onChange={(value) => onSelect(field.key, value)}
            allowClear
            showSearch
            optionFilterProp="label"
          >
            {sortedOptions.map((opt) => (
              <Option key={opt.value} value={opt.value} label={opt.label} disabled={opt.disabled}>
                <span style={{ opacity: opt.disabled ? 0.5 : 1 }}>{opt.label}</span>
                {opt.score >= 50 && !opt.disabled && (
                  <Tag color="blue" style={{ marginLeft: 8, fontSize: 10 }}>
                    Suggested
                  </Tag>
                )}
              </Option>
            ))}
          </Select>
        </Tooltip>
        {getConfidenceTag()}
      </div>
    </div>
  )
}
