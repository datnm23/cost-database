import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Space,
  Tag,
  Popconfirm,
  message,
  Tooltip,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  FolderOpenOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { projectService, Project, CreateProjectData } from '@/services/projectService'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Option } = Select
const { RangePicker } = DatePicker

export default function Projects() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [form] = Form.useForm()

  // Fetch projects
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectService.getProjects(),
  })

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (values: CreateProjectData) => {
      if (editingProject) {
        return projectService.updateProject(editingProject.id, values)
      }
      return projectService.createProject(values)
    },
    onSuccess: () => {
      message.success(`Project ${editingProject ? 'updated' : 'created'} successfully`)
      setIsModalOpen(false)
      setEditingProject(null)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      message.error('Failed to save project')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: projectService.deleteProject,
    onSuccess: () => {
      message.success('Project deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
    onError: () => {
      message.error('Failed to delete project')
    },
  })

  const handleCreate = () => {
    setEditingProject(null)
    form.resetFields()
    setIsModalOpen(true)
  }

  const handleEdit = (project: Project) => {
    setEditingProject(project)
    form.setFieldsValue({
      ...project,
      dates: project.start_date && project.end_date 
        ? [dayjs(project.start_date), dayjs(project.end_date)]
        : undefined,
    })
    setIsModalOpen(true)
  }

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const formData: CreateProjectData = {
        name: values.name,
        description: values.description,
        client_name: values.client_name,
        location: values.location,
        status: values.status,
      }

      if (values.dates && values.dates.length === 2) {
        formData.start_date = values.dates[0].format('YYYY-MM-DD')
        formData.end_date = values.dates[1].format('YYYY-MM-DD')
      }

      saveMutation.mutate(formData)
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const columns = [
    {
      title: 'Project Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Project) => (
        <Space>
          <FolderOpenOutlined />
          <a onClick={() => navigate(`/projects/${record.id}`)}>{text}</a>
        </Space>
      ),
    },
    {
      title: 'Client',
      dataIndex: 'client_name',
      key: 'client_name',
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          active: 'green',
          planning: 'blue',
          completed: 'default',
          on_hold: 'orange',
          cancelled: 'red',
        }
        return <Tag color={colors[status] || 'default'}>{status.replace('_', ' ').toUpperCase()}</Tag>
      },
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      key: 'file_count',
      render: (count: number) => count || 0,
    },
    {
      title: 'Line Items',
      dataIndex: 'line_item_count',
      key: 'line_item_count',
      render: (count: number) => count || 0,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Project) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/projects/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete Project"
            description="Are you sure you want to delete this project? This will also delete all associated files and line items."
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete">
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <h1>Projects</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Create Project
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={projects}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingProject ? 'Edit Project' : 'Create New Project'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false)
          setEditingProject(null)
          form.resetFields()
        }}
        confirmLoading={saveMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item
            name="name"
            label="Project Name"
            rules={[{ required: true, message: 'Please enter project name' }]}
          >
            <Input placeholder="Enter project name" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <TextArea rows={3} placeholder="Enter project description" />
          </Form.Item>

          <Form.Item
            name="client_name"
            label="Client Name"
            rules={[{ required: true, message: 'Please enter client name' }]}
          >
            <Input placeholder="Enter client name" />
          </Form.Item>

          <Form.Item name="location" label="Location">
            <Input placeholder="Enter project location" />
          </Form.Item>

          <Form.Item name="dates" label="Project Duration">
            <RangePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="status" label="Status" initialValue="planning">
            <Select>
              <Option value="planning">Planning</Option>
              <Option value="active">Active</Option>
              <Option value="on_hold">On Hold</Option>
              <Option value="completed">Completed</Option>
              <Option value="cancelled">Cancelled</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
