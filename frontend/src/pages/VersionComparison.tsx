import { useState } from 'react'
import {
  Card,
  Table,
  Select,
  Button,
  Space,
  Tag,
  Typography,
  Statistic,
  Row,
  Col,
  Empty,
  Spin,
  message,
} from 'antd'
import {
  SwapOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlusCircleOutlined,
  MinusCircleOutlined,
  CheckCircleOutlined,
  FileExcelOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useParams, useSearchParams } from 'react-router-dom'
import api from '@/services/api'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

interface Version {
  version_id: number
  version_number: number
  version_name: string | null
  file_id: number
  file_name: string | null
  created_at: string | null
  notes: string | null
}

interface ComparisonItem {
  description: string
  normalized_description: string | null
  sec_code: string | null
  status: 'unchanged' | 'price_changed' | 'quantity_changed' | 'added' | 'removed'
  v1_quantity: number | null
  v2_quantity: number | null
  v1_unit_price: number | null
  v2_unit_price: number | null
  v1_amount: number | null
  v2_amount: number | null
  price_diff_percent: number | null
  quantity_diff_percent: number | null
}

interface ComparisonSummary {
  v1_version_number: number
  v2_version_number: number
  v1_total_items: number
  v2_total_items: number
  v1_total_amount: number
  v2_total_amount: number
  amount_diff: number
  amount_diff_percent: number
  unchanged_count: number
  price_changed_count: number
  quantity_changed_count: number
  added_count: number
  removed_count: number
}

// Status colors and icons
const STATUS_CONFIG: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  unchanged: { color: 'default', icon: <CheckCircleOutlined />, label: 'Unchanged' },
  price_changed: { color: 'orange', icon: <SwapOutlined />, label: 'Price Changed' },
  quantity_changed: { color: 'blue', icon: <SwapOutlined />, label: 'Qty Changed' },
  added: { color: 'green', icon: <PlusCircleOutlined />, label: 'Added' },
  removed: { color: 'red', icon: <MinusCircleOutlined />, label: 'Removed' },
}

export default function VersionComparison() {
  const { projectId } = useParams<{ projectId: string }>()
  const [searchParams, setSearchParams] = useSearchParams()

  const [v1, setV1] = useState<number | undefined>(
    searchParams.get('v1') ? parseInt(searchParams.get('v1')!) : undefined
  )
  const [v2, setV2] = useState<number | undefined>(
    searchParams.get('v2') ? parseInt(searchParams.get('v2')!) : undefined
  )
  const [statusFilter, setStatusFilter] = useState<string | undefined>()

  // Fetch versions for project
  const { data: versionsData, isLoading: versionsLoading } = useQuery({
    queryKey: ['projectVersions', projectId],
    queryFn: async () => {
      const response = await api.get(`/projects/${projectId}/versions`)
      return response.data as { project_id: number; versions: Version[]; total: number }
    },
    enabled: !!projectId,
  })

  // Fetch comparison
  const { data: comparisonData, isLoading: comparisonLoading } = useQuery({
    queryKey: ['versionComparison', projectId, v1, v2, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (v1) params.append('v1', v1.toString())
      if (v2) params.append('v2', v2.toString())
      if (statusFilter) params.append('status_filter', statusFilter)
      params.append('limit', '500')

      const response = await api.get(`/projects/${projectId}/versions/compare?${params}`)
      return response.data as {
        project_id: number
        summary: ComparisonSummary
        items: ComparisonItem[]
        total_items: number
      }
    },
    enabled: !!projectId && !!v1 && !!v2,
  })

  const handleCompare = () => {
    if (!v1 || !v2) {
      message.warning('Please select two versions to compare')
      return
    }
    if (v1 === v2) {
      message.warning('Please select different versions')
      return
    }
    // Update URL params
    setSearchParams({ v1: v1.toString(), v2: v2.toString() })
  }

  const columns: ColumnsType<ComparisonItem> = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 130,
      filters: Object.entries(STATUS_CONFIG).map(([key, config]) => ({
        text: config.label,
        value: key,
      })),
      onFilter: (value, record) => record.status === value,
      render: (status: string) => {
        const config = STATUS_CONFIG[status]
        return config ? (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        ) : (
          status
        )
      },
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
      render: (desc: string, record) => (
        <Space direction="vertical" size="small">
          <Text>{desc}</Text>
          {record.sec_code && (
            <Tag color="blue" style={{ fontSize: 10 }}>
              {record.sec_code}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'V1 Price',
      dataIndex: 'v1_unit_price',
      key: 'v1_unit_price',
      width: 120,
      align: 'right',
      render: (price: number | null) =>
        price !== null ? price.toLocaleString('vi-VN') : '-',
    },
    {
      title: 'V2 Price',
      dataIndex: 'v2_unit_price',
      key: 'v2_unit_price',
      width: 120,
      align: 'right',
      render: (price: number | null) =>
        price !== null ? price.toLocaleString('vi-VN') : '-',
    },
    {
      title: 'Price Diff',
      dataIndex: 'price_diff_percent',
      key: 'price_diff_percent',
      width: 100,
      align: 'right',
      render: (diff: number | null) => {
        if (diff === null) return '-'
        const color = diff > 0 ? '#f5222d' : diff < 0 ? '#52c41a' : undefined
        const icon = diff > 0 ? <ArrowUpOutlined /> : diff < 0 ? <ArrowDownOutlined /> : null
        return (
          <Text style={{ color }}>
            {icon} {Math.abs(diff).toFixed(1)}%
          </Text>
        )
      },
    },
    {
      title: 'V1 Qty',
      dataIndex: 'v1_quantity',
      key: 'v1_quantity',
      width: 100,
      align: 'right',
      render: (qty: number | null) =>
        qty !== null ? qty.toLocaleString() : '-',
    },
    {
      title: 'V2 Qty',
      dataIndex: 'v2_quantity',
      key: 'v2_quantity',
      width: 100,
      align: 'right',
      render: (qty: number | null) =>
        qty !== null ? qty.toLocaleString() : '-',
    },
    {
      title: 'Qty Diff',
      dataIndex: 'quantity_diff_percent',
      key: 'quantity_diff_percent',
      width: 100,
      align: 'right',
      render: (diff: number | null) => {
        if (diff === null) return '-'
        const color = diff > 0 ? '#52c41a' : diff < 0 ? '#f5222d' : undefined
        const icon = diff > 0 ? <ArrowUpOutlined /> : diff < 0 ? <ArrowDownOutlined /> : null
        return (
          <Text style={{ color }}>
            {icon} {Math.abs(diff).toFixed(1)}%
          </Text>
        )
      },
    },
  ]

  // Row styling based on status
  const getRowClassName = (record: ComparisonItem) => {
    const statusClasses: Record<string, string> = {
      added: 'row-added',
      removed: 'row-removed',
      price_changed: 'row-changed',
      quantity_changed: 'row-changed',
    }
    return statusClasses[record.status] || ''
  }

  return (
    <div>
      <Title level={3}>
        <SwapOutlined /> Version Comparison
      </Title>

      {/* Version Selection */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="large" wrap>
          <div>
            <Text type="secondary">Version 1 (Base):</Text>
            <br />
            <Select
              style={{ width: 250 }}
              placeholder="Select base version"
              value={v1}
              onChange={setV1}
              loading={versionsLoading}
              options={versionsData?.versions?.map((v) => ({
                label: `v${v.version_number} - ${v.version_name || v.file_name || 'Unnamed'}`,
                value: v.version_number,
              }))}
            />
          </div>
          <div>
            <Text type="secondary">Version 2 (Compare):</Text>
            <br />
            <Select
              style={{ width: 250 }}
              placeholder="Select compare version"
              value={v2}
              onChange={setV2}
              loading={versionsLoading}
              options={versionsData?.versions?.map((v) => ({
                label: `v${v.version_number} - ${v.version_name || v.file_name || 'Unnamed'}`,
                value: v.version_number,
              }))}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <Button
              type="primary"
              icon={<SwapOutlined />}
              onClick={handleCompare}
              disabled={!v1 || !v2}
            >
              Compare Versions
            </Button>
          </div>
        </Space>
      </Card>

      {/* Loading State */}
      {comparisonLoading && (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      )}

      {/* No comparison yet */}
      {!comparisonLoading && !comparisonData && (
        <Card>
          <Empty description="Select two versions to compare" />
        </Card>
      )}

      {/* Comparison Results */}
      {comparisonData && (
        <>
          {/* Summary Cards */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Unchanged"
                  value={comparisonData.summary.unchanged_count}
                  valueStyle={{ color: '#8c8c8c' }}
                  prefix={<CheckCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Price Changed"
                  value={comparisonData.summary.price_changed_count}
                  valueStyle={{ color: '#fa8c16' }}
                  prefix={<SwapOutlined />}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Qty Changed"
                  value={comparisonData.summary.quantity_changed_count}
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<SwapOutlined />}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Added"
                  value={comparisonData.summary.added_count}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<PlusCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Removed"
                  value={comparisonData.summary.removed_count}
                  valueStyle={{ color: '#f5222d' }}
                  prefix={<MinusCircleOutlined />}
                />
              </Card>
            </Col>
            <Col span={4}>
              <Card size="small">
                <Statistic
                  title="Amount Diff"
                  value={comparisonData.summary.amount_diff_percent}
                  precision={1}
                  suffix="%"
                  valueStyle={{
                    color:
                      comparisonData.summary.amount_diff > 0
                        ? '#f5222d'
                        : comparisonData.summary.amount_diff < 0
                        ? '#52c41a'
                        : undefined,
                  }}
                  prefix={
                    comparisonData.summary.amount_diff > 0 ? (
                      <ArrowUpOutlined />
                    ) : comparisonData.summary.amount_diff < 0 ? (
                      <ArrowDownOutlined />
                    ) : null
                  }
                />
              </Card>
            </Col>
          </Row>

          {/* Filter by Status */}
          <Card style={{ marginBottom: 16 }}>
            <Space>
              <Text>Filter by Status:</Text>
              <Select
                style={{ width: 200 }}
                placeholder="All statuses"
                allowClear
                value={statusFilter}
                onChange={setStatusFilter}
                options={Object.entries(STATUS_CONFIG).map(([key, config]) => ({
                  label: config.label,
                  value: key,
                }))}
              />
              <Text type="secondary">
                Showing {comparisonData.items.length} of {comparisonData.total_items} items
              </Text>
            </Space>
          </Card>

          {/* Comparison Table */}
          <Card>
            <Table
              columns={columns}
              dataSource={comparisonData.items}
              rowKey={(record) => record.description}
              rowClassName={getRowClassName}
              size="small"
              scroll={{ x: 1200 }}
              pagination={{
                pageSize: 50,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} items`,
              }}
            />
          </Card>

          {/* Custom CSS for row highlighting */}
          <style>{`
            .row-added {
              background-color: #f6ffed !important;
            }
            .row-removed {
              background-color: #fff1f0 !important;
            }
            .row-changed {
              background-color: #fffbe6 !important;
            }
          `}</style>
        </>
      )}
    </div>
  )
}
