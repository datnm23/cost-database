import { useState, useEffect, useMemo } from 'react'
import { Modal, Steps, Button, Space, message } from 'antd'
import HeaderConfirmStep from './HeaderConfirmStep'
import ColumnMappingStep from './ColumnMappingStep'
import PreviewStep from './PreviewStep'
import { SYSTEM_FIELDS } from './fieldConfig'
import { HeaderDiscoveryResult, ColumnMappingResult } from './types'

interface ColumnMappingWizardProps {
  open: boolean
  onClose: () => void
  onComplete: (mapping: ColumnMappingResult) => void
  fileId: number
  fileName: string
  headerDiscovery: HeaderDiscoveryResult
  sampleData: any[][]
  allRows?: any[][]
}

export default function ColumnMappingWizard({
  open,
  onClose,
  onComplete,
  fileId: _fileId,
  fileName,
  headerDiscovery,
  sampleData,
  allRows = [],
}: ColumnMappingWizardProps) {
  // fileId is passed for future use when fetching additional data
  void _fileId
  const [currentStep, setCurrentStep] = useState(0)
  const [headerRow, setHeaderRow] = useState(headerDiscovery.header_row)
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [saveAsTemplate, setSaveAsTemplate] = useState(false)
  const [templateName, setTemplateName] = useState('')

  // Auto-suggest initial mapping based on column_type_hints and keyword matching
  useEffect(() => {
    const initialMapping: Record<string, string> = {}
    const columns = headerDiscovery.column_names

    // First, apply backend hints
    for (const [fieldKey, colIndex] of Object.entries(headerDiscovery.column_type_hints)) {
      if (colIndex >= 0 && colIndex < columns.length) {
        initialMapping[fieldKey] = columns[colIndex]
      }
    }

    // Then, try keyword matching for unmapped fields
    for (const field of SYSTEM_FIELDS) {
      if (!initialMapping[field.key]) {
        for (const col of columns) {
          const colLower = col.toLowerCase()
          for (const keyword of field.keywords) {
            if (colLower.includes(keyword.toLowerCase())) {
              // Check if this column is already used
              if (!Object.values(initialMapping).includes(col)) {
                initialMapping[field.key] = col
                break
              }
            }
          }
          if (initialMapping[field.key]) break
        }
      }
    }

    setColumnMapping(initialMapping)
  }, [headerDiscovery])

  // Reset when dialog opens
  useEffect(() => {
    if (open) {
      setCurrentStep(0)
      setHeaderRow(headerDiscovery.header_row)
    }
  }, [open, headerDiscovery.header_row])

  // Validation for proceeding
  const canProceedToStep2 = headerRow > 0
  const canProceedToStep3 = useMemo(() => {
    const requiredFields = SYSTEM_FIELDS.filter((f) => f.required)
    return requiredFields.every((f) => columnMapping[f.key])
  }, [columnMapping])

  const canComplete = canProceedToStep3

  const handleNext = () => {
    if (currentStep === 0 && !canProceedToStep2) {
      message.error('Please confirm the header row')
      return
    }
    if (currentStep === 1 && !canProceedToStep3) {
      message.error('Please map all required fields')
      return
    }
    setCurrentStep((prev) => Math.min(prev + 1, 2))
  }

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 0))
  }

  const handleComplete = () => {
    if (!canComplete) {
      message.error('Please map all required fields')
      return
    }

    const result: ColumnMappingResult = {
      columnMapping,
      headerRow,
      dataStartRow: headerDiscovery.data_start_row,
      sheetName: headerDiscovery.sheet_name,
      saveAsTemplate,
      templateName: saveAsTemplate ? templateName : undefined,
    }

    onComplete(result)
  }

  const steps = [
    {
      title: 'Confirm Header',
      description: 'Verify detected header row',
    },
    {
      title: 'Map Columns',
      description: 'Match system fields to Excel columns',
    },
    {
      title: 'Preview & Confirm',
      description: 'Review and process',
    },
  ]

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <HeaderConfirmStep
            headerDiscovery={headerDiscovery}
            sampleData={sampleData}
            allRows={allRows.length > 0 ? allRows : sampleData}
            selectedHeaderRow={headerRow}
            onHeaderRowChange={setHeaderRow}
          />
        )
      case 1:
        return (
          <ColumnMappingStep
            headerDiscovery={headerDiscovery}
            columnMapping={columnMapping}
            sampleData={sampleData}
            onMappingChange={setColumnMapping}
          />
        )
      case 2:
        return (
          <PreviewStep
            headerDiscovery={headerDiscovery}
            columnMapping={columnMapping}
            sampleData={sampleData}
            headerRow={headerRow}
            saveAsTemplate={saveAsTemplate}
            templateName={templateName}
            onSaveAsTemplateChange={setSaveAsTemplate}
            onTemplateNameChange={setTemplateName}
          />
        )
      default:
        return null
    }
  }

  return (
    <Modal
      title={`Column Mapping Wizard - ${fileName}`}
      open={open}
      onCancel={onClose}
      width={900}
      footer={null}
      destroyOnClose
    >
      <Steps current={currentStep} items={steps} style={{ marginBottom: 32 }} />

      <div style={{ minHeight: 400, maxHeight: 500, overflow: 'auto', padding: '0 4px' }}>
        {renderStepContent()}
      </div>

      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginTop: 24,
          paddingTop: 16,
          borderTop: '1px solid #f0f0f0',
        }}
      >
        <Button onClick={onClose}>Cancel</Button>
        <Space>
          {currentStep > 0 && <Button onClick={handleBack}>Back</Button>}
          {currentStep < 2 && (
            <Button type="primary" onClick={handleNext}>
              Next: {steps[currentStep + 1]?.title}
            </Button>
          )}
          {currentStep === 2 && (
            <Button type="primary" onClick={handleComplete} disabled={!canComplete}>
              Process File
            </Button>
          )}
        </Space>
      </div>
    </Modal>
  )
}
