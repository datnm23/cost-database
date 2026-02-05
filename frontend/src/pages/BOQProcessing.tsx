import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Statistic,
  Row,
  Col,
  message,
  Modal,
  Tabs,
  Select,
  Progress,
  Tooltip,
  Badge,
  Empty,
  Spin,
  Descriptions,
  List,
  Dropdown,
} from 'antd'
import {
  CloudUploadOutlined,
  CheckCircleOutlined,
  PlusCircleOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
  ReloadOutlined,
  EyeOutlined,
  DatabaseOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fileService } from '@/services/fileService'
import {
  boqProcessingService,
  MatchResult,
  ProcessingResult,
} from '@/services/boqProcessingService'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

export default function BOQProcessing() {
  const queryClient = useQueryClient()
  const [selectedFileId, setSelectedFileId] = useState<number | null>(null)
  const [processingMethod, setProcessingMethod] = useState<'3_tier' | 'ai_only'>('3_tier')
  const [processingResult, setProcessingResult] = useState<ProcessingResult | null>(null)
  const [activeTab, setActiveTab] = useState('matched')
  const [selectedNewItems, setSelectedNewItems] = useState<number[]>([])
  const [alternativesModal, setAlternativesModal] = useState<{
    open: boolean
    item: MatchResult | null
  }>({ open: false, item: null })

  // Fetch available files
  const { data: files, isLoading: filesLoading } = useQuery({
    queryKey: ['boqFiles'],
    queryFn: () => fileService.list({ status: 'mapped' }),
  })

  // Process BOQ mutation
  const processMutation = useMutation({
    mutationFn: (fileId: number) =>
      boqProcessingService.processBoq(fileId, {
        min_similarity: 0.7,
        use_semantic: true,
        processing_method: processingMethod,
      }),
    onSuccess: (data) => {
      setProcessingResult(data)
      message.success(`Processed ${data.total_items} items successfully`)
    },
    onError: () => {
      message.error('Failed to process BOQ file')
    },
  })

  // Add new items mutation
  const addNewMutation = useMutation({
    mutationFn: ({ fileId, itemIds }: { fileId: number; itemIds: number[] }) =>
      boqProcessingService.addNewItems(fileId, itemIds),
    onSuccess: (data) => {
      message.success(`Added ${data.added} items to master database`)
      setSelectedNewItems([])
      queryClient.invalidateQueries({ queryKey: ['masterItems'] })
    },
    onError: () => {
      message.error('Failed to add items to master')
    },
  })

  // Download mutations
  const downloadMutation = useMutation({
    mutationFn: (fileId: number) => boqProcessingService.downloadResults(fileId),
    onSuccess: () => {
      message.success('File downloaded successfully')
    },
    onError: () => {
      message.error('Failed to download file')
    },
  })

  const downloadOriginalMutation = useMutation({
    mutationFn: (fileId: number) => boqProcessingService.downloadWithOriginalFormat(fileId),
    onSuccess: () => {
      message.success('File downloaded successfully')
    },
    onError: () => {
      message.error('Failed to download file')
    },
  })

  const handleProcess = () => {
    if (selectedFileId) {
      processMutation.mutate(selectedFileId)
    }
  }

  const handleAddSelected = () => {
    if (selectedFileId && selectedNewItems.length > 0) {
      addNewMutation.mutate({ fileId: selectedFileId, itemIds: selectedNewItems })
    }
  }

  const handleAddAll = () => {
    if (selectedFileId && processingResult) {
      const allNewIds = processingResult.results
        .filter((r) => r.match_status === 'new')
        .map((r) => r.line_item_id)
      addNewMutation.mutate({ fileId: selectedFileId, itemIds: allNewIds })
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'matched':
        return 'success'
      case 'new':
        return 'processing'
      case 'review_needed':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getMatchTypeColor = (type: string) => {
    switch (type) {
      case 'exact':
        return 'green'
      case 'fuzzy':
        return 'blue'
      case 'semantic':
        return 'purple'
      case 'keyword':
        return 'orange'
      default:
        return 'default'
    }
  }

  const matchedColumns: ColumnsType<MatchResult> = [
    {
      title: 'Original Description',
      dataIndex: 'original_description',
      key: 'original_description',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Matched Work Code',
      dataIndex: 'matched_work_code',
      key: 'matched_work_code',
      width: 180,
      render: (code: string) => <Text strong copyable>{code}</Text>,
    },
    {
      title: 'Matched Description',
      dataIndex: 'matched_description',
      key: 'matched_description',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Score',
      dataIndex: 'similarity_score',
      key: 'similarity_score',
      width: 100,
      align: 'center',
      render: (score: number) => (
        <Progress
          type="circle"
          size={40}
          percent={Math.round(score * 100)}
          format={(p) => `${p}%`}
          strokeColor={score >= 0.9 ? '#52c41a' : score >= 0.7 ? '#1890ff' : '#faad14'}
        />
      ),
    },
    {
      title: 'Match Type',
      dataIndex: 'match_type',
      key: 'match_type',
      width: 100,
      render: (type: string) => <Tag color={getMatchTypeColor(type)}>{type}</Tag>,
    },
    {
      title: 'Tier',
      dataIndex: 'tier_used',
      key: 'tier_used',
      width: 80,
      render: (tier: string) => <Tag>{tier}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Tooltip title="View Alternatives">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => setAlternativesModal({ open: true, item: record })}
            disabled={!record.alternatives?.length}
          />
        </Tooltip>
      ),
    },
  ]

  const newItemsColumns: ColumnsType<MatchResult> = [
    {
      title: 'Description',
      dataIndex: 'original_description',
      key: 'original_description',
      width: 400,
      ellipsis: true,
    },
    {
      title: 'Normalized',
      dataIndex: 'normalized_description',
      key: 'normalized_description',
      width: 400,
      ellipsis: true,
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (conf: number) => (
        <Progress percent={Math.round((conf || 0) * 100)} size="small" />
      ),
    },
  ]

  const reviewColumns: ColumnsType<MatchResult> = [
    {
      title: 'Original Description',
      dataIndex: 'original_description',
      key: 'original_description',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Best Match',
      dataIndex: 'matched_description',
      key: 'matched_description',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'Score',
      dataIndex: 'similarity_score',
      key: 'similarity_score',
      width: 100,
      render: (score: number) => (
        <Progress
          type="circle"
          size={40}
          percent={Math.round((score || 0) * 100)}
          format={(p) => `${p}%`}
          strokeColor="#faad14"
        />
      ),
    },
    {
      title: 'Alternatives',
      dataIndex: 'alternatives',
      key: 'alternatives',
      width: 100,
      render: (alts: MatchResult['alternatives']) => (
        <Badge count={alts?.length || 0} showZero />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="View Alternatives">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => setAlternativesModal({ open: true, item: record })}
            />
          </Tooltip>
          <Tooltip title="Add as New">
            <Button
              type="text"
              icon={<PlusCircleOutlined />}
              onClick={() => {
                if (selectedFileId) {
                  addNewMutation.mutate({
                    fileId: selectedFileId,
                    itemIds: [record.line_item_id],
                  })
                }
              }}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  const filteredResults = processingResult?.results.filter((r) => {
    switch (activeTab) {
      case 'matched':
        return r.match_status === 'matched'
      case 'new':
        return r.match_status === 'new'
      case 'review':
        return r.match_status === 'review_needed'
      default:
        return true
    }
  })

  const matchedCount = processingResult?.results.filter(
    (r) => r.match_status === 'matched'
  ).length || 0
  const newCount = processingResult?.results.filter(
    (r) => r.match_status === 'new'
  ).length || 0
  const reviewCount = processingResult?.results.filter(
    (r) => r.match_status === 'review_needed'
  ).length || 0

  return (
    <div>
      <Title level={3}>
        <DatabaseOutlined /> BOQ Processing
      </Title>
      <Text type="secondary">
        Process BOQ files with hybrid matching to find existing master items or identify new ones
      </Text>

      {/* File Selection */}
      <Card style={{ marginTop: 24 }}>
        <Space size="large" align="center">
          <Select
            placeholder="Select a BOQ file to process"
            style={{ width: 400 }}
            loading={filesLoading}
            value={selectedFileId}
            onChange={setSelectedFileId}
            options={files?.map((f: { id: number; original_filename: string; row_count: number }) => ({
              label: `${f.original_filename} (${f.row_count} rows)`,
              value: f.id,
            }))}
            showSearch
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
          />
          <Select
            style={{ width: 180 }}
            value={processingMethod}
            onChange={setProcessingMethod}
            options={[
              { label: '3-Tier Hybrid', value: '3_tier' },
              { label: '100% AI', value: 'ai_only' },
            ]}
          />
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            onClick={handleProcess}
            loading={processMutation.isPending}
            disabled={!selectedFileId}
          >
            Process BOQ
          </Button>
          {processingResult && (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'processing',
                    label: 'Processing Results',
                    icon: <FileExcelOutlined />,
                    onClick: () => selectedFileId && downloadMutation.mutate(selectedFileId),
                  },
                  {
                    key: 'original',
                    label: 'With Original Format',
                    icon: <FileExcelOutlined />,
                    onClick: () => selectedFileId && downloadOriginalMutation.mutate(selectedFileId),
                  },
                ],
              }}
            >
              <Button
                icon={<DownloadOutlined />}
                loading={downloadMutation.isPending || downloadOriginalMutation.isPending}
              >
                Download Results
              </Button>
            </Dropdown>
          )}
        </Space>
      </Card>

      {/* Processing Progress */}
      {processMutation.isPending && (
        <Card style={{ marginTop: 24 }}>
          <Spin tip="Processing BOQ file..." size="large">
            <div style={{ padding: 50, textAlign: 'center' }}>
              <Text>Analyzing descriptions and matching against master database...</Text>
            </div>
          </Spin>
        </Card>
      )}

      {/* Results */}
      {processingResult && !processMutation.isPending && (
        <>
          {/* Summary Stats */}
          <Row gutter={16} style={{ marginTop: 24 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Total Items"
                  value={processingResult.total_items}
                  prefix={<DatabaseOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Matched"
                  value={matchedCount}
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<CheckCircleOutlined />}
                  suffix={
                    <Text type="secondary" style={{ fontSize: 14 }}>
                      ({Math.round((matchedCount / processingResult.total_items) * 100)}%)
                    </Text>
                  }
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="New Items"
                  value={newCount}
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<PlusCircleOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Review Needed"
                  value={reviewCount}
                  valueStyle={{ color: '#faad14' }}
                  prefix={<ExclamationCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* Results Tabs */}
          <Card style={{ marginTop: 24 }}>
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              items={[
                {
                  key: 'matched',
                  label: (
                    <span>
                      <CheckCircleOutlined />
                      Matched ({matchedCount})
                    </span>
                  ),
                  children: (
                    <Table
                      columns={matchedColumns}
                      dataSource={filteredResults}
                      rowKey="line_item_id"
                      scroll={{ x: 1200 }}
                      pagination={{ pageSize: 20 }}
                    />
                  ),
                },
                {
                  key: 'new',
                  label: (
                    <span>
                      <PlusCircleOutlined />
                      New Items ({newCount})
                    </span>
                  ),
                  children: (
                    <>
                      <Space style={{ marginBottom: 16 }}>
                        <Button
                          type="primary"
                          icon={<PlusCircleOutlined />}
                          onClick={handleAddSelected}
                          disabled={selectedNewItems.length === 0}
                          loading={addNewMutation.isPending}
                        >
                          Add Selected ({selectedNewItems.length})
                        </Button>
                        <Button
                          onClick={handleAddAll}
                          disabled={newCount === 0}
                          loading={addNewMutation.isPending}
                        >
                          Add All New Items
                        </Button>
                      </Space>
                      <Table
                        columns={newItemsColumns}
                        dataSource={filteredResults}
                        rowKey="line_item_id"
                        rowSelection={{
                          selectedRowKeys: selectedNewItems,
                          onChange: (keys) => setSelectedNewItems(keys as number[]),
                        }}
                        scroll={{ x: 1000 }}
                        pagination={{ pageSize: 20 }}
                      />
                    </>
                  ),
                },
                {
                  key: 'review',
                  label: (
                    <span>
                      <ExclamationCircleOutlined />
                      Review Needed ({reviewCount})
                    </span>
                  ),
                  children: (
                    <Table
                      columns={reviewColumns}
                      dataSource={filteredResults}
                      rowKey="line_item_id"
                      scroll={{ x: 1000 }}
                      pagination={{ pageSize: 20 }}
                    />
                  ),
                },
              ]}
            />
          </Card>
        </>
      )}

      {/* Empty State */}
      {!processingResult && !processMutation.isPending && (
        <Card style={{ marginTop: 24 }}>
          <Empty
            description={
              <span>
                Select a BOQ file and click "Process BOQ" to start matching
              </span>
            }
          >
            <Button type="primary" disabled={!selectedFileId} onClick={handleProcess}>
              Start Processing
            </Button>
          </Empty>
        </Card>
      )}

      {/* Alternatives Modal */}
      <Modal
        title="Match Alternatives"
        open={alternativesModal.open}
        onCancel={() => setAlternativesModal({ open: false, item: null })}
        footer={null}
        width={800}
      >
        {alternativesModal.item && (
          <>
            <Descriptions bordered size="small" column={1} style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Original Description">
                {alternativesModal.item.original_description}
              </Descriptions.Item>
              <Descriptions.Item label="Normalized">
                {alternativesModal.item.normalized_description}
              </Descriptions.Item>
            </Descriptions>

            <Title level={5}>Alternative Matches</Title>
            <List
              dataSource={alternativesModal.item.alternatives || []}
              renderItem={(alt) => (
                <List.Item
                  actions={[
                    <Button key="select" type="link">
                      Select This Match
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong copyable>{alt.work_code}</Text>
                        <Tag color={alt.score >= 0.8 ? 'green' : 'orange'}>
                          {Math.round(alt.score * 100)}%
                        </Tag>
                      </Space>
                    }
                    description={alt.description}
                  />
                </List.Item>
              )}
              locale={{ emptyText: 'No alternatives found' }}
            />
          </>
        )}
      </Modal>
    </div>
  )
}
