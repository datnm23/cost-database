import { useState, useEffect, useCallback } from 'react'
import {
  Card,
  Table,
  Button,
  Select,
  Input,
  Space,
  Tag,
  Modal,
  Form,
  InputNumber,
  message,
  Popconfirm,
  Tooltip,
  Badge,
  Drawer,
  Dropdown,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  EditOutlined,
  DeleteOutlined,
  FilterOutlined,
  CheckOutlined,
  SearchOutlined,
  SwapOutlined,
  ThunderboltOutlined,
  FlagOutlined,
  WarningOutlined,
  QuestionCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  lineItemService,
  secCodeService,
  LineItem,
  SECCode,
  ConfidenceRange,
} from '@/services/lineItemService'
import { namingService } from '@/services/namingService'

const { Option } = Select
const { TextArea } = Input

// Flag type icons and colors
const FLAG_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  price_warning: { icon: <WarningOutlined />, color: 'orange', label: 'Price Warning' },
  needs_verify: { icon: <QuestionCircleOutlined />, color: 'blue', label: 'Needs Verify' },
  confirmed: { icon: <CheckCircleOutlined />, color: 'green', label: 'Confirmed' },
  important: { icon: <ExclamationCircleOutlined />, color: 'red', label: 'Important' },
  question: { icon: <QuestionCircleOutlined />, color: 'purple', label: 'Question' },
}

// Confidence score color helper
const getConfidenceColor = (score: number | undefined): string => {
  if (!score) return 'default'
  if (score >= 95) return 'green'
  if (score >= 80) return 'orange'
  return 'red'
}

const getConfidenceLabel = (score: number | undefined): string => {
  if (!score) return 'N/A'
  if (score >= 95) return 'High'
  if (score >= 80) return 'Medium'
  return 'Low'
}

export default function LineItems() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const [form] = Form.useForm()

  // State
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [editingItem, setEditingItem] = useState<LineItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false)
  const [showNormalized, setShowNormalized] = useState(false)
  const [filters, setFilters] = useState({
    file_id: searchParams.get('file_id') ? parseInt(searchParams.get('file_id')!) : undefined,
    project_id: searchParams.get('project_id') ? parseInt(searchParams.get('project_id')!) : undefined,
    sec_code: undefined as string | undefined,
    needs_review: undefined as boolean | undefined,
    confidence_range: undefined as ConfidenceRange | undefined,
    search: '',
  })

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+A to select all visible items
      if ((e.ctrlKey || e.metaKey) && e.key === 'a' && !e.shiftKey) {
        e.preventDefault()
        if (filteredLineItems && filteredLineItems.length > 0) {
          setSelectedRowKeys(filteredLineItems.map(item => item.line_item_id))
          message.info(`Selected ${filteredLineItems.length} items`)
        }
      }
      // Escape to clear selection
      if (e.key === 'Escape') {
        if (selectedRowKeys.length > 0) {
          setSelectedRowKeys([])
          message.info('Selection cleared')
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [filteredLineItems, selectedRowKeys])

  // Fetch line items
  const { data: lineItems, isLoading } = useQuery({
    queryKey: ['lineItems', filters],
    queryFn: () => lineItemService.getLineItems({
      file_id: filters.file_id,
      project_id: filters.project_id,
      sec_code: filters.sec_code,
      needs_review: filters.needs_review,
      confidence_range: filters.confidence_range,
      limit: 1000,
    }),
  })

  // Fetch SEC codes
  const { data: secCodes } = useQuery({
    queryKey: ['secCodes'],
    queryFn: () => secCodeService.getSECCodes(),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<LineItem> }) =>
      lineItemService.updateLineItem(id, data),
    onSuccess: () => {
      message.success('Line item updated successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
      setIsModalOpen(false)
      setEditingItem(null)
    },
    onError: () => {
      message.error('Failed to update line item')
    },
  })

  // Bulk update mutation
  const bulkUpdateMutation = useMutation({
    mutationFn: lineItemService.bulkUpdate,
    onSuccess: () => {
      message.success('Line items updated successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
      setSelectedRowKeys([])
    },
    onError: () => {
      message.error('Failed to update line items')
    },
  })

  // Classify mutation
  const classifyMutation = useMutation({
    mutationFn: lineItemService.classifyLineItem,
    onSuccess: () => {
      message.success('Item classified successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
    },
    onError: () => {
      message.error('Failed to classify item')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: lineItemService.deleteLineItem,
    onSuccess: () => {
      message.success('Line item deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
    },
    onError: () => {
      message.error('Failed to delete line item')
    },
  })

  // Normalize mutation
  const normalizeMutation = useMutation({
    mutationFn: namingService.normalizeLineItem,
    onSuccess: () => {
      message.success('Item normalized successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
    },
    onError: () => {
      message.error('Failed to normalize item')
    },
  })

  // Bulk normalize mutation
  const bulkNormalizeMutation = useMutation({
    mutationFn: namingService.bulkNormalize,
    onSuccess: (data) => {
      message.success(`Normalized ${data.success} items successfully`)
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
      setSelectedRowKeys([])
    },
    onError: () => {
      message.error('Failed to normalize items')
    },
  })

  // Add flag mutation
  const addFlagMutation = useMutation({
    mutationFn: ({ lineItemId, flagType, note }: { lineItemId: number; flagType: string; note?: string }) =>
      lineItemService.createFlag(lineItemId, flagType, note),
    onSuccess: () => {
      message.success('Flag added successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
    },
    onError: () => {
      message.error('Failed to add flag')
    },
  })

  // Bulk add flag mutation
  const bulkAddFlagMutation = useMutation({
    mutationFn: ({ flagType, note }: { flagType: string; note?: string }) =>
      lineItemService.bulkCreateFlags(selectedRowKeys, flagType, note),
    onSuccess: () => {
      message.success('Flags added successfully')
      queryClient.invalidateQueries({ queryKey: ['lineItems'] })
      setSelectedRowKeys([])
    },
    onError: () => {
      message.error('Failed to add flags')
    },
  })

  const handleEdit = (item: LineItem) => {
    setEditingItem(item)
    form.setFieldsValue(item)
    setIsModalOpen(true)
  }

  const handleUpdate = async () => {
    try {
      const values = await form.validateFields()
      if (editingItem) {
        updateMutation.mutate({ id: editingItem.line_item_id, data: values })
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleBulkVerify = () => {
    bulkUpdateMutation.mutate({
      line_item_ids: selectedRowKeys,
      needs_review: false,
    })
  }

  const handleBulkUpdateSEC = (secCode: string) => {
    bulkUpdateMutation.mutate({
      line_item_ids: selectedRowKeys,
      sec_code: secCode,
    })
  }

  const handleClassify = (id: number) => {
    classifyMutation.mutate(id)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleNormalize = (id: number) => {
    normalizeMutation.mutate(id)
  }

  const handleBulkNormalize = () => {
    bulkNormalizeMutation.mutate(selectedRowKeys)
  }

  // Filter line items by search
  const filteredLineItems = lineItems?.filter((item) => {
    if (!filters.search) return true
    const search = filters.search.toLowerCase()
    return (
      item.description?.toLowerCase().includes(search) ||
      item.normalized_description?.toLowerCase().includes(search) ||
      item.sec_code?.toLowerCase().includes(search)
    )
  })

  // Work category colors
  const workCategoryColors: Record<string, string> = {
    earthworks_piling: 'orange',
    concrete_rebar: 'blue',
    finishing: 'green',
    steel_mep: 'purple',
    general: 'default',
  }

  const columns = [
    {
      title: 'Row No.',
      dataIndex: 'row_number',
      key: 'row_number',
      width: 80,
    },
    {
      title: showNormalized ? 'Normalized Description' : 'Description',
      dataIndex: showNormalized ? 'normalized_description' : 'description',
      key: 'description',
      width: 350,
      ellipsis: true,
      render: (_: string, record: LineItem) => {
        const text = showNormalized
          ? (record.normalized_description || record.description)
          : record.description
        return (
          <Tooltip title={text}>
            <span>{text}</span>
          </Tooltip>
        )
      },
    },
    {
      title: 'Category',
      dataIndex: 'work_category',
      key: 'work_category',
      width: 120,
      render: (category: string) => {
        if (!category) return '-'
        const displayName = category.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())
        return (
          <Tag color={workCategoryColors[category] || 'default'}>
            {displayName}
          </Tag>
        )
      },
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      render: (val: number) => val?.toFixed(2) || '-',
    },
    {
      title: 'Unit',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
    },
    {
      title: 'Unit Price',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 120,
      render: (val: number) => val ? `$${val.toFixed(2)}` : '-',
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (val: number) => val ? `$${val.toFixed(2)}` : '-',
    },
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
      width: 140,
      render: (code: string, record: LineItem) => (
        <Space direction="vertical" size="small">
          <Tag color={code ? 'blue' : 'default'}>{code || 'Not Classified'}</Tag>
          {record.confidence_score !== undefined && (
            <Tag color={getConfidenceColor(record.confidence_score)}>
              {record.confidence_score.toFixed(0)}% ({getConfidenceLabel(record.confidence_score)})
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Flags',
      dataIndex: 'flags',
      key: 'flags',
      width: 100,
      render: (flags: Array<{ flag_type: string; note?: string }> | undefined, record: LineItem) => {
        if (!flags || flags.length === 0) return '-'
        return (
          <Space size="small">
            {flags.map((flag, idx) => {
              const config = FLAG_CONFIG[flag.flag_type]
              if (!config) return null
              return (
                <Tooltip key={idx} title={flag.note || config.label}>
                  <Tag color={config.color} icon={config.icon}>
                    {config.label.split(' ')[0]}
                  </Tag>
                </Tooltip>
              )
            })}
          </Space>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'needs_review',
      key: 'needs_review',
      width: 100,
      render: (needsReview: boolean) => (
        <Tag color={needsReview ? 'orange' : 'green'} icon={needsReview ? <CloseCircleOutlined /> : <CheckCircleOutlined />}>
          {needsReview ? 'Needs Review' : 'Verified'}
        </Tag>
      ),
    },
    {
      title: 'Method',
      dataIndex: 'classification_method',
      key: 'classification_method',
      width: 100,
      render: (method: string) => {
        if (!method) return '-'
        const colors: Record<string, string> = {
          ml: 'purple',
          rule: 'cyan',
          manual: 'green',
        }
        return <Tag color={colors[method] || 'default'}>{method.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 220,
      fixed: 'right' as const,
      render: (_: any, record: LineItem) => (
        <Space size="small">
          <Tooltip title="Edit">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          {!record.normalized_description && (
            <Tooltip title="Normalize">
              <Button
                type="link"
                size="small"
                icon={<ThunderboltOutlined />}
                onClick={() => handleNormalize(record.line_item_id)}
                loading={normalizeMutation.isPending}
              />
            </Tooltip>
          )}
          {!record.sec_code && (
            <Tooltip title="Auto-Classify">
              <Button
                type="link"
                size="small"
                icon={<SyncOutlined />}
                onClick={() => handleClassify(record.line_item_id)}
                loading={classifyMutation.isPending}
              />
            </Tooltip>
          )}
          {record.needs_review && (
            <Tooltip title="Mark as Verified">
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => updateMutation.mutate({
                  id: record.line_item_id,
                  data: { needs_review: false },
                })}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="Delete Line Item"
            description="Are you sure you want to delete this item?"
            onConfirm={() => handleDelete(record.line_item_id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete">
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys: any) => setSelectedRowKeys(keys),
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Line Items Review</h1>
        <Space>
          <Button
            icon={<SwapOutlined />}
            onClick={() => setShowNormalized(!showNormalized)}
            type={showNormalized ? 'primary' : 'default'}
          >
            {showNormalized ? 'Normalized' : 'Original'}
          </Button>
          <Input
            placeholder="Search items..."
            prefix={<SearchOutlined />}
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            style={{ width: 250 }}
            allowClear
          />
          <Badge count={Object.values(filters).filter(v => v !== undefined && v !== '').length - (filters.search ? 1 : 0)}>
            <Button icon={<FilterOutlined />} onClick={() => setFilterDrawerOpen(true)}>
              Filters
            </Button>
          </Badge>
        </Space>
      </div>

      {selectedRowKeys.length > 0 && (
        <Card style={{ marginBottom: 16 }}>
          <Space>
            <span><strong>{selectedRowKeys.length}</strong> items selected</span>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={handleBulkNormalize}
              loading={bulkNormalizeMutation.isPending}
            >
              Normalize Selected
            </Button>
            <Button type="primary" onClick={handleBulkVerify}>
              Mark as Verified
            </Button>
            <Select
              placeholder="Assign SEC Code"
              style={{ width: 200 }}
              onChange={handleBulkUpdateSEC}
              allowClear
            >
              {secCodes?.map((sec: SECCode) => (
                <Option key={sec.sec_code} value={sec.sec_code}>
                  {sec.sec_code} - {sec.sec_name_vi}
                </Option>
              ))}
            </Select>
            <Dropdown
              menu={{
                items: Object.entries(FLAG_CONFIG).map(([key, config]) => ({
                  key,
                  label: config.label,
                  icon: config.icon,
                  onClick: () => bulkAddFlagMutation.mutate({ flagType: key }),
                })),
              }}
            >
              <Button icon={<FlagOutlined />}>Add Flag</Button>
            </Dropdown>
            <Button onClick={() => setSelectedRowKeys([])}>Clear Selection</Button>
          </Space>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={filteredLineItems}
          rowKey="line_item_id"
          loading={isLoading}
          rowSelection={rowSelection}
          pagination={{
            pageSize: 50,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} items`,
          }}
          scroll={{ x: 1400 }}
          size="small"
        />
      </Card>

      {/* Edit Modal */}
      <Modal
        title="Edit Line Item"
        open={isModalOpen}
        onOk={handleUpdate}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingItem(null)
        }}
        confirmLoading={updateMutation.isPending}
        width={700}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item name="item_number" label="Item Number">
            <Input />
          </Form.Item>
          <Form.Item name="description" label="Description" rules={[{ required: true }]}>
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item name="quantity" label="Quantity">
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
          </Form.Item>
          <Form.Item name="unit" label="Unit">
            <Input />
          </Form.Item>
          <Form.Item name="unit_price" label="Unit Price">
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} prefix="$" />
          </Form.Item>
          <Form.Item name="total_price" label="Total Price">
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} prefix="$" />
          </Form.Item>
          <Form.Item name="sec_code_id" label="SEC Code">
            <Select allowClear placeholder="Select SEC code">
              {secCodes?.map((sec: SECCode) => (
                <Option key={sec.sec_code} value={sec.sec_code}>
                  {sec.sec_code} - {sec.sec_name_vi}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="needs_review" label="Needs Review" valuePropName="checked">
            <Select>
              <Option value={true}>Needs Review</Option>
              <Option value={false}>Verified</Option>
            </Select>
          </Form.Item>
          <Form.Item name="notes" label="Notes">
            <TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Filter Drawer */}
      <Drawer
        title="Filter Line Items"
        placement="right"
        onClose={() => setFilterDrawerOpen(false)}
        open={filterDrawerOpen}
        width={350}
      >
        <Form layout="vertical">
          <Form.Item label="Review Status">
            <Select
              value={filters.needs_review}
              onChange={(val) => setFilters({ ...filters, needs_review: val })}
              allowClear
              placeholder="All statuses"
            >
              <Option key="needs_review" value={true}>Needs Review</Option>
              <Option key="verified" value={false}>Verified</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Confidence Level">
            <Select
              value={filters.confidence_range}
              onChange={(val) => setFilters({ ...filters, confidence_range: val })}
              allowClear
              placeholder="All confidence levels"
            >
              <Option key="low" value="low">
                <Tag color="red">Low (&lt;80%)</Tag> - Needs attention
              </Option>
              <Option key="medium" value="medium">
                <Tag color="orange">Medium (80-95%)</Tag> - Review recommended
              </Option>
              <Option key="high" value="high">
                <Tag color="green">High (≥95%)</Tag> - High confidence
              </Option>
            </Select>
          </Form.Item>
          <Form.Item label="SEC Code">
            <Select
              value={filters.sec_code}
              onChange={(val) => setFilters({ ...filters, sec_code: val })}
              allowClear
              placeholder="All SEC codes"
              showSearch
            >
              {secCodes?.map((sec: SECCode) => (
                <Option key={sec.sec_code} value={sec.sec_code}>
                  {sec.sec_code} - {sec.sec_name_vi}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Button
            type="primary"
            block
            onClick={() => setFilterDrawerOpen(false)}
          >
            Apply Filters
          </Button>
          <Button
            block
            style={{ marginTop: 8 }}
            onClick={() => {
              setFilters({
                file_id: undefined,
                project_id: undefined,
                sec_code: undefined,
                needs_review: undefined,
                confidence_range: undefined,
                search: '',
              })
            }}
          >
            Clear All Filters
          </Button>
          <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
            <strong>Keyboard Shortcuts:</strong>
            <ul style={{ paddingLeft: 16, marginTop: 8 }}>
              <li><code>Ctrl+A</code> - Select all visible items</li>
              <li><code>Escape</code> - Clear selection</li>
            </ul>
          </div>
        </Form>
      </Drawer>
    </div>
  )
}
