import { useMemo } from 'react'
import { Table, Alert, Checkbox, Input, Typography, Space, Tag } from 'antd'
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { SYSTEM_FIELDS } from './fieldConfig'
import { ValidationWarning, HeaderDiscoveryResult } from './types'

const { Text, Title } = Typography

interface PreviewStepProps {
  headerDiscovery: HeaderDiscoveryResult
  columnMapping: Record<string, string>
  sampleData: any[][]
  headerRow: number
  saveAsTemplate: boolean
  templateName: string
  onSaveAsTemplateChange: (value: boolean) => void
  onTemplateNameChange: (value: string) => void
}

function validateMapping(
  mapping: Record<string, string>,
  sampleData: any[][],
  columns: string[]
): ValidationWarning[] {
  const warnings: ValidationWarning[] = []

  // Check required fields
  for (const field of SYSTEM_FIELDS) {
    if (field.required && !mapping[field.key]) {
      warnings.push({
        field: field.key,
        type: 'missing_required',
        message: `${field.label} is required`,
        severity: 'error',
      })
    }
  }

  // Check for empty values in mapped columns
  for (const [fieldKey, colName] of Object.entries(mapping)) {
    const colIndex = columns.indexOf(colName)
    if (colIndex >= 0) {
      const emptyCount = sampleData.filter((row) => !row[colIndex] || row[colIndex] === '').length
      const emptyPercent = (emptyCount / sampleData.length) * 100

      if (emptyPercent > 50) {
        warnings.push({
          field: fieldKey,
          type: 'empty_values',
          message: `${Math.round(emptyPercent)}% of values are empty`,
          severity: 'warning',
        })
      }
    }
  }

  return warnings
}

export default function PreviewStep({
  headerDiscovery,
  columnMapping,
  sampleData,
  headerRow,
  saveAsTemplate,
  templateName,
  onSaveAsTemplateChange,
  onTemplateNameChange,
}: PreviewStepProps) {
  const columns = headerDiscovery.column_names

  // Validate mapping
  const warnings = useMemo(() => {
    return validateMapping(columnMapping, sampleData, columns)
  }, [columnMapping, sampleData, columns])

  const errors = warnings.filter((w) => w.severity === 'error')
  const warningItems = warnings.filter((w) => w.severity === 'warning')

  // Build full preview data (10 rows)
  const previewData = useMemo(() => {
    return sampleData.slice(0, 10).map((row, idx) => {
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
  const previewColumns = SYSTEM_FIELDS.filter((field) => columnMapping[field.key]).map((field) => ({
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
      <span style={{ color: value === '---' || !value ? '#999' : 'inherit' }}>
        {String(value ?? '---')}
      </span>
    ),
  }))

  // Mapping summary
  const mappedFields = SYSTEM_FIELDS.filter((f) => columnMapping[f.key])

  return (
    <div>
      {/* Summary */}
      <div style={{ marginBottom: 24 }}>
        <Title level={5}>Mapping Summary</Title>
        <Space wrap>
          {mappedFields.map((field) => (
            <Tag key={field.key} color="blue" icon={<CheckCircleOutlined />}>
              {field.label}: {columnMapping[field.key]}
            </Tag>
          ))}
        </Space>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">
            Header row: {headerRow} | Sheet: {headerDiscovery.sheet_name} | Data starts at row:{' '}
            {headerDiscovery.data_start_row}
          </Text>
        </div>
      </div>

      {/* Validation alerts */}
      {errors.length > 0 && (
        <Alert
          message="Validation Errors"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {errors.map((err, idx) => (
                <li key={idx}>
                  <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                  {err.message}
                </li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {warningItems.length > 0 && (
        <Alert
          message="Warnings"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              {warningItems.map((warn, idx) => (
                <li key={idx}>
                  <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
                  {SYSTEM_FIELDS.find((f) => f.key === warn.field)?.label}: {warn.message}
                </li>
              ))}
            </ul>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {errors.length === 0 && warningItems.length === 0 && (
        <Alert
          message="All validations passed"
          description="Your column mapping looks good. You can proceed to process the file."
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Data Preview */}
      <div style={{ marginBottom: 24 }}>
        <Title level={5}>Data Preview (First 10 rows)</Title>
        <Table
          columns={previewColumns}
          dataSource={previewData}
          pagination={false}
          size="small"
          bordered
          scroll={{ x: 'max-content' }}
        />
      </div>

      {/* Save as template option */}
      <div
        style={{
          padding: 16,
          background: '#fafafa',
          borderRadius: 8,
          border: '1px solid #d9d9d9',
        }}
      >
        <Checkbox checked={saveAsTemplate} onChange={(e) => onSaveAsTemplateChange(e.target.checked)}>
          Save this mapping as a template for future uploads
        </Checkbox>
        {saveAsTemplate && (
          <Input
            placeholder="Template name (e.g., 'Standard BOQ Format')"
            value={templateName}
            onChange={(e) => onTemplateNameChange(e.target.value)}
            style={{ marginTop: 12, maxWidth: 400 }}
          />
        )}
      </div>
    </div>
  )
}
