import { useState, useEffect } from 'react'
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
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  lineItemService,
  secCodeService,
  LineItem,
  SECCode,
} from '@/services/lineItemService'

const { Option } = Select
const { TextArea } = Input

export default function LineItems() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const [form] = Form.useForm()

  // State
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [editingItem, setEditingItem] = useState<LineItem | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [filterDrawerOpen, setFilterDrawerOpen] = useState(false)
  const [filters, setFilters] = useState({
    file_id: searchParams.get('file_id') ? parseInt(searchParams.get('file_id')!) : undefined,
    project_id: searchParams.get('project_id') ? parseInt(searchParams.get('project_id')!) : undefined,
    sec_code: undefined as string | undefined,
    is_verified: undefined as boolean | undefined,
    search: '',
  })

  // Fetch line items
  const { data: lineItems, isLoading } = useQuery({
    queryKey: ['lineItems', filters],
    queryFn: () => lineItemService.getLineItems({
      file_id: filters.file_id,
      project_id: filters.project_id,
      sec_code: filters.sec_code,
      is_verified: filters.is_verified,
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

  const handleEdit = (item: LineItem) => {
    setEditingItem(item)
    form.setFieldsValue(item)
    setIsModalOpen(true)
  }

  const handleUpdate = async () => {
    try {
      const values = await form.validateFields()
      if (editingItem) {
        updateMutation.mutate({ id: editingItem.id, data: values })
      }
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleBulkVerify = () => {
    bulkUpdateMutation.mutate({
      line_item_ids: selectedRowKeys,
      is_verified: true,
    })
  }

  const handleBulkUpdateSEC = (secCodeId: number) => {
    bulkUpdateMutation.mutate({
      line_item_ids: selectedRowKeys,
      sec_code_id: secCodeId,
    })
  }

  const handleClassify = (id: number) => {
    classifyMutation.mutate(id)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  // Filter line items by search
  const filteredLineItems = lineItems?.filter((item) => {
    if (!filters.search) return true
    const search = filters.search.toLowerCase()
    return (
      item.description?.toLowerCase().includes(search) ||
      item.item_number?.toLowerCase().includes(search) ||
      item.sec_code?.toLowerCase().includes(search)
    )
  })

  const columns = [
    {
      title: 'Item No.',
      dataIndex: 'item_number',
      key: 'item_number',
      width: 100,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
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
      title: 'Total Price',
      dataIndex: 'total_price',
      key: 'total_price',
      width: 120,
      render: (val: number) => val ? `$${val.toFixed(2)}` : '-',
    },
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
      width: 120,
      render: (code: string, record: LineItem) => (
        <Space direction="vertical" size="small">
          <Tag color={code ? 'blue' : 'default'}>{code || 'Not Classified'}</Tag>
          {record.classification_confidence && (
            <span style={{ fontSize: 11, color: '#999' }}>
              {(record.classification_confidence * 100).toFixed(0)}% confidence
            </span>
          )}
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_verified',
      key: 'is_verified',
      width: 100,
      render: (verified: boolean) => (
        <Tag color={verified ? 'green' : 'orange'} icon={verified ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {verified ? 'Verified' : 'Pending'}
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
      width: 200,
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
          {!record.sec_code && (
            <Tooltip title="Auto-Classify">
              <Button
                type="link"
                size="small"
                icon={<SyncOutlined />}
                onClick={() => handleClassify(record.id)}
                loading={classifyMutation.isPending}
              />
            </Tooltip>
          )}
          {!record.is_verified && (
            <Tooltip title="Mark as Verified">
              <Button
                type="link"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => updateMutation.mutate({
                  id: record.id,
                  data: { is_verified: true },
                })}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="Delete Line Item"
            description="Are you sure you want to delete this item?"
            onConfirm={() => handleDelete(record.id)}
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
                <Option key={sec.id} value={sec.id}>
                  {sec.code} - {sec.description}
                </Option>
              ))}
            </Select>
            <Button onClick={() => setSelectedRowKeys([])}>Clear Selection</Button>
          </Space>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={filteredLineItems}
          rowKey="id"
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
                <Option key={sec.id} value={sec.id}>
                  {sec.code} - {sec.description}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="is_verified" label="Verified" valuePropName="checked">
            <Select>
              <Option value={true}>Verified</Option>
              <Option value={false}>Pending</Option>
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
          <Form.Item label="Verification Status">
            <Select
              value={filters.is_verified}
              onChange={(val) => setFilters({ ...filters, is_verified: val })}
              allowClear
              placeholder="All statuses"
            >
              <Option value={true}>Verified</Option>
              <Option value={false}>Pending</Option>
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
                <Option key={sec.code} value={sec.code}>
                  {sec.code} - {sec.description}
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
                is_verified: undefined,
                search: '',
              })
            }}
          >
            Clear All Filters
          </Button>
        </Form>
      </Drawer>
    </div>
  )
}
