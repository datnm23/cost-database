/**
 * Template Management Page
 *
 * Manage column mapping templates for BOQ file uploads.
 * Allows creating, editing, and viewing template usage statistics.
 */
import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Input,
  Select,
  Modal,
  message,
  Row,
  Col,
  Statistic,
  Form,
  Tooltip,
  Popconfirm,
  Badge,
  Descriptions,
  Empty,
  Progress,
} from 'antd'
import {
  FileTextOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
  CopyOutlined,
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SearchOutlined,
  TeamOutlined,
  GlobalOutlined,
  LockOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

import { templateService, Template, TemplateCreate, TemplateVisibility } from '@/services/templateService'

dayjs.extend(relativeTime)

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

export default function TemplateManagement() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [visibilityFilter, setVisibilityFilter] = useState<TemplateVisibility | undefined>()
  const [showInactive, setShowInactive] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null)
  const [form] = Form.useForm()

  // Fetch templates
  const { data: templatesData, isLoading, refetch } = useQuery({
    queryKey: ['templates', visibilityFilter, showInactive],
    queryFn: () =>
      templateService.list({
        visibility: visibilityFilter,
        include_inactive: showInactive,
        limit: 100,
      }),
  })

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['templateStatistics'],
    queryFn: templateService.getStatistics,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: templateService.create,
    onSuccess: () => {
      message.success('Template created successfully')
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['templateStatistics'] })
      setIsModalOpen(false)
      form.resetFields()
    },
    onError: (error: Error) => {
      message.error(`Failed to create template: ${error.message}`)
    },
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<TemplateCreate> }) =>
      templateService.update(id, data),
    onSuccess: () => {
      message.success('Template updated successfully')
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      setIsModalOpen(false)
      setSelectedTemplate(null)
      form.resetFields()
    },
    onError: (error: Error) => {
      message.error(`Failed to update template: ${error.message}`)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => templateService.delete(id),
    onSuccess: () => {
      message.success('Template deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['templateStatistics'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to delete template: ${error.message}`)
    },
  })

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      templateService.duplicate(id, name),
    onSuccess: () => {
      message.success('Template duplicated successfully')
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      queryClient.invalidateQueries({ queryKey: ['templateStatistics'] })
    },
    onError: (error: Error) => {
      message.error(`Failed to duplicate template: ${error.message}`)
    },
  })

  // Toggle active mutation
  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, active }: { id: number; active: boolean }) =>
      active ? templateService.activate(id) : templateService.deactivate(id),
    onSuccess: (_, { active }) => {
      message.success(`Template ${active ? 'activated' : 'deactivated'}`)
      queryClient.invalidateQueries({ queryKey: ['templates'] })
    },
  })

  const handleOpenModal = (template?: Template) => {
    if (template) {
      setSelectedTemplate(template)
      form.setFieldsValue({
        name: template.name,
        description: template.description,
        column_mapping: JSON.stringify(template.column_mapping, null, 2),
        header_row_hint: template.header_row_hint,
        sheet_name_pattern: template.sheet_name_pattern,
        visibility: template.visibility,
      })
    } else {
      setSelectedTemplate(null)
      form.resetFields()
    }
    setIsModalOpen(true)
  }

  const handleViewTemplate = (template: Template) => {
    setSelectedTemplate(template)
    setIsViewModalOpen(true)
  }

  const handleSubmit = async (values: {
    name: string
    description?: string
    column_mapping: string
    header_row_hint?: number
    sheet_name_pattern?: string
    visibility: TemplateVisibility
  }) => {
    try {
      const columnMapping = JSON.parse(values.column_mapping)

      const data: TemplateCreate = {
        name: values.name,
        description: values.description,
        column_mapping: columnMapping,
        header_row_hint: values.header_row_hint || 0,
        sheet_name_pattern: values.sheet_name_pattern,
        visibility: values.visibility,
      }

      if (selectedTemplate) {
        updateMutation.mutate({ id: selectedTemplate.template_id, data })
      } else {
        createMutation.mutate(data)
      }
    } catch {
      message.error('Invalid JSON in column mapping')
    }
  }

  const handleDuplicate = (template: Template) => {
    const newName = `${template.name} (Copy)`
    duplicateMutation.mutate({ id: template.template_id, name: newName })
  }

  const getVisibilityIcon = (visibility: TemplateVisibility) => {
    switch (visibility) {
      case 'private':
        return <LockOutlined />
      case 'team':
        return <TeamOutlined />
      case 'public':
        return <GlobalOutlined />
    }
  }

  const getVisibilityColor = (visibility: TemplateVisibility) => {
    switch (visibility) {
      case 'private':
        return 'default'
      case 'team':
        return 'blue'
      case 'public':
        return 'green'
    }
  }

  // Filter templates by search
  const filteredTemplates = templatesData?.templates.filter((t) =>
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    t.description?.toLowerCase().includes(search.toLowerCase())
  ) || []

  const columns: ColumnsType<Template> = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (name: string, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <Text strong>{name}</Text>
            {record.is_system && <Tag color="purple">System</Tag>}
            {!record.is_active && <Tag color="red">Inactive</Tag>}
          </Space>
          {record.description && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.description.length > 50
                ? `${record.description.substring(0, 50)}...`
                : record.description}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Columns',
      key: 'columns',
      width: 180,
      render: (_, record) => {
        const mappings = Object.entries(record.column_mapping)
        return (
          <Tooltip
            title={
              <div>
                {mappings.map(([from, to]) => (
                  <div key={from}>
                    {from} → {to}
                  </div>
                ))}
              </div>
            }
          >
            <Text>{mappings.length} column{mappings.length !== 1 ? 's' : ''} mapped</Text>
          </Tooltip>
        )
      },
    },
    {
      title: 'Visibility',
      dataIndex: 'visibility',
      key: 'visibility',
      width: 100,
      render: (visibility: TemplateVisibility) => (
        <Tag icon={getVisibilityIcon(visibility)} color={getVisibilityColor(visibility)}>
          {visibility}
        </Tag>
      ),
    },
    {
      title: 'Usage',
      key: 'usage',
      width: 120,
      sorter: (a, b) => a.use_count - b.use_count,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text>{record.use_count} uses</Text>
          <Progress
            percent={record.match_success_rate}
            size="small"
            status={record.match_success_rate >= 80 ? 'success' : record.match_success_rate >= 50 ? 'normal' : 'exception'}
            format={(p) => `${p?.toFixed(0)}%`}
          />
        </Space>
      ),
    },
    {
      title: 'Last Used',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 120,
      render: (date: string | null) =>
        date ? (
          <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm')}>
            <Text type="secondary">{dayjs(date).fromNow()}</Text>
          </Tooltip>
        ) : (
          <Text type="secondary">Never</Text>
        ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm')}>
          <Text type="secondary">{dayjs(date).fromNow()}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 160,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewTemplate(record)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
              disabled={record.is_system}
            />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button
              type="text"
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleDuplicate(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? 'Deactivate' : 'Activate'}>
            <Button
              type="text"
              size="small"
              icon={record.is_active ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              onClick={() =>
                toggleActiveMutation.mutate({
                  id: record.template_id,
                  active: !record.is_active,
                })
              }
              disabled={record.is_system}
            />
          </Tooltip>
          <Popconfirm
            title="Delete template?"
            description="This action cannot be undone."
            onConfirm={() => deleteMutation.mutate(record.template_id)}
            okText="Delete"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="Delete">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                disabled={record.is_system}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>
        <FileTextOutlined style={{ marginRight: 8 }} />
        Column Mapping Templates
      </Title>

      <Paragraph type="secondary">
        Manage reusable column mapping templates for BOQ file uploads. Templates enable automatic
        column detection based on file structure fingerprints.
      </Paragraph>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Templates"
              value={stats?.total_templates || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Templates"
              value={stats?.active_templates || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Uses"
              value={stats?.total_uses || 0}
              prefix={<ReloadOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={stats?.average_success_rate || 0}
              suffix="%"
              precision={1}
              valueStyle={{
                color:
                  (stats?.average_success_rate || 0) >= 80
                    ? '#3f8600'
                    : (stats?.average_success_rate || 0) >= 50
                    ? '#faad14'
                    : '#cf1322',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main Table Card */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            Templates
            <Badge count={filteredTemplates.length} style={{ marginLeft: 8 }} />
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              New Template
            </Button>
          </Space>
        }
      >
        {/* Filters */}
        <Space wrap style={{ marginBottom: 16 }}>
          <Input
            placeholder="Search templates..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="Visibility"
            allowClear
            style={{ width: 150 }}
            value={visibilityFilter}
            onChange={setVisibilityFilter}
            options={[
              { value: 'private', label: 'Private' },
              { value: 'team', label: 'Team' },
              { value: 'public', label: 'Public' },
            ]}
          />
          <Button
            type={showInactive ? 'primary' : 'default'}
            onClick={() => setShowInactive(!showInactive)}
          >
            {showInactive ? 'Showing Inactive' : 'Show Inactive'}
          </Button>
        </Space>

        {/* Table */}
        <Table
          columns={columns}
          dataSource={filteredTemplates}
          rowKey="template_id"
          loading={isLoading}
          pagination={{
            defaultPageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `${total} templates`,
          }}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty description="No templates found">
                <Button type="primary" onClick={() => handleOpenModal()}>
                  Create First Template
                </Button>
              </Empty>
            ),
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={selectedTemplate ? 'Edit Template' : 'Create Template'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          setSelectedTemplate(null)
          form.resetFields()
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ visibility: 'private', header_row_hint: 0 }}
        >
          <Form.Item
            name="name"
            label="Template Name"
            rules={[{ required: true, message: 'Name is required' }]}
          >
            <Input placeholder="e.g., Nhà thầu ABC - Format 2024" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={2} placeholder="Optional description for this template" />
          </Form.Item>

          <Form.Item
            name="column_mapping"
            label="Column Mapping (JSON)"
            rules={[
              { required: true, message: 'Column mapping is required' },
              {
                validator: (_, value) => {
                  try {
                    JSON.parse(value)
                    return Promise.resolve()
                  } catch {
                    return Promise.reject('Invalid JSON format')
                  }
                },
              },
            ]}
            tooltip="JSON object mapping Excel column names to standard fields"
          >
            <TextArea
              rows={6}
              placeholder={`{
  "Mô tả công việc": "description",
  "Đơn vị": "unit",
  "Khối lượng": "quantity",
  "Đơn giá": "unit_price",
  "Thành tiền": "amount"
}`}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="header_row_hint"
                label="Header Row Hint"
                tooltip="Expected row number of the header (0-based)"
              >
                <Input type="number" min={0} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="sheet_name_pattern"
                label="Sheet Name Pattern"
                tooltip="Regex pattern to match sheet names"
              >
                <Input placeholder="e.g., BOQ|Bill" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="visibility"
            label="Visibility"
            rules={[{ required: true }]}
          >
            <Select
              options={[
                { value: 'private', label: 'Private - Only you can see' },
                { value: 'team', label: 'Team - Your team can see' },
                { value: 'public', label: 'Public - Everyone can see' },
              ]}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsModalOpen(false)}>Cancel</Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {selectedTemplate ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* View Details Modal */}
      <Modal
        title="Template Details"
        open={isViewModalOpen}
        onCancel={() => {
          setIsViewModalOpen(false)
          setSelectedTemplate(null)
        }}
        footer={
          <Button onClick={() => setIsViewModalOpen(false)}>Close</Button>
        }
        width={700}
      >
        {selectedTemplate && (
          <div>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Name" span={2}>
                <Text strong>{selectedTemplate.name}</Text>
                {selectedTemplate.is_system && (
                  <Tag color="purple" style={{ marginLeft: 8 }}>
                    System
                  </Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>
                {selectedTemplate.description || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Visibility">
                <Tag
                  icon={getVisibilityIcon(selectedTemplate.visibility)}
                  color={getVisibilityColor(selectedTemplate.visibility)}
                >
                  {selectedTemplate.visibility}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={selectedTemplate.is_active ? 'green' : 'red'}>
                  {selectedTemplate.is_active ? 'Active' : 'Inactive'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Usage Count">
                {selectedTemplate.use_count}
              </Descriptions.Item>
              <Descriptions.Item label="Success Rate">
                <Progress
                  percent={selectedTemplate.match_success_rate}
                  size="small"
                  style={{ width: 120 }}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Header Row Hint">
                {selectedTemplate.header_row_hint}
              </Descriptions.Item>
              <Descriptions.Item label="Sheet Pattern">
                {selectedTemplate.sheet_name_pattern || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {dayjs(selectedTemplate.created_at).format('YYYY-MM-DD HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="Last Used">
                {selectedTemplate.last_used_at
                  ? dayjs(selectedTemplate.last_used_at).format('YYYY-MM-DD HH:mm')
                  : 'Never'}
              </Descriptions.Item>
              <Descriptions.Item label="Fingerprint" span={2}>
                <Text code copyable style={{ fontSize: 11 }}>
                  {selectedTemplate.fingerprint}
                </Text>
              </Descriptions.Item>
            </Descriptions>

            <Title level={5} style={{ marginTop: 16 }}>
              Column Mapping
            </Title>
            <Table
              dataSource={Object.entries(selectedTemplate.column_mapping).map(
                ([from, to], i) => ({ key: i, from, to })
              )}
              columns={[
                {
                  title: 'Excel Column',
                  dataIndex: 'from',
                  key: 'from',
                  render: (text) => <Text code>{text}</Text>,
                },
                { title: '', key: 'arrow', width: 50, render: () => '→' },
                {
                  title: 'Standard Field',
                  dataIndex: 'to',
                  key: 'to',
                  render: (text) => <Tag color="blue">{text}</Tag>,
                },
              ]}
              pagination={false}
              size="small"
            />

            {selectedTemplate.fingerprint_components && (
              <>
                <Title level={5} style={{ marginTop: 16 }}>
                  Fingerprint Components
                </Title>
                <Descriptions bordered size="small" column={1}>
                  <Descriptions.Item label="Column Count">
                    {selectedTemplate.fingerprint_components.column_count}
                  </Descriptions.Item>
                  <Descriptions.Item label="Keywords">
                    {selectedTemplate.fingerprint_components.column_keywords.map((kw) => (
                      <Tag key={kw}>{kw}</Tag>
                    ))}
                  </Descriptions.Item>
                  <Descriptions.Item label="Order Hash">
                    <Text code>{selectedTemplate.fingerprint_components.column_order_hash}</Text>
                  </Descriptions.Item>
                </Descriptions>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
