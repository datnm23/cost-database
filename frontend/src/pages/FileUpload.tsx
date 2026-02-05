import { useState } from 'react'
import {
  Card,
  Upload,
  Button,
  Select,
  Steps,
  Form,
  message,
  Progress,
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
import { HeaderDiscoveryResult } from '@/services/headerDiscoveryService'
import { ColumnMappingWizard, ColumnMappingResult } from '@/components/ColumnMappingWizard'
import type { UploadFile } from 'antd/es/upload/interface'

const { Dragger } = Upload
const { Option } = Select

export default function FileUpload() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // State management
  const [currentStep, setCurrentStep] = useState(0)
  const [selectedProject, setSelectedProject] = useState<number | null>(null)
  const [uploadedFile, setUploadedFile] = useState<UploadFile | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [fileId, setFileId] = useState<number | null>(null)
  const [fileStructure, setFileStructure] = useState<FileStructure | null>(null)

  // Wizard state
  const [wizardOpen, setWizardOpen] = useState(false)
  const [headerDiscovery, setHeaderDiscovery] = useState<HeaderDiscoveryResult | null>(null)

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

        // Check if header_discovery is available from backend
        if (data.header_discovery) {
          setHeaderDiscovery(data.header_discovery)
          setWizardOpen(true)
        } else {
          // Create a fallback header discovery result from structure
          const fallbackDiscovery: HeaderDiscoveryResult = {
            sheet_name: 'Sheet1',
            sheet_index: 0,
            header_row: 1,
            data_start_row: 2,
            column_names: data.structure.columns,
            confidence_score: 80,
            is_merged_header: false,
            column_type_hints: {},
            sheets: [{ name: 'Sheet1', index: 0, priority_score: 100, skip_reason: null }],
          }
          setHeaderDiscovery(fallbackDiscovery)
          setWizardOpen(true)
        }

        setCurrentStep(1) // Move to wizard step
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
    mutationFn: async (mappingResult: ColumnMappingResult) => {
      if (!fileId) throw new Error('No file ID')
      return fileService.processFile(fileId, {
        column_mapping: mappingResult.columnMapping,
        has_headers: true,
        sheet_name: mappingResult.sheetName,
        header_row: mappingResult.headerRow,
        data_start_row: mappingResult.dataStartRow,
      })
    },
    onSuccess: () => {
      message.success('File processed successfully! Redirecting to line items...')
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setWizardOpen(false)
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

  const handleMappingComplete = (mappingResult: ColumnMappingResult) => {
    processMutation.mutate(mappingResult)
  }

  const handleWizardClose = () => {
    setWizardOpen(false)
    // Reset to allow re-upload
    setCurrentStep(0)
    setUploadedFile(null)
    setUploadProgress(0)
  }

  const handleStartOver = () => {
    setCurrentStep(0)
    setUploadedFile(null)
    setUploadProgress(0)
    setFileId(null)
    setFileStructure(null)
    setHeaderDiscovery(null)
    setWizardOpen(false)
  }

  const steps = [
    {
      title: 'Select Project & Upload',
      icon: <UploadOutlined />,
    },
    {
      title: 'Map Columns',
      icon: currentStep === 1 ? <SyncOutlined spin={processMutation.isPending} /> : <CheckCircleOutlined />,
    },
    {
      title: 'Complete',
      icon: <CheckCircleOutlined />,
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Upload BOQ File</h1>

      <Card>
        <Steps current={currentStep} items={steps} style={{ marginBottom: 32 }} />

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

        {/* Step 1: Wizard is open */}
        {currentStep === 1 && !wizardOpen && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <h3 style={{ marginTop: 16 }}>File uploaded successfully</h3>
            <p>Click below to open the Column Mapping Wizard</p>
            <Button type="primary" onClick={() => setWizardOpen(true)} style={{ marginTop: 16 }}>
              Open Mapping Wizard
            </Button>
            <Button onClick={handleStartOver} style={{ marginLeft: 8, marginTop: 16 }}>
              Start Over
            </Button>
          </div>
        )}

        {/* Step 2: Processing complete - this is shown briefly before redirect */}
        {currentStep === 2 && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
            <h3 style={{ marginTop: 16 }}>Processing complete!</h3>
            <p>Redirecting to line items...</p>
          </div>
        )}
      </Card>

      {/* Column Mapping Wizard Modal */}
      {headerDiscovery && fileStructure && (
        <ColumnMappingWizard
          open={wizardOpen}
          onClose={handleWizardClose}
          onComplete={handleMappingComplete}
          fileId={fileId || 0}
          fileName={uploadedFile?.name || ''}
          headerDiscovery={headerDiscovery}
          sampleData={fileStructure.sample_data}
          allRows={fileStructure.sample_data}
        />
      )}
    </div>
  )
}
