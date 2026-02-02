import { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Space,
  Typography,
  Alert,
  Divider,
  Row,
  Col,
  Tag,
  Descriptions,
  Switch,
  message,
} from 'antd'
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CopyOutlined,
} from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import { masterItemsService, WorkCodeGenerateResponse } from '@/services/masterItemsService'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

export default function WorkCodeGenerator() {
  const [form] = Form.useForm()
  const [result, setResult] = useState<WorkCodeGenerateResponse | null>(null)

  const generateMutation = useMutation({
    mutationFn: masterItemsService.generateCode,
    onSuccess: (data) => {
      setResult(data)
      message.success('Work code generated successfully!')
    },
    onError: () => {
      message.error('Failed to generate work code')
    },
  })

  const handleGenerate = (values: any) => {
    generateMutation.mutate({
      description: values.description,
      sec_code: values.sec_code,
      unit: values.unit,
      include_grade: values.include_grade ?? true,
    })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    message.success('Copied to clipboard!')
  }

  return (
    <div>
      <Card
        title={
          <Space>
            <ThunderboltOutlined />
            <Title level={4} style={{ margin: 0 }}>
              Work Code Generator
            </Title>
          </Space>
        }
      >
        <Row gutter={24}>
          {/* Input Form */}
          <Col xs={24} lg={12}>
            <Card type="inner" title="Input">
              <Form
                form={form}
                layout="vertical"
                onFinish={handleGenerate}
                initialValues={{
                  sec_code: 'SEC-02',
                  include_grade: true,
                }}
              >
                <Form.Item
                  name="description"
                  label="Description"
                  rules={[
                    {
                      required: true,
                      message: 'Please enter description',
                    },
                  ]}
                >
                  <TextArea
                    rows={3}
                    placeholder="e.g., Bê tông M200 dầm"
                    showCount
                    maxLength={500}
                  />
                </Form.Item>

                <Form.Item
                  name="sec_code"
                  label="SEC Code"
                  rules={[
                    {
                      required: true,
                      message: 'Please select SEC code',
                    },
                  ]}
                >
                  <Select
                    options={[
                      {
                        label: 'SEC-00 - Preliminaries & General',
                        value: 'SEC-00',
                      },
                      {
                        label: 'SEC-01 - Substructure',
                        value: 'SEC-01',
                      },
                      {
                        label: 'SEC-01-01 - Earthworks',
                        value: 'SEC-01-01',
                      },
                      {
                        label: 'SEC-01-02 - Piling',
                        value: 'SEC-01-02',
                      },
                      {
                        label: 'SEC-01-03 - Foundation',
                        value: 'SEC-01-03',
                      },
                      {
                        label: 'SEC-02 - Superstructure',
                        value: 'SEC-02',
                      },
                      {
                        label: 'SEC-03 - Architecture & Finishes',
                        value: 'SEC-03',
                      },
                      {
                        label: 'SEC-04 - MEP Systems',
                        value: 'SEC-04',
                      },
                      {
                        label: 'SEC-05 - Landscape & External',
                        value: 'SEC-05',
                      },
                    ]}
                  />
                </Form.Item>

                <Form.Item name="unit" label="Unit (Optional)">
                  <Input placeholder="e.g., m3, m2, pcs" />
                </Form.Item>

                <Form.Item
                  name="include_grade"
                  label="Include Material Grade"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    block
                    icon={<ThunderboltOutlined />}
                    loading={generateMutation.isPending}
                  >
                    Generate Work Code
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </Col>

          {/* Result Display */}
          <Col xs={24} lg={12}>
            <Card type="inner" title="Result">
              {!result ? (
                <Alert
                  message="No Result Yet"
                  description="Enter description and SEC code, then click Generate to see the result."
                  type="info"
                  showIcon
                />
              ) : (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  {/* Work Code */}
                  <div>
                    <Text type="secondary">Generated Work Code:</Text>
                    <div
                      style={{
                        marginTop: 8,
                        padding: 16,
                        background: '#f0f2f5',
                        borderRadius: 8,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Text
                        strong
                        style={{ fontSize: 20, fontFamily: 'monospace' }}
                      >
                        {result.work_code}
                      </Text>
                      <Button
                        icon={<CopyOutlined />}
                        onClick={() => copyToClipboard(result.work_code)}
                      >
                        Copy
                      </Button>
                    </div>
                  </div>

                  {/* Validation Status */}
                  <Alert
                    message={
                      result.is_valid
                        ? 'Valid Work Code'
                        : 'Invalid Work Code'
                    }
                    description={
                      result.is_valid
                        ? 'This work code follows the correct format.'
                        : 'This work code does not follow the correct format.'
                    }
                    type={result.is_valid ? 'success' : 'error'}
                    icon={
                      result.is_valid ? (
                        <CheckCircleOutlined />
                      ) : (
                        <CloseCircleOutlined />
                      )
                    }
                    showIcon
                  />

                  <Divider />

                  {/* Parsed Components */}
                  {result.parsed && (
                    <Descriptions
                      title="Code Components"
                      column={1}
                      size="small"
                      bordered
                    >
                      <Descriptions.Item label="SEC Prefix">
                        <Tag color="blue">{result.parsed.sec_prefix}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Category">
                        <Tag color="green">{result.parsed.category}</Tag>
                      </Descriptions.Item>
                      <Descriptions.Item label="Sub-Category">
                        {result.parsed.sub_category ? (
                          <Tag color="purple">
                            {result.parsed.sub_category}
                          </Tag>
                        ) : (
                          <Text type="secondary">None</Text>
                        )}
                      </Descriptions.Item>
                      <Descriptions.Item label="Sequence">
                        <Tag>{result.parsed.sequence}</Tag>
                      </Descriptions.Item>
                    </Descriptions>
                  )}

                  {/* Material Grade */}
                  {result.material_grade && (
                    <Alert
                      message="Material Grade Detected"
                      description={
                        <Space direction="vertical">
                          <Text>
                            Detected material grade:{' '}
                            <Tag color="orange" style={{ fontSize: 16 }}>
                              {result.material_grade}
                            </Tag>
                          </Text>
                          <Text type="secondary">
                            This grade was automatically detected from the
                            description and included in the work code.
                          </Text>
                        </Space>
                      }
                      type="info"
                      showIcon
                    />
                  )}
                </Space>
              )}
            </Card>
          </Col>
        </Row>

        {/* Examples */}
        <Divider />
        <Card type="inner" title="Examples">
          <Paragraph>
            <Text strong>Common Patterns:</Text>
          </Paragraph>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Tag color="blue">S01-EARTH-EXCAV-0001</Tag>
              <Text type="secondary"> = Đào đất móng (SEC-01, Earthworks, Excavation)</Text>
            </div>
            <div>
              <Tag color="blue">S02-CONC-M200-0001</Tag>
              <Text type="secondary"> = Bê tông M200 dầm (SEC-02, Concrete, M200 grade)</Text>
            </div>
            <div>
              <Tag color="blue">S03-WALL-BRICK-0001</Tag>
              <Text type="secondary"> = Tường gạch (SEC-03, Wall, Brick)</Text>
            </div>
            <div>
              <Tag color="blue">S04-ELEC-0001</Tag>
              <Text type="secondary"> = Hệ thống điện (SEC-04, Electrical)</Text>
            </div>
            <div>
              <Tag color="blue">S05-ROAD-0001</Tag>
              <Text type="secondary"> = Đường nội bộ (SEC-05, Road)</Text>
            </div>
          </Space>
        </Card>
      </Card>
    </div>
  )
}
