import { useMemo } from 'react'
import { Progress, Table, Typography, Divider } from 'antd'
import MappingFieldRow from './MappingFieldRow'
import { SYSTEM_FIELDS } from './fieldConfig'
import { HeaderDiscoveryResult } from './types'

const { Text, Title } = Typography

interface ColumnMappingStepProps {
  headerDiscovery: HeaderDiscoveryResult
  columnMapping: Record<string, string>
  sampleData: any[][]
  onMappingChange: (mapping: Record<string, string>) => void
}

export default function ColumnMappingStep({
  headerDiscovery,
  columnMapping,
  sampleData,
  onMappingChange,
}: ColumnMappingStepProps) {
  const columns = headerDiscovery.column_names

  // Calculate mapping progress
  const mappedCount = Object.keys(columnMapping).filter((k) => columnMapping[k]).length
  const totalFields = SYSTEM_FIELDS.length
  const requiredFields = SYSTEM_FIELDS.filter((f) => f.required)
  const mappedRequiredCount = requiredFields.filter((f) => columnMapping[f.key]).length

  // Get set of already-selected columns
  const selectedColumns = useMemo(() => {
    return new Set(Object.values(columnMapping).filter(Boolean))
  }, [columnMapping])

  const handleFieldSelect = (fieldKey: string, column: string | undefined) => {
    const newMapping = { ...columnMapping }
    if (column) {
      newMapping[fieldKey] = column
    } else {
      delete newMapping[fieldKey]
    }
    onMappingChange(newMapping)
  }

  // Build preview data based on current mapping
  const previewData = useMemo(() => {
    return sampleData.slice(0, 5).map((row, idx) => {
      const mappedRow: Record<string, any> = { key: idx }

      for (const field of SYSTEM_FIELDS) {
        const excelColumn = columnMapping[field.key]
        if (excelColumn) {
          const colIndex = columns.indexOf(excelColumn)
          mappedRow[field.key] = colIndex >= 0 ? row[colIndex] : '---'
        } else {
          mappedRow[field.key] = '---'
        }
      }

      return mappedRow
    })
  }, [columnMapping, sampleData, columns])

  // Preview table columns
  const previewColumns = SYSTEM_FIELDS.map((field) => ({
    title: (
      <span>
        {field.label}
        {field.required && <span style={{ color: '#ff4d4f' }}> *</span>}
      </span>
    ),
    dataIndex: field.key,
    key: field.key,
    width: 150,
    render: (value: any) => (
      <span style={{ color: value === '---' ? '#999' : 'inherit' }}>{String(value ?? '---')}</span>
    ),
  }))

  return (
    <div>
      {/* Progress indicator */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
        <Text strong>Progress:</Text>
        <Progress
          percent={Math.round((mappedCount / totalFields) * 100)}
          size="small"
          style={{ flex: 1, maxWidth: 200 }}
          format={() => `${mappedCount}/${totalFields}`}
        />
        {mappedRequiredCount < requiredFields.length && (
          <Text type="danger">
            Required: {mappedRequiredCount}/{requiredFields.length}
          </Text>
        )}
        {mappedRequiredCount === requiredFields.length && (
          <Text type="success">All required fields mapped</Text>
        )}
      </div>

      {/* Mapping fields */}
      <div
        style={{
          border: '1px solid #d9d9d9',
          borderRadius: 8,
          overflow: 'hidden',
          marginBottom: 24,
        }}
      >
        <div
          style={{
            display: 'flex',
            padding: '12px 16px',
            background: '#fafafa',
            borderBottom: '1px solid #d9d9d9',
            fontWeight: 600,
          }}
        >
          <div style={{ flex: '0 0 200px' }}>SYSTEM FIELD</div>
          <div style={{ flex: 1 }}>EXCEL COLUMN</div>
        </div>
        {SYSTEM_FIELDS.map((field) => (
          <MappingFieldRow
            key={field.key}
            field={field}
            columns={columns}
            selectedColumn={columnMapping[field.key]}
            columnTypeHints={headerDiscovery.column_type_hints}
            selectedColumns={selectedColumns}
            sampleData={sampleData}
            onSelect={handleFieldSelect}
          />
        ))}
      </div>

      <Divider />

      {/* Live Preview */}
      <div>
        <Title level={5} style={{ marginBottom: 12 }}>
          Live Preview (First 5 rows)
        </Title>
        <Table
          columns={previewColumns}
          dataSource={previewData}
          pagination={false}
          size="small"
          bordered
          scroll={{ x: 'max-content' }}
        />
      </div>
    </div>
  )
}
