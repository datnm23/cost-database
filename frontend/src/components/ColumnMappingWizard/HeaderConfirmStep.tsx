import { useState } from 'react'
import { Alert, Radio, Table, Select, Space, Tag, Typography } from 'antd'
import { CheckCircleOutlined } from '@ant-design/icons'
import { HeaderDiscoveryResult } from './types'

const { Text } = Typography

interface HeaderConfirmStepProps {
  headerDiscovery: HeaderDiscoveryResult
  sampleData: any[][]
  allRows: any[][]
  onHeaderRowChange: (row: number) => void
  selectedHeaderRow: number
}

export default function HeaderConfirmStep({
  headerDiscovery,
  sampleData: _sampleData,
  allRows,
  onHeaderRowChange,
  selectedHeaderRow,
}: HeaderConfirmStepProps) {
  // sampleData is available for extended preview features
  void _sampleData
  const [useDetected, setUseDetected] = useState(true)

  const confidenceColor =
    headerDiscovery.confidence_score >= 90
      ? 'success'
      : headerDiscovery.confidence_score >= 70
      ? 'warning'
      : 'default'

  // Generate row options for manual selection (first 20 rows)
  const rowOptions = allRows.slice(0, 20).map((row, idx) => ({
    value: idx + 1,
    label: `Row ${idx + 1}: ${row.slice(0, 4).join(' | ')}...`,
    preview: row,
  }))

  // Get the header row data for preview
  const headerRowData =
    selectedHeaderRow > 0 && selectedHeaderRow <= allRows.length
      ? allRows[selectedHeaderRow - 1]
      : headerDiscovery.column_names

  // Table columns for header preview
  const previewColumns = headerRowData.map((_col: any, idx: number) => ({
    title: `Col ${idx + 1}`,
    dataIndex: idx.toString(),
    key: idx.toString(),
    width: 120,
    ellipsis: true,
  }))

  // Data for preview table (just the header row)
  const previewData = [
    headerRowData.reduce((acc: any, val: any, idx: number) => {
      acc[idx.toString()] = val
      acc.key = 'header'
      return acc
    }, {}),
  ]

  const handleSelectionChange = (detected: boolean) => {
    setUseDetected(detected)
    if (detected) {
      onHeaderRowChange(headerDiscovery.header_row)
    }
  }

  return (
    <div>
      <Alert
        message="Header Detection"
        description={
          <Space direction="vertical" size="small">
            <Text>
              <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
              Header detected at <Text strong>row {headerDiscovery.header_row}</Text>
              <Tag color={confidenceColor} style={{ marginLeft: 8 }}>
                Confidence: {Math.round(headerDiscovery.confidence_score)}%
              </Tag>
            </Text>
            {headerDiscovery.is_merged_header && (
              <Text type="secondary">Note: Merged header cells were detected</Text>
            )}
            <Text type="secondary">Sheet: {headerDiscovery.sheet_name}</Text>
          </Space>
        }
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <div style={{ marginBottom: 24 }}>
        <Text strong style={{ display: 'block', marginBottom: 12 }}>
          Detected Header Row Preview:
        </Text>
        <Table
          columns={previewColumns}
          dataSource={previewData}
          pagination={false}
          size="small"
          bordered
          scroll={{ x: 'max-content' }}
          style={{
            marginBottom: 24,
            border: '2px solid #1890ff',
            borderRadius: 8,
          }}
        />
      </div>

      <div style={{ marginBottom: 24 }}>
        <Radio.Group
          value={useDetected}
          onChange={(e) => handleSelectionChange(e.target.value)}
        >
          <Space direction="vertical">
            <Radio value={true}>
              Use detected row ({headerDiscovery.header_row})
              <Tag color="blue" style={{ marginLeft: 8 }}>
                Recommended
              </Tag>
            </Radio>
            <Radio value={false}>Select different row:</Radio>
          </Space>
        </Radio.Group>

        {!useDetected && (
          <Select
            style={{ width: '100%', marginTop: 12 }}
            placeholder="Select header row"
            value={selectedHeaderRow}
            onChange={(value) => onHeaderRowChange(value)}
            options={rowOptions.map((opt) => ({
              value: opt.value,
              label: opt.label,
            }))}
          />
        )}
      </div>

      {headerDiscovery.sheets.length > 1 && (
        <Alert
          message="Multiple Sheets Available"
          description={
            <div>
              <Text type="secondary">
                Found {headerDiscovery.sheets.length} sheets. Currently using: {headerDiscovery.sheet_name}
              </Text>
              <div style={{ marginTop: 8 }}>
                {headerDiscovery.sheets.map((sheet) => (
                  <Tag
                    key={sheet.index}
                    color={sheet.name === headerDiscovery.sheet_name ? 'blue' : 'default'}
                    style={{ marginRight: 8 }}
                  >
                    {sheet.name}
                    {sheet.skip_reason && ` (${sheet.skip_reason})`}
                  </Tag>
                ))}
              </div>
            </div>
          }
          type="info"
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  )
}
