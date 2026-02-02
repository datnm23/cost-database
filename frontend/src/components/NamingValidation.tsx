import { useState } from 'react'
import {
  Card,
  Input,
  Button,
  Space,
  Tag,
  Alert,
  List,
  Typography,
  Spin,
  Divider,
  Progress,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ThunderboltOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery } from '@tanstack/react-query'
import { namingService, ValidationResponse } from '@/services/namingService'

const { TextArea } = Input
const { Text, Title } = Typography

interface NamingValidationProps {
  initialValue?: string
  secCode?: string
  onNormalized?: (normalizedName: string) => void
}

export default function NamingValidation({
  initialValue = '',
  secCode,
  onNormalized,
}: NamingValidationProps) {
  const [description, setDescription] = useState(initialValue)
  const [validationResult, setValidationResult] = useState<ValidationResponse | null>(null)

  // Validate mutation
  const validateMutation = useMutation({
    mutationFn: () =>
      namingService.validate({
        name: description,
        sec_code: secCode,
        strict_mode: false,
      }),
    onSuccess: (data) => {
      setValidationResult(data)
    },
  })

  // Generate mutation
  const generateMutation = useMutation({
    mutationFn: () =>
      namingService.generate({
        description,
        sec_code: secCode || 'SEC-01',
      }),
    onSuccess: (data) => {
      setDescription(data.natural_name)
      setValidationResult(data.validation)
      if (onNormalized) {
        onNormalized(data.natural_name)
      }
    },
  })

  // Get examples
  const { data: examples } = useQuery({
    queryKey: ['namingExamples', secCode],
    queryFn: () => namingService.getExamples(secCode, 5),
    enabled: !!secCode,
  })

  const handleValidate = () => {
    if (description.trim()) {
      validateMutation.mutate()
    }
  }

  const handleNormalize = () => {
    if (description.trim()) {
      generateMutation.mutate()
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#52c41a'
    if (confidence >= 60) return '#faad14'
    return '#ff4d4f'
  }

  return (
    <Card title="Naming Validation" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <TextArea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Enter description to validate..."
          rows={3}
        />

        <Space>
          <Button
            type="primary"
            onClick={handleValidate}
            loading={validateMutation.isPending}
          >
            Validate
          </Button>
          <Button
            icon={<ThunderboltOutlined />}
            onClick={handleNormalize}
            loading={generateMutation.isPending}
          >
            Auto-Normalize
          </Button>
        </Space>

        {(validateMutation.isPending || generateMutation.isPending) && (
          <Spin tip="Processing..." />
        )}

        {validationResult && (
          <>
            <Divider />

            <Space direction="vertical" style={{ width: '100%' }}>
              <Space>
                {validationResult.is_valid ? (
                  <Tag icon={<CheckCircleOutlined />} color="success">
                    Valid
                  </Tag>
                ) : (
                  <Tag icon={<CloseCircleOutlined />} color="error">
                    Invalid
                  </Tag>
                )}

                <Text type="secondary">
                  Confidence: {validationResult.confidence_score.toFixed(0)}%
                </Text>
                <Progress
                  percent={validationResult.confidence_score}
                  size="small"
                  strokeColor={getConfidenceColor(validationResult.confidence_score)}
                  style={{ width: 100 }}
                  showInfo={false}
                />
              </Space>

              <Space wrap>
                <Tag color={validationResult.has_verb ? 'green' : 'red'}>
                  {validationResult.has_verb ? 'Has Verb' : 'No Verb'}
                </Tag>
                <Tag color={validationResult.has_specs ? 'green' : 'red'}>
                  {validationResult.has_specs ? 'Has Specs' : 'No Specs'}
                </Tag>
                <Tag>Parts: {validationResult.parts_count}</Tag>
                <Tag>Length: {validationResult.length}</Tag>
              </Space>

              {validationResult.issues.length > 0 && (
                <Alert
                  type="warning"
                  message="Issues"
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {validationResult.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  }
                />
              )}

              {validationResult.suggestions && validationResult.suggestions.length > 0 && (
                <Alert
                  type="info"
                  icon={<BulbOutlined />}
                  message="Suggestions"
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {validationResult.suggestions.map((suggestion, idx) => (
                        <li key={idx}>{suggestion}</li>
                      ))}
                    </ul>
                  }
                />
              )}
            </Space>
          </>
        )}

        {examples && examples.examples.length > 0 && (
          <>
            <Divider />
            <Title level={5}>Examples for {secCode}</Title>
            <List
              size="small"
              dataSource={examples.examples}
              renderItem={(example) => (
                <List.Item>
                  <Space direction="vertical" size={0}>
                    <Text strong>{example.natural_name}</Text>
                    <Space size="small">
                      {example.parts.map((part, idx) => (
                        <Tag key={idx} size="small">
                          {part}
                        </Tag>
                      ))}
                    </Space>
                  </Space>
                </List.Item>
              )}
            />
          </>
        )}
      </Space>
    </Card>
  )
}
