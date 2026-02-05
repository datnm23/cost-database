import { useState } from 'react'
import {
  Card,
  Tabs,
  Input,
  Button,
  Space,
  Tag,
  Typography,
  Table,
  Row,
  Col,
  Alert,
  message,
  Select,
  Collapse,
  Badge,
  Spin,
  List,
  Tooltip,
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  BookOutlined,
  FileTextOutlined,
  BulbOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  namingService,
  ValidationResponse,
  GenerateResponse,
  VerbDictionaryItem,
  LocationDictionaryItem,
  NamingExample,
  BatchValidateResponse,
  BatchGenerateResponse,
} from '@/services/namingService'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

export default function NamingTools() {
  const [activeTab, setActiveTab] = useState('validate')

  // Validate Tab State
  const [validateInput, setValidateInput] = useState('')
  const [validationResult, setValidationResult] = useState<ValidationResponse | null>(null)

  // Generate Tab State
  const [generateDescription, setGenerateDescription] = useState('')
  const [generateSecCode, setGenerateSecCode] = useState('')
  const [generateResult, setGenerateResult] = useState<GenerateResponse | null>(null)

  // Batch Tab State
  const [batchInput, setBatchInput] = useState('')
  const [batchMode, setBatchMode] = useState<'validate' | 'generate'>('validate')
  const [batchSecCode, setBatchSecCode] = useState('')
  const [batchValidateResult, setBatchValidateResult] = useState<BatchValidateResponse | null>(null)
  const [batchGenerateResult, setBatchGenerateResult] = useState<BatchGenerateResponse | null>(null)

  // Dictionary Tab State
  const [verbCategory, setVerbCategory] = useState<string | undefined>()
  const [dictionarySearch, setDictionarySearch] = useState('')

  // Examples Tab State
  const [examplesSecCode, setExamplesSecCode] = useState<string | undefined>()

  // Fetch dictionaries
  const { data: verbs, isLoading: verbsLoading } = useQuery({
    queryKey: ['namingVerbs', verbCategory],
    queryFn: () => namingService.getVerbs(verbCategory),
  })

  const { data: locations, isLoading: locationsLoading } = useQuery({
    queryKey: ['namingLocations'],
    queryFn: () => namingService.getLocations(),
  })

  const { data: examples, isLoading: examplesLoading, refetch: refetchExamples } = useQuery({
    queryKey: ['namingExamples', examplesSecCode],
    queryFn: () => namingService.getExamples(examplesSecCode, 50),
  })

  // Mutations
  const validateMutation = useMutation({
    mutationFn: (name: string) =>
      namingService.validate({ name, strict_mode: true }),
    onSuccess: (data) => setValidationResult(data),
    onError: () => message.error('Failed to validate name'),
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      namingService.generate({
        description: generateDescription,
        sec_code: generateSecCode,
      }),
    onSuccess: (data) => setGenerateResult(data),
    onError: () => message.error('Failed to generate name'),
  })

  const batchValidateMutation = useMutation({
    mutationFn: (names: string[]) => namingService.batchValidate(names, true),
    onSuccess: (data) => {
      setBatchValidateResult(data)
      setBatchGenerateResult(null)
    },
    onError: () => message.error('Failed to batch validate'),
  })

  const batchGenerateMutation = useMutation({
    mutationFn: (items: Array<{ description: string; sec_code: string }>) =>
      namingService.batchGenerate(items),
    onSuccess: (data) => {
      setBatchGenerateResult(data)
      setBatchValidateResult(null)
    },
    onError: () => message.error('Failed to batch generate'),
  })

  const handleValidate = () => {
    if (validateInput.trim()) {
      validateMutation.mutate(validateInput.trim())
    }
  }

  const handleGenerate = () => {
    if (generateDescription.trim() && generateSecCode.trim()) {
      generateMutation.mutate()
    }
  }

  const handleBatchProcess = () => {
    const lines = batchInput
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l)

    if (lines.length === 0) {
      message.warning('Please enter at least one item')
      return
    }

    if (batchMode === 'validate') {
      batchValidateMutation.mutate(lines)
    } else {
      if (!batchSecCode) {
        message.warning('Please select a SEC code for generation')
        return
      }
      const items = lines.map((description) => ({
        description,
        sec_code: batchSecCode,
      }))
      batchGenerateMutation.mutate(items)
    }
  }

  const filteredVerbs = verbs?.filter(
    (v) =>
      !dictionarySearch ||
      v.vn_verb.toLowerCase().includes(dictionarySearch.toLowerCase()) ||
      v.en_key.toLowerCase().includes(dictionarySearch.toLowerCase())
  )

  const filteredLocations = locations?.filter(
    (l) =>
      !dictionarySearch ||
      l.vn_location.toLowerCase().includes(dictionarySearch.toLowerCase()) ||
      l.en_key.toLowerCase().includes(dictionarySearch.toLowerCase())
  )

  const verbColumns: ColumnsType<VerbDictionaryItem> = [
    { title: 'English Key', dataIndex: 'en_key', key: 'en_key', width: 150 },
    { title: 'Vietnamese Verb', dataIndex: 'vn_verb', key: 'vn_verb', width: 200 },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 150,
      render: (cat: string) => <Tag color="blue">{cat}</Tag>,
    },
    {
      title: 'Examples',
      dataIndex: 'examples',
      key: 'examples',
      render: (exs: string[]) => exs?.slice(0, 2).join(', ') || '-',
    },
  ]

  const locationColumns: ColumnsType<LocationDictionaryItem> = [
    { title: 'English Key', dataIndex: 'en_key', key: 'en_key', width: 150 },
    { title: 'Vietnamese Location', dataIndex: 'vn_location', key: 'vn_location', width: 200 },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 150,
      render: (cat: string) => <Tag color="green">{cat}</Tag>,
    },
    {
      title: 'SEC Codes',
      dataIndex: 'sec_codes',
      key: 'sec_codes',
      render: (codes: string[]) =>
        codes?.map((c) => <Tag key={c}>{c}</Tag>) || '-',
    },
  ]

  const exampleColumns: ColumnsType<NamingExample> = [
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
      width: 100,
      render: (code: string) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: 'Natural Name',
      dataIndex: 'natural_name',
      key: 'natural_name',
      width: 400,
    },
    {
      title: 'Parts',
      dataIndex: 'parts',
      key: 'parts',
      render: (parts: string[]) =>
        parts?.map((p, i) => (
          <Tag key={i} color={['green', 'blue', 'orange', 'purple'][i % 4]}>
            {p}
          </Tag>
        )),
    },
    {
      title: 'Has Verb',
      dataIndex: 'has_verb',
      key: 'has_verb',
      width: 80,
      render: (v: boolean) =>
        v ? (
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
        ) : (
          <CloseCircleOutlined style={{ color: '#d9d9d9' }} />
        ),
    },
    {
      title: 'Has Specs',
      dataIndex: 'has_specs',
      key: 'has_specs',
      width: 80,
      render: (v: boolean) =>
        v ? (
          <CheckCircleOutlined style={{ color: '#52c41a' }} />
        ) : (
          <CloseCircleOutlined style={{ color: '#d9d9d9' }} />
        ),
    },
  ]

  return (
    <div>
      <Title level={3}>
        <EditOutlined /> Naming Tools
      </Title>
      <Text type="secondary">
        Validate and generate standardized work descriptions following the 4-part syntax
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'validate',
              label: (
                <span>
                  <CheckCircleOutlined />
                  Validate
                </span>
              ),
              children: (
                <div>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>Check if a description follows the 4-part naming syntax:</Text>
                    <Input
                      size="large"
                      placeholder="Enter a work description to validate..."
                      value={validateInput}
                      onChange={(e) => setValidateInput(e.target.value)}
                      onPressEnter={handleValidate}
                      suffix={
                        <Button
                          type="primary"
                          onClick={handleValidate}
                          loading={validateMutation.isPending}
                        >
                          Validate
                        </Button>
                      }
                    />

                    {validationResult && (
                      <Card size="small" style={{ marginTop: 16 }}>
                        <Row gutter={16}>
                          <Col span={12}>
                            <Space direction="vertical" style={{ width: '100%' }}>
                              <Space>
                                <Text strong>Result:</Text>
                                {validationResult.is_valid ? (
                                  <Tag icon={<CheckCircleOutlined />} color="success">
                                    Valid
                                  </Tag>
                                ) : (
                                  <Tag icon={<CloseCircleOutlined />} color="error">
                                    Invalid
                                  </Tag>
                                )}
                              </Space>

                              <Space>
                                <Text>Confidence:</Text>
                                <Badge
                                  count={`${Math.round(validationResult.confidence_score * 100)}%`}
                                  style={{
                                    backgroundColor:
                                      validationResult.confidence_score >= 0.8
                                        ? '#52c41a'
                                        : validationResult.confidence_score >= 0.5
                                        ? '#faad14'
                                        : '#ff4d4f',
                                  }}
                                />
                              </Space>

                              <div>
                                <Text>Parts:</Text>
                                <Space style={{ marginLeft: 8 }}>
                                  <Tag color={validationResult.has_verb ? 'green' : 'red'}>
                                    Verb: {validationResult.has_verb ? '✓' : '✗'}
                                  </Tag>
                                  <Tag color={validationResult.has_specs ? 'green' : 'red'}>
                                    Specs: {validationResult.has_specs ? '✓' : '✗'}
                                  </Tag>
                                  <Tag>Parts: {validationResult.parts_count}</Tag>
                                </Space>
                              </div>
                            </Space>
                          </Col>
                          <Col span={12}>
                            {validationResult.issues.length > 0 && (
                              <Alert
                                type="warning"
                                message="Issues Found"
                                description={
                                  <ul style={{ margin: 0, paddingLeft: 16 }}>
                                    {validationResult.issues.map((issue, i) => (
                                      <li key={i}>{issue}</li>
                                    ))}
                                  </ul>
                                }
                              />
                            )}
                            {validationResult.suggestions &&
                              validationResult.suggestions.length > 0 && (
                                <Alert
                                  type="info"
                                  message="Suggestions"
                                  style={{ marginTop: 8 }}
                                  description={
                                    <ul style={{ margin: 0, paddingLeft: 16 }}>
                                      {validationResult.suggestions.map((sug, i) => (
                                        <li key={i}>{sug}</li>
                                      ))}
                                    </ul>
                                  }
                                />
                              )}
                          </Col>
                        </Row>
                      </Card>
                    )}
                  </Space>
                </div>
              ),
            },
            {
              key: 'generate',
              label: (
                <span>
                  <BulbOutlined />
                  Generate
                </span>
              ),
              children: (
                <div>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>Generate a standardized natural name from a raw description:</Text>
                    <Row gutter={16}>
                      <Col span={16}>
                        <Input
                          size="large"
                          placeholder="Enter raw description..."
                          value={generateDescription}
                          onChange={(e) => setGenerateDescription(e.target.value)}
                        />
                      </Col>
                      <Col span={8}>
                        <Select
                          size="large"
                          style={{ width: '100%' }}
                          placeholder="Select SEC code"
                          value={generateSecCode || undefined}
                          onChange={setGenerateSecCode}
                          options={[
                            { label: 'ARC - Architecture', value: 'ARC' },
                            { label: 'STR - Structure', value: 'STR' },
                            { label: 'MEP - M&E/Plumbing', value: 'MEP' },
                            { label: 'ELE - Electrical', value: 'ELE' },
                            { label: 'CIV - Civil', value: 'CIV' },
                            { label: 'LAN - Landscape', value: 'LAN' },
                          ]}
                        />
                      </Col>
                    </Row>
                    <Button
                      type="primary"
                      onClick={handleGenerate}
                      loading={generateMutation.isPending}
                      disabled={!generateDescription || !generateSecCode}
                    >
                      Generate Natural Name
                    </Button>

                    {generateResult && (
                      <Card size="small" style={{ marginTop: 16 }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div>
                            <Text type="secondary">Original:</Text>
                            <Paragraph style={{ margin: '4px 0' }}>
                              {generateResult.original_description}
                            </Paragraph>
                          </div>
                          <div>
                            <Text type="secondary">Generated Natural Name:</Text>
                            <Paragraph
                              strong
                              copyable
                              style={{ margin: '4px 0', fontSize: 16 }}
                            >
                              {generateResult.natural_name}
                            </Paragraph>
                          </div>
                          <Space>
                            <Text>Validation:</Text>
                            {generateResult.validation.is_valid ? (
                              <Tag icon={<CheckCircleOutlined />} color="success">
                                Valid
                              </Tag>
                            ) : (
                              <Tag icon={<CloseCircleOutlined />} color="error">
                                Invalid
                              </Tag>
                            )}
                            <Badge
                              count={`${Math.round(
                                generateResult.validation.confidence_score * 100
                              )}%`}
                              style={{ backgroundColor: '#1890ff' }}
                            />
                          </Space>
                        </Space>
                      </Card>
                    )}
                  </Space>
                </div>
              ),
            },
            {
              key: 'batch',
              label: (
                <span>
                  <FileTextOutlined />
                  Batch Process
                </span>
              ),
              children: (
                <div>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Select
                          style={{ width: '100%' }}
                          value={batchMode}
                          onChange={setBatchMode}
                          options={[
                            { label: 'Validate Names', value: 'validate' },
                            { label: 'Generate Names', value: 'generate' },
                          ]}
                        />
                      </Col>
                      {batchMode === 'generate' && (
                        <Col span={12}>
                          <Select
                            style={{ width: '100%' }}
                            placeholder="Select SEC code for generation"
                            value={batchSecCode || undefined}
                            onChange={setBatchSecCode}
                            options={[
                              { label: 'ARC - Architecture', value: 'ARC' },
                              { label: 'STR - Structure', value: 'STR' },
                              { label: 'MEP - M&E/Plumbing', value: 'MEP' },
                              { label: 'ELE - Electrical', value: 'ELE' },
                              { label: 'CIV - Civil', value: 'CIV' },
                              { label: 'LAN - Landscape', value: 'LAN' },
                            ]}
                          />
                        </Col>
                      )}
                    </Row>
                    <TextArea
                      rows={8}
                      placeholder="Enter one description per line..."
                      value={batchInput}
                      onChange={(e) => setBatchInput(e.target.value)}
                    />
                    <Button
                      type="primary"
                      onClick={handleBatchProcess}
                      loading={
                        batchValidateMutation.isPending || batchGenerateMutation.isPending
                      }
                    >
                      Process Batch
                    </Button>

                    {batchValidateResult && (
                      <Card size="small" style={{ marginTop: 16 }}>
                        <Row gutter={16} style={{ marginBottom: 16 }}>
                          <Col span={8}>
                            <Statistic title="Total" value={batchValidateResult.total} />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="Valid"
                              value={batchValidateResult.valid}
                              valueStyle={{ color: '#52c41a' }}
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="Invalid"
                              value={batchValidateResult.invalid}
                              valueStyle={{ color: '#ff4d4f' }}
                            />
                          </Col>
                        </Row>
                        <Table
                          dataSource={batchValidateResult.results}
                          rowKey="name"
                          size="small"
                          pagination={{ pageSize: 10 }}
                          columns={[
                            {
                              title: 'Name',
                              dataIndex: 'name',
                              key: 'name',
                              ellipsis: true,
                            },
                            {
                              title: 'Valid',
                              dataIndex: 'is_valid',
                              key: 'is_valid',
                              width: 80,
                              render: (v: boolean) =>
                                v ? (
                                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                ) : (
                                  <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                                ),
                            },
                            {
                              title: 'Confidence',
                              dataIndex: 'confidence_score',
                              key: 'confidence_score',
                              width: 100,
                              render: (v: number) => `${Math.round(v * 100)}%`,
                            },
                            {
                              title: 'Issues',
                              dataIndex: 'issues',
                              key: 'issues',
                              render: (issues: string[]) => issues?.join(', ') || '-',
                            },
                          ]}
                        />
                      </Card>
                    )}

                    {batchGenerateResult && (
                      <Card size="small" style={{ marginTop: 16 }}>
                        <Row gutter={16} style={{ marginBottom: 16 }}>
                          <Col span={8}>
                            <Statistic title="Total" value={batchGenerateResult.total} />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="Successful"
                              value={batchGenerateResult.successful}
                              valueStyle={{ color: '#52c41a' }}
                            />
                          </Col>
                          <Col span={8}>
                            <Statistic
                              title="Failed"
                              value={batchGenerateResult.failed}
                              valueStyle={{ color: '#ff4d4f' }}
                            />
                          </Col>
                        </Row>
                        <Table
                          dataSource={batchGenerateResult.results}
                          rowKey="original"
                          size="small"
                          pagination={{ pageSize: 10 }}
                          columns={[
                            {
                              title: 'Original',
                              dataIndex: 'original',
                              key: 'original',
                              ellipsis: true,
                            },
                            {
                              title: 'Generated',
                              dataIndex: 'natural_name',
                              key: 'natural_name',
                              ellipsis: true,
                            },
                            {
                              title: 'Status',
                              dataIndex: 'status',
                              key: 'status',
                              width: 100,
                              render: (s: string) =>
                                s === 'success' ? (
                                  <Tag color="success">Success</Tag>
                                ) : (
                                  <Tag color="error">Error</Tag>
                                ),
                            },
                          ]}
                        />
                      </Card>
                    )}
                  </Space>
                </div>
              ),
            },
            {
              key: 'dictionary',
              label: (
                <span>
                  <BookOutlined />
                  Dictionary
                </span>
              ),
              children: (
                <div>
                  <Space style={{ marginBottom: 16 }}>
                    <Input.Search
                      placeholder="Search dictionary..."
                      style={{ width: 300 }}
                      value={dictionarySearch}
                      onChange={(e) => setDictionarySearch(e.target.value)}
                    />
                    <Select
                      placeholder="Filter by category"
                      allowClear
                      style={{ width: 200 }}
                      value={verbCategory}
                      onChange={setVerbCategory}
                      options={[
                        { label: 'Construction', value: 'construction' },
                        { label: 'Installation', value: 'installation' },
                        { label: 'Finishing', value: 'finishing' },
                        { label: 'MEP', value: 'mep' },
                      ]}
                    />
                  </Space>

                  <Collapse defaultActiveKey={['verbs']}>
                    <Collapse.Panel
                      header={
                        <Space>
                          <Text strong>Verbs</Text>
                          <Badge count={filteredVerbs?.length || 0} style={{ backgroundColor: '#1890ff' }} />
                        </Space>
                      }
                      key="verbs"
                    >
                      <Spin spinning={verbsLoading}>
                        <Table
                          columns={verbColumns}
                          dataSource={filteredVerbs}
                          rowKey="en_key"
                          size="small"
                          pagination={{ pageSize: 10 }}
                        />
                      </Spin>
                    </Collapse.Panel>
                    <Collapse.Panel
                      header={
                        <Space>
                          <Text strong>Locations</Text>
                          <Badge
                            count={filteredLocations?.length || 0}
                            style={{ backgroundColor: '#52c41a' }}
                          />
                        </Space>
                      }
                      key="locations"
                    >
                      <Spin spinning={locationsLoading}>
                        <Table
                          columns={locationColumns}
                          dataSource={filteredLocations}
                          rowKey="en_key"
                          size="small"
                          pagination={{ pageSize: 10 }}
                        />
                      </Spin>
                    </Collapse.Panel>
                  </Collapse>
                </div>
              ),
            },
            {
              key: 'examples',
              label: (
                <span>
                  <FileTextOutlined />
                  Examples
                </span>
              ),
              children: (
                <div>
                  <Space style={{ marginBottom: 16 }}>
                    <Select
                      placeholder="Filter by SEC code"
                      allowClear
                      style={{ width: 200 }}
                      value={examplesSecCode}
                      onChange={setExamplesSecCode}
                      options={[
                        { label: 'All SEC Codes', value: undefined },
                        { label: 'ARC - Architecture', value: 'ARC' },
                        { label: 'STR - Structure', value: 'STR' },
                        { label: 'MEP - M&E/Plumbing', value: 'MEP' },
                        { label: 'ELE - Electrical', value: 'ELE' },
                        { label: 'CIV - Civil', value: 'CIV' },
                        { label: 'LAN - Landscape', value: 'LAN' },
                      ]}
                    />
                    <Button icon={<ReloadOutlined />} onClick={() => refetchExamples()}>
                      Refresh
                    </Button>
                  </Space>

                  <Spin spinning={examplesLoading}>
                    <Text type="secondary" style={{ marginBottom: 16, display: 'block' }}>
                      Showing {examples?.examples?.length || 0} of {examples?.total || 0} examples
                    </Text>
                    <Table
                      columns={exampleColumns}
                      dataSource={examples?.examples}
                      rowKey="natural_name"
                      size="small"
                      pagination={{ pageSize: 15 }}
                    />
                  </Spin>
                </div>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

function Statistic({ title, value, valueStyle }: { title: string; value: number; valueStyle?: React.CSSProperties }) {
  return (
    <div>
      <Text type="secondary">{title}</Text>
      <div style={{ fontSize: 24, fontWeight: 'bold', ...valueStyle }}>{value}</div>
    </div>
  )
}
