import { useState } from 'react'
import {
  Table,
  Button,
  Tag,
  Modal,
  Form,
  Input,
  Space,
  Statistic,
  Card,
  Row,
  Col,
  Progress,
  message,
  Select,
  Tooltip,
  Popconfirm,
} from 'antd'
import {
  CheckOutlined,
  CloseOutlined,
  EditOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { pendingItemsService, PendingItem } from '@/services/pendingItemsService'

export default function PendingItemsReview() {
  const [selectedItem, setSelectedItem] = useState<PendingItem | null>(null)
  const [reviewModalVisible, setReviewModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [statusFilter, setStatusFilter] = useState<string>('PENDING')
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  // Fetch pending items
  const { data: items, isLoading, refetch } = useQuery({
    queryKey: ['pendingItems', statusFilter],
    queryFn: () => pendingItemsService.list({ status: statusFilter, limit: 200 }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['pendingItemsStats'],
    queryFn: pendingItemsService.getStats,
  })

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (data: { id: number; notes?: string }) =>
      pendingItemsService.approve(data.id, { reviewer_id: 1, notes: data.notes }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pendingItems'] })
      queryClient.invalidateQueries({ queryKey: ['pendingItemsStats'] })
      message.success(`Item approved! Work code: ${result.work_code}`)
    },
    onError: (error: Error) => {
      message.error(`Failed to approve: ${error.message}`)
    },
  })

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (data: { id: number; notes: string }) =>
      pendingItemsService.reject(data.id, { reviewer_id: 1, notes: data.notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingItems'] })
      queryClient.invalidateQueries({ queryKey: ['pendingItemsStats'] })
      message.success('Item rejected')
      setReviewModalVisible(false)
    },
    onError: (error: Error) => {
      message.error(`Failed to reject: ${error.message}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: { id: number; updates: Partial<PendingItem> }) =>
      pendingItemsService.update(data.id, data.updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pendingItems'] })
      message.success('Item updated')
      setEditModalVisible(false)
    },
    onError: (error: Error) => {
      message.error(`Failed to update: ${error.message}`)
    },
  })

  // Bulk approve mutation
  const bulkApproveMutation = useMutation({
    mutationFn: (ids: number[]) => pendingItemsService.bulkApprove(ids, 1),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pendingItems'] })
      queryClient.invalidateQueries({ queryKey: ['pendingItemsStats'] })
      message.success(`Approved ${result.approved} of ${result.total} items`)
      setSelectedRowKeys([])
    },
    onError: (error: Error) => {
      message.error(`Bulk approve failed: ${error.message}`)
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
      render: (text: string, record: PendingItem) => (
        <Tooltip title={record.original_description || text}>
          <span>{text}</span>
        </Tooltip>
      ),
    },
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
      width: 100,
    },
    {
      title: 'Unit',
      dataIndex: 'unit_standard',
      key: 'unit_standard',
      width: 80,
    },
    {
      title: 'Quality Score',
      dataIndex: 'quality_score',
      key: 'quality_score',
      width: 130,
      sorter: (a: PendingItem, b: PendingItem) =>
        (a.quality_score || 0) - (b.quality_score || 0),
      render: (score: number) => (
        <Progress
          percent={Math.round(score || 0)}
          size="small"
          status={
            score >= 75 ? 'success' : score >= 50 ? 'normal' : 'exception'
          }
          format={(p) => `${p}%`}
        />
      ),
    },
    {
      title: 'Indicators',
      dataIndex: 'quality_indicators',
      key: 'quality_indicators',
      width: 200,
      render: (indicators: string) => {
        const parsed = parseIndicators(indicators)
        return (
          <Space wrap size="small">
            {parsed.has_verb && <Tag color="green">Verb</Tag>}
            {parsed.has_material && <Tag color="blue">Material</Tag>}
            {parsed.has_specs && <Tag color="orange">Specs</Tag>}
            {parsed.has_location && <Tag color="purple">Location</Tag>}
            {parsed.has_dimension && <Tag color="cyan">Dimension</Tag>}
          </Space>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const colors: Record<string, string> = {
          PENDING: 'gold',
          APPROVED: 'green',
          REJECTED: 'red',
        }
        return <Tag color={colors[status] || 'default'}>{status}</Tag>
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      render: (_: unknown, record: PendingItem) =>
        record.status === 'PENDING' ? (
          <Space size="small">
            <Button
              type="primary"
              icon={<CheckOutlined />}
              size="small"
              onClick={() => approveMutation.mutate({ id: record.pending_id })}
              loading={approveMutation.isPending}
            >
              Approve
            </Button>
            <Button
              icon={<EditOutlined />}
              size="small"
              onClick={() => {
                setSelectedItem(record)
                editForm.setFieldsValue({
                  description: record.description,
                  sec_code: record.sec_code,
                  unit_standard: record.unit_standard,
                })
                setEditModalVisible(true)
              }}
            />
            <Button
              danger
              icon={<CloseOutlined />}
              size="small"
              onClick={() => {
                setSelectedItem(record)
                setReviewModalVisible(true)
              }}
            />
          </Space>
        ) : (
          <span style={{ color: '#999' }}>
            {record.status === 'APPROVED' ? 'Approved' : 'Rejected'}
          </span>
        ),
    },
  ]

  const approvalRate =
    stats && stats.total > 0
      ? Math.round((stats.approved / stats.total) * 100)
      : 0

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Pending Items Review</h1>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pending"
              value={stats?.pending || 0}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Approved"
              value={stats?.approved || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Rejected"
              value={stats?.rejected || 0}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Approval Rate"
              value={approvalRate}
              suffix="%"
              valueStyle={{ color: approvalRate >= 50 ? '#52c41a' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Bulk Actions */}
      <Row justify="space-between" style={{ marginBottom: 16 }}>
        <Col>
          <Space>
            <Select
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 150 }}
              options={[
                { value: 'PENDING', label: 'Pending' },
                { value: 'APPROVED', label: 'Approved' },
                { value: 'REJECTED', label: 'Rejected' },
                { value: '', label: 'All' },
              ]}
            />
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          </Space>
        </Col>
        <Col>
          {selectedRowKeys.length > 0 && (
            <Space>
              <Popconfirm
                title={`Approve ${selectedRowKeys.length} items?`}
                onConfirm={() => bulkApproveMutation.mutate(selectedRowKeys)}
                icon={<ExclamationCircleOutlined style={{ color: '#52c41a' }} />}
              >
                <Button
                  type="primary"
                  loading={bulkApproveMutation.isPending}
                >
                  Bulk Approve ({selectedRowKeys.length})
                </Button>
              </Popconfirm>
              <Button onClick={() => setSelectedRowKeys([])}>
                Clear Selection
              </Button>
            </Space>
          )}
        </Col>
      </Row>

      {/* Table */}
      <Table
        rowKey="pending_id"
        columns={columns}
        dataSource={items}
        loading={isLoading}
        rowSelection={
          statusFilter === 'PENDING'
            ? {
                selectedRowKeys,
                onChange: (keys) => setSelectedRowKeys(keys as number[]),
              }
            : undefined
        }
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 1100 }}
      />

      {/* Reject Modal */}
      <Modal
        title="Reject Item"
        open={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        footer={null}
      >
        {selectedItem && (
          <Form
            form={form}
            onFinish={(values) => {
              rejectMutation.mutate({
                id: selectedItem.pending_id,
                notes: values.notes,
              })
            }}
          >
            <Form.Item label="Description">
              <Input.TextArea
                value={selectedItem.description}
                disabled
                rows={3}
              />
            </Form.Item>
            <Form.Item
              label="Rejection Reason"
              name="notes"
              rules={[{ required: true, message: 'Please provide a reason' }]}
            >
              <Input.TextArea
                placeholder="Enter reason for rejection..."
                rows={3}
              />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  danger
                  loading={rejectMutation.isPending}
                >
                  Confirm Rejection
                </Button>
                <Button onClick={() => setReviewModalVisible(false)}>
                  Cancel
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="Edit Before Approval"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        {selectedItem && (
          <Form
            form={editForm}
            layout="vertical"
            onFinish={(values) => {
              updateMutation.mutate({
                id: selectedItem.pending_id,
                updates: values,
              })
            }}
          >
            <Form.Item
              label="Description"
              name="description"
              rules={[{ required: true }]}
            >
              <Input.TextArea rows={3} />
            </Form.Item>
            <Form.Item label="SEC Code" name="sec_code">
              <Input placeholder="e.g., SEC-01" />
            </Form.Item>
            <Form.Item label="Unit" name="unit_standard">
              <Input placeholder="e.g., m3, kg" />
            </Form.Item>
            <Form.Item>
              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={updateMutation.isPending}
                >
                  Save Changes
                </Button>
                <Button
                  type="primary"
                  onClick={() => {
                    editForm.validateFields().then((values) => {
                      updateMutation.mutate(
                        {
                          id: selectedItem.pending_id,
                          updates: values,
                        },
                        {
                          onSuccess: () => {
                            approveMutation.mutate({ id: selectedItem.pending_id })
                            setEditModalVisible(false)
                          },
                        }
                      )
                    })
                  }}
                >
                  Save & Approve
                </Button>
                <Button onClick={() => setEditModalVisible(false)}>
                  Cancel
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  )
}
