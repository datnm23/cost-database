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
  message,
  Select,
  Descriptions,
  Tree,
  Spin,
  Progress,
  Alert,
  Statistic,
  Empty,
} from 'antd'
import {
  BarcodeOutlined,
  SearchOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  ApartmentOutlined,
  GlobalOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  codeService,
  LegalCodeParsed,
  LegalCodeSearchResult,
  LegalCodeGenerateResult,
  LegalCodeStats,
  ISOCodeParsed,
  ISOCodeGenerateResult,
  MultiCodeMappingResult,
} from '@/services/codeService'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

export default function CodeManagement() {
  const [activeTab, setActiveTab] = useState('legal')

  // Legal Tab State
  const [legalCodeInput, setLegalCodeInput] = useState('')
  const [legalParsed, setLegalParsed] = useState<LegalCodeParsed | null>(null)
  const [legalSearchPrefix, setLegalSearchPrefix] = useState<string | undefined>()
  const [legalSearchAppendix, setLegalSearchAppendix] = useState<string | undefined>()
  const [legalSearchQuery, setLegalSearchQuery] = useState('')
  const [legalSearchResults, setLegalSearchResults] = useState<LegalCodeSearchResult[]>([])
  const [legalGenDescription, setLegalGenDescription] = useState('')
  const [legalGenResult, setLegalGenResult] = useState<LegalCodeGenerateResult | null>(null)

  // ISO Tab State
  const [isoCodeInput, setIsoCodeInput] = useState('')
  const [isoParsed, setIsoParsed] = useState<ISOCodeParsed | null>(null)
  const [isoGenDescription, setIsoGenDescription] = useState('')
  const [isoGenResult, setIsoGenResult] = useState<ISOCodeGenerateResult | null>(null)

  // Multi-Code Tab State
  const [multiDescription, setMultiDescription] = useState('')
  const [multiSecCode, setMultiSecCode] = useState<string | undefined>()
  const [multiResult, setMultiResult] = useState<MultiCodeMappingResult | null>(null)
  const [multiSearchQuery, setMultiSearchQuery] = useState('')

  // Fetch legal stats
  const { data: legalStats, isLoading: legalStatsLoading } = useQuery({
    queryKey: ['legalStats'],
    queryFn: codeService.getLegalStats,
    enabled: activeTab === 'legal',
  })

  // Mutations
  const parseLegalMutation = useMutation({
    mutationFn: (code: string) => codeService.parseLegalCode(code),
    onSuccess: (data) => setLegalParsed(data),
    onError: () => message.error('Failed to parse legal code'),
  })

  const searchLegalMutation = useMutation({
    mutationFn: () =>
      codeService.searchLegalCodes({
        prefix: legalSearchPrefix,
        appendix: legalSearchAppendix,
        query: legalSearchQuery,
        limit: 50,
      }),
    onSuccess: (data) => setLegalSearchResults(data),
    onError: () => message.error('Failed to search legal codes'),
  })

  const generateLegalMutation = useMutation({
    mutationFn: (description: string) => codeService.generateLegalCode(description),
    onSuccess: (data) => setLegalGenResult(data),
    onError: () => message.error('Failed to generate legal code'),
  })

  const parseISOMutation = useMutation({
    mutationFn: (code: string) => codeService.parseISOCode(code),
    onSuccess: (data) => setIsoParsed(data),
    onError: () => message.error('Failed to parse ISO code'),
  })

  const generateISOMutation = useMutation({
    mutationFn: (description: string) => codeService.generateISOCode(description),
    onSuccess: (data) => setIsoGenResult(data),
    onError: () => message.error('Failed to generate ISO code'),
  })

  const autoMapMutation = useMutation({
    mutationFn: () => codeService.autoMapCodes(multiDescription, multiSecCode),
    onSuccess: (data) => setMultiResult(data),
    onError: () => message.error('Failed to auto-map codes'),
  })

  const multiSearchMutation = useMutation({
    mutationFn: (query: string) => codeService.multiCodeSearch(query),
  })

  const legalSearchColumns: ColumnsType<LegalCodeSearchResult> = [
    {
      title: 'Code',
      dataIndex: 'code',
      key: 'code',
      width: 150,
      render: (code: string) => <Text strong copyable>{code}</Text>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Prefix',
      dataIndex: 'prefix',
      key: 'prefix',
      width: 100,
      render: (p: string) => <Tag color="blue">{p}</Tag>,
    },
    {
      title: 'Appendix',
      dataIndex: 'appendix',
      key: 'appendix',
      width: 100,
      render: (a: string) => <Tag color="green">{a}</Tag>,
    },
  ]

  return (
    <div>
      <Title level={3}>
        <BarcodeOutlined /> Code Systems Management
      </Title>
      <Text type="secondary">
        Manage Legal (Vietnamese) and ISO code mappings for work items
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            {
              key: 'legal',
              label: (
                <span>
                  <BarcodeOutlined />
                  Legal Codes
                </span>
              ),
              children: (
                <Tabs
                  type="card"
                  items={[
                    {
                      key: 'parse',
                      label: 'Parse Code',
                      children: (
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text>Parse a legal code to understand its structure:</Text>
                          <Space.Compact style={{ width: '100%' }}>
                            <Input
                              placeholder="Enter legal code (e.g., AB.12345)"
                              value={legalCodeInput}
                              onChange={(e) => setLegalCodeInput(e.target.value)}
                              onPressEnter={() =>
                                legalCodeInput && parseLegalMutation.mutate(legalCodeInput)
                              }
                            />
                            <Button
                              type="primary"
                              onClick={() => parseLegalMutation.mutate(legalCodeInput)}
                              loading={parseLegalMutation.isPending}
                            >
                              Parse
                            </Button>
                          </Space.Compact>

                          {legalParsed && (
                            <Card size="small" style={{ marginTop: 16 }}>
                              <Descriptions bordered size="small" column={2}>
                                <Descriptions.Item label="Code">
                                  <Text strong copyable>{legalParsed.code}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Valid">
                                  {legalParsed.is_valid ? (
                                    <Tag color="success">Valid</Tag>
                                  ) : (
                                    <Tag color="error">Invalid</Tag>
                                  )}
                                </Descriptions.Item>
                                <Descriptions.Item label="Prefix">
                                  <Tag color="blue">{legalParsed.prefix}</Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Appendix">
                                  <Tag color="green">{legalParsed.appendix}</Tag>
                                </Descriptions.Item>
                                {legalParsed.chapter && (
                                  <Descriptions.Item label="Chapter">
                                    {legalParsed.chapter}
                                  </Descriptions.Item>
                                )}
                                {legalParsed.section && (
                                  <Descriptions.Item label="Section">
                                    {legalParsed.section}
                                  </Descriptions.Item>
                                )}
                                {legalParsed.description && (
                                  <Descriptions.Item label="Description" span={2}>
                                    {legalParsed.description}
                                  </Descriptions.Item>
                                )}
                              </Descriptions>
                            </Card>
                          )}
                        </Space>
                      ),
                    },
                    {
                      key: 'search',
                      label: 'Search Codes',
                      children: (
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Row gutter={16}>
                            <Col span={6}>
                              <Select
                                placeholder="Filter by prefix"
                                allowClear
                                style={{ width: '100%' }}
                                value={legalSearchPrefix}
                                onChange={setLegalSearchPrefix}
                                options={
                                  legalStats?.by_prefix
                                    ? Object.keys(legalStats.by_prefix).map((p) => ({
                                        label: `${p} (${legalStats.by_prefix[p]})`,
                                        value: p,
                                      }))
                                    : []
                                }
                              />
                            </Col>
                            <Col span={6}>
                              <Select
                                placeholder="Filter by appendix"
                                allowClear
                                style={{ width: '100%' }}
                                value={legalSearchAppendix}
                                onChange={setLegalSearchAppendix}
                                options={
                                  legalStats?.by_appendix
                                    ? Object.keys(legalStats.by_appendix).map((a) => ({
                                        label: `${a} (${legalStats.by_appendix[a]})`,
                                        value: a,
                                      }))
                                    : []
                                }
                              />
                            </Col>
                            <Col span={8}>
                              <Input
                                placeholder="Search description..."
                                value={legalSearchQuery}
                                onChange={(e) => setLegalSearchQuery(e.target.value)}
                                onPressEnter={() => searchLegalMutation.mutate()}
                              />
                            </Col>
                            <Col span={4}>
                              <Button
                                type="primary"
                                icon={<SearchOutlined />}
                                onClick={() => searchLegalMutation.mutate()}
                                loading={searchLegalMutation.isPending}
                                style={{ width: '100%' }}
                              >
                                Search
                              </Button>
                            </Col>
                          </Row>

                          <Table
                            columns={legalSearchColumns}
                            dataSource={legalSearchResults}
                            rowKey="code"
                            size="small"
                            pagination={{ pageSize: 15 }}
                            locale={{ emptyText: 'Enter search criteria and click Search' }}
                          />
                        </Space>
                      ),
                    },
                    {
                      key: 'generate',
                      label: 'Generate Code',
                      children: (
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text>Generate a legal code from a work description:</Text>
                          <TextArea
                            rows={3}
                            placeholder="Enter work description..."
                            value={legalGenDescription}
                            onChange={(e) => setLegalGenDescription(e.target.value)}
                          />
                          <Button
                            type="primary"
                            icon={<ThunderboltOutlined />}
                            onClick={() => generateLegalMutation.mutate(legalGenDescription)}
                            loading={generateLegalMutation.isPending}
                            disabled={!legalGenDescription}
                          >
                            Generate Legal Code
                          </Button>

                          {legalGenResult && (
                            <Card size="small" style={{ marginTop: 16 }}>
                              <Space direction="vertical" style={{ width: '100%' }}>
                                <div>
                                  <Text type="secondary">Suggested Code:</Text>
                                  <Paragraph
                                    strong
                                    copyable
                                    style={{ margin: '4px 0', fontSize: 18 }}
                                  >
                                    {legalGenResult.suggested_code}
                                  </Paragraph>
                                </div>
                                <Space>
                                  <Text>Confidence:</Text>
                                  <Progress
                                    type="circle"
                                    size={60}
                                    percent={Math.round(legalGenResult.confidence * 100)}
                                  />
                                </Space>
                                {legalGenResult.alternatives &&
                                  legalGenResult.alternatives.length > 0 && (
                                    <div>
                                      <Text type="secondary">Alternatives:</Text>
                                      <div style={{ marginTop: 4 }}>
                                        {legalGenResult.alternatives.map((alt) => (
                                          <Tag key={alt}>{alt}</Tag>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                              </Space>
                            </Card>
                          )}
                        </Space>
                      ),
                    },
                    {
                      key: 'stats',
                      label: 'Statistics',
                      children: (
                        <Spin spinning={legalStatsLoading}>
                          {legalStats ? (
                            <Row gutter={[16, 16]}>
                              <Col span={6}>
                                <Card>
                                  <Statistic
                                    title="Total Legal Codes"
                                    value={legalStats.total_codes}
                                    prefix={<BarcodeOutlined />}
                                  />
                                </Card>
                              </Col>
                              <Col span={9}>
                                <Card title="By Prefix">
                                  {Object.entries(legalStats.by_prefix)
                                    .slice(0, 5)
                                    .map(([prefix, count]) => (
                                      <Tag key={prefix} style={{ marginBottom: 4 }}>
                                        {prefix}: {count}
                                      </Tag>
                                    ))}
                                </Card>
                              </Col>
                              <Col span={9}>
                                <Card title="Most Used">
                                  {legalStats.most_used.slice(0, 5).map((item) => (
                                    <div key={item.code} style={{ marginBottom: 4 }}>
                                      <Text code>{item.code}</Text>
                                      <Tag style={{ marginLeft: 8 }}>{item.count}</Tag>
                                    </div>
                                  ))}
                                </Card>
                              </Col>
                            </Row>
                          ) : (
                            <Empty description="No statistics available" />
                          )}
                        </Spin>
                      ),
                    },
                  ]}
                />
              ),
            },
            {
              key: 'iso',
              label: (
                <span>
                  <GlobalOutlined />
                  ISO Codes
                </span>
              ),
              children: (
                <Tabs
                  type="card"
                  items={[
                    {
                      key: 'parse',
                      label: 'Parse Code',
                      children: (
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text>Parse an ISO code to understand its hierarchy:</Text>
                          <Space.Compact style={{ width: '100%' }}>
                            <Input
                              placeholder="Enter ISO code..."
                              value={isoCodeInput}
                              onChange={(e) => setIsoCodeInput(e.target.value)}
                              onPressEnter={() =>
                                isoCodeInput && parseISOMutation.mutate(isoCodeInput)
                              }
                            />
                            <Button
                              type="primary"
                              onClick={() => parseISOMutation.mutate(isoCodeInput)}
                              loading={parseISOMutation.isPending}
                            >
                              Parse
                            </Button>
                          </Space.Compact>

                          {isoParsed && (
                            <Card size="small" style={{ marginTop: 16 }}>
                              <Descriptions bordered size="small" column={2}>
                                <Descriptions.Item label="Code">
                                  <Text strong copyable>{isoParsed.code}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Valid">
                                  {isoParsed.is_valid ? (
                                    <Tag color="success">Valid</Tag>
                                  ) : (
                                    <Tag color="error">Invalid</Tag>
                                  )}
                                </Descriptions.Item>
                                <Descriptions.Item label="System">
                                  <Tag color="purple">{isoParsed.system}</Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Group">
                                  <Tag color="blue">{isoParsed.group}</Tag>
                                </Descriptions.Item>
                                <Descriptions.Item label="Class">
                                  <Tag color="cyan">{isoParsed.class}</Tag>
                                </Descriptions.Item>
                                {isoParsed.subclass && (
                                  <Descriptions.Item label="Subclass">
                                    <Tag color="green">{isoParsed.subclass}</Tag>
                                  </Descriptions.Item>
                                )}
                                {isoParsed.description && (
                                  <Descriptions.Item label="Description" span={2}>
                                    {isoParsed.description}
                                  </Descriptions.Item>
                                )}
                              </Descriptions>
                            </Card>
                          )}
                        </Space>
                      ),
                    },
                    {
                      key: 'generate',
                      label: 'Generate Code',
                      children: (
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Text>Generate an ISO code from a work description:</Text>
                          <TextArea
                            rows={3}
                            placeholder="Enter work description..."
                            value={isoGenDescription}
                            onChange={(e) => setIsoGenDescription(e.target.value)}
                          />
                          <Button
                            type="primary"
                            icon={<ThunderboltOutlined />}
                            onClick={() => generateISOMutation.mutate(isoGenDescription)}
                            loading={generateISOMutation.isPending}
                            disabled={!isoGenDescription}
                          >
                            Generate ISO Code
                          </Button>

                          {isoGenResult && (
                            <Card size="small" style={{ marginTop: 16 }}>
                              <Space direction="vertical" style={{ width: '100%' }}>
                                <div>
                                  <Text type="secondary">Suggested Code:</Text>
                                  <Paragraph
                                    strong
                                    copyable
                                    style={{ margin: '4px 0', fontSize: 18 }}
                                  >
                                    {isoGenResult.suggested_code}
                                  </Paragraph>
                                </div>
                                <Space>
                                  <Text>Confidence:</Text>
                                  <Progress
                                    type="circle"
                                    size={60}
                                    percent={Math.round(isoGenResult.confidence * 100)}
                                  />
                                </Space>
                                {isoGenResult.hierarchy && isoGenResult.hierarchy.length > 0 && (
                                  <div>
                                    <Text type="secondary">Hierarchy:</Text>
                                    <div style={{ marginTop: 4 }}>
                                      {isoGenResult.hierarchy.map((level, i) => (
                                        <span key={i}>
                                          {i > 0 && ' → '}
                                          <Tag>{level}</Tag>
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </Space>
                            </Card>
                          )}
                        </Space>
                      ),
                    },
                  ]}
                />
              ),
            },
            {
              key: 'multi',
              label: (
                <span>
                  <ApartmentOutlined />
                  Multi-Code Mapping
                </span>
              ),
              children: (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Alert
                    message="Auto-Map All Codes"
                    description="Automatically map a work description to SEC, Legal, ISO, and Work codes"
                    type="info"
                    showIcon
                  />

                  <Row gutter={16}>
                    <Col span={18}>
                      <TextArea
                        rows={2}
                        placeholder="Enter work description..."
                        value={multiDescription}
                        onChange={(e) => setMultiDescription(e.target.value)}
                      />
                    </Col>
                    <Col span={6}>
                      <Select
                        placeholder="SEC code (optional)"
                        allowClear
                        style={{ width: '100%', marginBottom: 8 }}
                        value={multiSecCode}
                        onChange={setMultiSecCode}
                        options={[
                          { label: 'ARC - Architecture', value: 'ARC' },
                          { label: 'STR - Structure', value: 'STR' },
                          { label: 'MEP - M&E/Plumbing', value: 'MEP' },
                          { label: 'ELE - Electrical', value: 'ELE' },
                          { label: 'CIV - Civil', value: 'CIV' },
                          { label: 'LAN - Landscape', value: 'LAN' },
                        ]}
                      />
                      <Button
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        onClick={() => autoMapMutation.mutate()}
                        loading={autoMapMutation.isPending}
                        disabled={!multiDescription}
                        style={{ width: '100%' }}
                      >
                        Auto Map
                      </Button>
                    </Col>
                  </Row>

                  {multiResult && (
                    <Card size="small" style={{ marginTop: 16 }}>
                      <Descriptions bordered size="small" column={2}>
                        <Descriptions.Item label="Description" span={2}>
                          {multiResult.description}
                        </Descriptions.Item>
                        <Descriptions.Item label="SEC Code">
                          {multiResult.sec_code ? (
                            <Tag color="blue">{multiResult.sec_code}</Tag>
                          ) : (
                            '-'
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Work Code">
                          {multiResult.work_code ? (
                            <Text strong copyable>{multiResult.work_code}</Text>
                          ) : (
                            '-'
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Legal Code">
                          {multiResult.legal_code ? (
                            <Text strong copyable>{multiResult.legal_code}</Text>
                          ) : (
                            '-'
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="ISO Code">
                          {multiResult.iso_code ? (
                            <Text strong copyable>{multiResult.iso_code}</Text>
                          ) : (
                            '-'
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Confidence">
                          <Progress
                            percent={Math.round(multiResult.confidence * 100)}
                            size="small"
                            style={{ width: 150 }}
                          />
                        </Descriptions.Item>
                        <Descriptions.Item label="Source">
                          <Tag>{multiResult.mapping_source}</Tag>
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                  )}

                  <Card title="Multi-Code Search" size="small" style={{ marginTop: 24 }}>
                    <Space.Compact style={{ width: '100%' }}>
                      <Input
                        placeholder="Search across all code systems..."
                        value={multiSearchQuery}
                        onChange={(e) => setMultiSearchQuery(e.target.value)}
                        onPressEnter={() =>
                          multiSearchQuery && multiSearchMutation.mutate(multiSearchQuery)
                        }
                      />
                      <Button
                        type="primary"
                        icon={<SearchOutlined />}
                        onClick={() => multiSearchMutation.mutate(multiSearchQuery)}
                        loading={multiSearchMutation.isPending}
                      >
                        Search
                      </Button>
                    </Space.Compact>

                    {multiSearchMutation.data && (
                      <Table
                        style={{ marginTop: 16 }}
                        dataSource={multiSearchMutation.data.results}
                        rowKey={(r) => `${r.type}-${r.code}`}
                        size="small"
                        pagination={{ pageSize: 10 }}
                        columns={[
                          {
                            title: 'Type',
                            dataIndex: 'type',
                            key: 'type',
                            width: 80,
                            render: (t: string) => (
                              <Tag
                                color={
                                  t === 'sec'
                                    ? 'blue'
                                    : t === 'legal'
                                    ? 'green'
                                    : t === 'iso'
                                    ? 'purple'
                                    : 'orange'
                                }
                              >
                                {t.toUpperCase()}
                              </Tag>
                            ),
                          },
                          {
                            title: 'Code',
                            dataIndex: 'code',
                            key: 'code',
                            width: 150,
                            render: (code: string) => <Text strong copyable>{code}</Text>,
                          },
                          {
                            title: 'Description',
                            dataIndex: 'description',
                            key: 'description',
                            ellipsis: true,
                          },
                          {
                            title: 'Score',
                            dataIndex: 'score',
                            key: 'score',
                            width: 100,
                            render: (s: number) => (
                              <Progress
                                percent={Math.round(s * 100)}
                                size="small"
                                style={{ width: 80 }}
                              />
                            ),
                          },
                        ]}
                      />
                    )}
                  </Card>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}
