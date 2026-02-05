import { useState } from 'react'
import {
  Table,
  Button,
  Tag,
  Card,
  Row,
  Col,
  Statistic,
  Select,
  Space,
  message,
  Popconfirm,
  Tooltip,
  Progress,
} from 'antd'
import {
  DeleteOutlined,
  ReloadOutlined,
  ArrowUpOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { quarantineService, QuarantineLog } from '@/services/quarantineService'

export default function QuarantineLogPage() {
  const [reasonFilter, setReasonFilter] = useState<string>('')
  const queryClient = useQueryClient()

  // Fetch quarantine logs
  const { data: logs, isLoading, refetch } = useQuery({
    queryKey: ['quarantineLogs', reasonFilter],
    queryFn: () =>
      quarantineService.list({
        rejection_reason: reasonFilter || undefined,
        limit: 200,
      }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['quarantineStats'],
    queryFn: quarantineService.getStats,
  })

  // Fetch rejection reasons for filter
  const { data: reasons } = useQuery({
    queryKey: ['quarantineReasons'],
    queryFn: quarantineService.getReasons,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: quarantineService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quarantineLogs'] })
      queryClient.invalidateQueries({ queryKey: ['quarantineStats'] })
      message.success('Log entry deleted')
    },
    onError: (error: Error) => {
      message.error(`Failed to delete: ${error.message}`)
    },
  })

  // Promote to pending mutation
  const promoteMutation = useMutation({
    mutationFn: quarantineService.promoteToPending,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['quarantineLogs'] })
      queryClient.invalidateQueries({ queryKey: ['quarantineStats'] })
      queryClient.invalidateQueries({ queryKey: ['pendingItemsStats'] })
      message.success(`Promoted to pending. ID: ${result.pending_id}`)
    },
    onError: (error: Error) => {
      message.error(`Failed to promote: ${error.message}`)
    },
  })

  // Parse quality indicators
  const parseIndicators = (indicatorsStr?: string) => {
    if (!indicatorsStr) return {}
    try {
      return JSON.parse(indicatorsStr)
    } catch {
      return {}
    }
  }

  // Columns
  const columns = [
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      width: 300,
      render: (text: string) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Rejection Reason',
      dataIndex: 'rejection_reason',
      key: 'rejection_reason',
      width: 200,
      render: (reason: string) => (
        <Tag color="red">{reason || 'Unknown'}</Tag>
      ),
    },
    {
      title: 'Quality Score',
      dataIndex: 'quality_score',
      key: 'quality_score',
      width: 120,
      sorter: (a: QuarantineLog, b: QuarantineLog) =>
        (a.quality_score || 0) - (b.quality_score || 0),
      render: (score: number) => (
        <Progress
          percent={Math.round(score || 0)}
          size="small"
          status="exception"
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: 'Forbidden Pattern',
      dataIndex: 'matched_forbidden_pattern',
      key: 'matched_forbidden_pattern',
      width: 150,
      render: (pattern: string) =>
        pattern ? (
          <Tag color="volcano">{pattern}</Tag>
        ) : (
          <span style={{ color: '#999' }}>-</span>
        ),
    },
    {
      title: 'Indicators',
      dataIndex: 'quality_indicators',
      key: 'quality_indicators',
      width: 180,
      render: (indicators: string) => {
        const parsed = parseIndicators(indicators)
        const missing = []
        if (!parsed.has_verb) missing.push('Verb')
        if (!parsed.has_material) missing.push('Material')
        if (!parsed.has_specs) missing.push('Specs')

        return (
          <Space wrap size="small">
            {missing.map((m) => (
              <Tag key={m} color="default">
                No {m}
              </Tag>
            ))}
          </Space>
        )
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      render: (date: string) =>
        date ? new Date(date).toLocaleString() : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_: unknown, record: QuarantineLog) => (
        <Space size="small">
          <Tooltip title="Promote to Pending">
            <Popconfirm
              title="Promote this item to pending for manual review?"
              onConfirm={() => promoteMutation.mutate(record.log_id)}
            >
              <Button
                icon={<ArrowUpOutlined />}
                size="small"
                loading={promoteMutation.isPending}
              />
            </Popconfirm>
          </Tooltip>
          <Tooltip title="Delete">
            <Popconfirm
              title="Delete this log entry?"
              onConfirm={() => deleteMutation.mutate(record.log_id)}
            >
              <Button
                danger
                icon={<DeleteOutlined />}
                size="small"
                loading={deleteMutation.isPending}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ]

  // Reason statistics for display
  const reasonStats = stats?.by_reason || {}
  const topReasons = Object.entries(reasonStats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Quarantine Log</h1>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Statistic
              title="Total Quarantined"
              value={stats?.total || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={16}>
          <Card title="Top Rejection Reasons" size="small">
            <Space wrap>
              {topReasons.map(([reason, count]) => (
                <Tag
                  key={reason}
                  color="red"
                  style={{ cursor: 'pointer' }}
                  onClick={() => setReasonFilter(reason)}
                >
                  {reason}: {count}
                </Tag>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Row style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <Select
              value={reasonFilter}
              onChange={setReasonFilter}
              style={{ width: 250 }}
              placeholder="Filter by reason"
              allowClear
              options={[
                { value: '', label: 'All Reasons' },
                ...(reasons?.map((r) => ({ value: r, label: r })) || []),
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Table */}
      <Table
        rowKey="log_id"
        columns={columns}
        dataSource={logs}
        loading={isLoading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 1200 }}
      />
    </div>
  )
}
