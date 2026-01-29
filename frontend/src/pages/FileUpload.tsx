import { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  Select,
  Steps,
  Table,
  Form,
  Input,
  message,
  Space,
  Progress,
  Alert,
  Tag,
  Checkbox,
} from 'antd'
import {
  InboxOutlined,
  UploadOutlined,
  CheckCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { projectService, Project } from '@/services/projectService'
import { fileService, FileStructure } from '@/services/fileService'
import type { UploadFile } from 'antd/es/upload/interface'

const { Dragger } = Upload
const { Option } = Select
const { Step } = Steps

export default function FileUpload() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()

  // State management
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  const [uploadedFile, setUploadedFile] = useState<UploadFile | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [fileId, setFileId] = useState<number | null>(null)
  const [fileStructure, setFileStructure] = useState<FileStructure | null>(null)
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [hasHeaders, setHasHeaders] = useState(true)

  // Fetch projects
  const { data: projects = [], isLoading: loadingProjects } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectService.getProjects(),
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!selectedProject) throw new Error('No project selected')
      return fileService.uploadFile(selectedProject, file, setUploadProgress)
    },
    onSuccess: (data) => {
      console.log('Upload response:', data)
      message.success('File uploaded successfully')
      setFileId(data.file_id)

      // Use structure from upload response
      if (data.structure) {
        console.log('Structure found:', data.structure)
        setFileStructure(data.structure)

        // Auto-detect column mapping based on common column names
        const autoMapping: Record<string, string> = {}
        data.structure.columns.forEach((col: string) => {
          const lower = col.toLowerCase()
          if (lower.includes('item') && lower.includes('no')) autoMapping['item_number'] = col
          if (lower.includes('description') || lower.includes('desc')) autoMapping['description'] = col
          if (lower.includes('quantity') || lower.includes('qty')) autoMapping['quantity'] = col
          if (lower.includes('unit') && !lower.includes('price')) autoMapping['unit'] = col
          if (lower.includes('unit') && lower.includes('price')) autoMapping['unit_price'] = col
          if (lower.includes('total') || lower.includes('amount')) autoMapping['total_price'] = col
        })
        setColumnMapping(autoMapping)
        setCurrentStep(2) // Skip analyze step, go directly to mapping
      } else {
        console.error('No structure in response')
      }
    },
    onError: () => {
      message.error('Failed to upload file')
      setUploadedFile(null)
      setUploadProgress(0)
    },
  })

  // Process mutation
  const processMutation = useMutation({
    mutationFn: async () => {
      if (!fileId) throw new Error('No file ID')
      return fileService.processFile(fileId, {
        column_mapping: columnMapping,
        has_headers: hasHeaders,
      })
    },
    onSuccess: () => {
      message.success('File processed successfully! Redirecting to line items...')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setTimeout(() => {
        navigate(`/line-items?file_id=${fileId}`)
      }, 1500)
    },
    onError: () => {
      message.error('Failed to process file')
    },
  })

  const handleFileSelect = (file: File) => {
    if (!selectedProject) {
      message.error('Please select a project first')
      return false
    }

    const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                    file.type === 'application/vnd.ms-excel' ||
                    file.name.endsWith('.xlsx') ||
                    file.name.endsWith('.xls')

    if (!isExcel) {
      message.error('Please upload an Excel file (.xlsx or .xls)')
      return false
    }

    const isLt10M = file.size / 1024 / 1024 < 10
    if (!isLt10M) {
      message.error('File must be smaller than 10MB')
      return false
    }

    setUploadedFile({
      uid: '-1',
      name: file.name,
      status: 'uploading',
      size: file.size,
    })

    uploadMutation.mutate(file)
    return false // Prevent default upload behavior
  }

  const handleProcess = () => {
    // Validate that required columns are mapped
    if (!columnMapping.description) {
      message.error('Description column is required')
      return
    }
    processMutation.mutate()
  }

  const requiredColumns = [
    { key: 'item_number', label: 'Item Number', required: false },
    { key: 'description', label: 'Description', required: true },
    { key: 'quantity', label: 'Quantity', required: false },
    { key: 'unit', label: 'Unit', required: false },
    { key: 'unit_price', label: 'Unit Price', required: false },
    { key: 'total_price', label: 'Total Price', required: false },
  ]

  const sampleDataColumns = fileStructure?.columns.map(col => ({
    title: col,
    dataIndex: col,
    key: col,
    width: 150,
  })) || []

  const sampleDataSource = fileStructure?.sample_data.map((row, idx) => {
    const obj: any = { key: idx }
    row.forEach((val, colIdx) => {
      obj[fileStructure.columns[colIdx]] = val
    })
    return obj
  }) || []

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Upload BOQ File</h1>

      <Card>
        <Steps current={currentStep} style={{ marginBottom: 32 }}>
          <Step title="Select Project & Upload" icon={<UploadOutlined />} />
          <Step title="Analyze Structure" icon={<SyncOutlined spin={uploadMutation.isPending && currentStep === 1} />} />
          <Step title="Map Columns & Process" icon={<CheckCircleOutlined />} />
        </Steps>

        {/* Step 0: Project Selection and Upload */}
        {currentStep === 0 && (
          <div>
            <Form layout="vertical">
              <Form.Item
                label="Select Project"
                required
                help="Choose the project this BOQ file belongs to"
              >
                <Select
                  placeholder="Select a project"
                  loading={loadingProjects}
                  onChange={(value) => setSelectedProject(value)}
                  size="large"
                  style={{ width: '100%', maxWidth: 400 }}
                >
                  {(projects || []).map((project) => (
                    <Option key={project.id} value={project.id}>
                      {project.name} - {project.client_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Form>

            <Dragger
              name="file"
              accept=".xlsx,.xls"
              beforeUpload={handleFileSelect}
              fileList={uploadedFile ? [uploadedFile] : []}
              disabled={!selectedProject || uploadMutation.isPending}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">Click or drag Excel file to this area to upload</p>
              <p className="ant-upload-hint">
                Support for .xlsx and .xls files (max 10MB). Make sure your file contains BOQ data with
                columns for item number, description, quantity, unit, and pricing.
              </p>
            </Dragger>

            {uploadMutation.isPending && (
              <div style={{ marginTop: 16 }}>
                <Progress percent={uploadProgress} status="active" />
                <p style={{ textAlign: 'center', marginTop: 8 }}>
                  Uploading {uploadedFile?.name}...
                </p>
              </div>
            )}
          </div>
        )}

        {/* Step 1: Analyzing (automatic) */}
        {currentStep === 1 && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <SyncOutlined spin style={{ fontSize: 48, color: '#1890ff' }} />
            <h3 style={{ marginTop: 16 }}>Analyzing file structure...</h3>
            <p>This will only take a moment.</p>
          </div>
        )}

        {/* Step 2: Column Mapping */}
        {currentStep === 2 && fileStructure && (
          <div>
            <Alert
              message="Map Your Columns"
              description={`We detected ${fileStructure.columns.length} columns and ${fileStructure.total_rows} rows in your file. Please map the columns to the appropriate BOQ fields.`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Checkbox
              checked={hasHeaders}
              onChange={(e) => setHasHeaders(e.target.checked)}
              style={{ marginBottom: 16 }}
            >
              First row contains headers
            </Checkbox>

            <h3>Column Mapping</h3>
            <Form layout="vertical" style={{ marginBottom: 24 }}>
              {requiredColumns.map((field) => (
                <Form.Item
                  key={field.key}
                  label={
                    <span>
                      {field.label}
                      {field.required && <Tag color="red" style={{ marginLeft: 8 }}>Required</Tag>}
                    </span>
                  }
                >
                  <Select
                    placeholder={`Select column for ${field.label}`}
                    value={columnMapping[field.key] && fileStructure.columns.includes(columnMapping[field.key]) ? columnMapping[field.key] : undefined}
                    onChange={(value) => setColumnMapping({ ...columnMapping, [field.key]: value })}
                    allowClear
                  >
                    {fileStructure.columns.map((col) => (
                      <Option key={col} value={col}>
                        {col}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              ))}
            </Form>

            <h3>Sample Data Preview</h3>
            <Table
              columns={sampleDataColumns}
              dataSource={sampleDataSource}
              scroll={{ x: 'max-content' }}
              pagination={false}
              size="small"
              bordered
            />

            <div style={{ marginTop: 24, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setCurrentStep(0)}>Start Over</Button>
                <Button
                  type="primary"
                  onClick={handleProcess}
                  loading={processMutation.isPending}
                  disabled={!columnMapping.description}
                >
                  Process File & Import Data
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
