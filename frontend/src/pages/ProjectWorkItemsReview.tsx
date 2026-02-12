import { useState } from 'react'
import {
  Table,
  Button,
  Tag,
  Modal,
  Input,
  Space,
  Statistic,
  Card,
  Row,
  Col,
  message,
  Select,
  Tooltip,
  Breadcrumb,
  Typography,
  InputNumber,
} from 'antd'
import {
  CheckOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  LinkOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  projectWorkItemsService,
  ProjectWorkItem,
} from '@/services/projectWorkItemsService'
import { apiClient } from '@/services/api'

const { Text } = Typography
const { Search } = Input

interface MasterItem {
  master_id: number
  work_code: string
  description: string
  sec_code: string
}

export default function ProjectWorkItemsReview() {
  const [selectedItem, setSelectedItem] = useState<ProjectWorkItem | null>(null)
  const [resolveModalVisible, setResolveModalVisible] = useState(false)
  const [gateFilter, setGateFilter] = useState<string | undefined>(undefined)
  const [resolutionFilter, setResolutionFilter] = useState<string>('UNRESOLVED')
  const [masterSearch, setMasterSearch] = useState('')
  const [masterSearchResults, setMasterSearchResults] = useState<MasterItem[]>([])
  const [selectedMasterId, setSelectedMasterId] = useState<number | null>(null)
  const queryClient = useQueryClient()

  // Fetch project work items
  const { data: items, isLoading, refetch } = useQuery({
    queryKey: ['projectWorkItems', gateFilter, resolutionFilter],
    queryFn: () =>
      projectWorkItemsService.list({
        gate_status: gateFilter,
        resolution_status: resolutionFilter,
        limit: 200,
      }),
  })

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ['projectWorkItemsStats'],
    queryFn: () => projectWorkItemsService.getStats(),
  })

  // Resolve mutation
  const resolveMutation = useMutation({
    mutationFn: (data: { id: number; master_id: number }) =>
      projectWorkItemsService.resolve(data.id, {
        master_work_item_id: data.master_id,
        reviewer_id: 1,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projectWorkItems'] })
      queryClient.invalidateQueries({ queryKey: ['projectWorkItemsStats'] })
      message.success('Item resolved and synonym created!')
      setResolveModalVisible(false)
      setSelectedItem(null)
      setSelectedMasterId(null)
      setMasterSearch('')
      setMasterSearchResults([])
    },
    onError: (error: Error) => {
      message.error(`Failed to resolve: ${error.message}`)
    },
  })

  // Search master items
  const handleMasterSearch = async (value: string) => {
    setMasterSearch(value)
    if (value.length < 2) {
      setMasterSearchResults([])
      return
    }
    try {
      const res = await apiClient.get('/master-items', {
        params: { search: value, limit: 10 },
      })
      setMasterSearchResults(res.data.items || res.data || [])
    } catch {
      setMasterSearchResults([])
    }
  }

  // Parse WBS context
  const parseWbs = (wbsJson?: string) => {
    if (!wbsJson) return null
    try {
      return JSON.parse(wbsJson)
    } catch {
      return null
    }
  }

  // Parse AI structured output
  const parseStructured = (json?: string) => {
    if (!json) return null
    try {
      return JSON.parse(json)
    } catch {
      return null
    }
  }

  const gateColor = (status: string) => {
    switch (status) {
      case 'GREEN': return 'green'
      case 'YELLOW': return 'orange'
      case 'RED': return 'red'
      default: return 'default'
    }
  }

  const resolutionColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'green'
      case 'MATCHED': return 'blue'
      case 'MERGED': return 'cyan'
      case 'UNRESOLVED': return 'default'
      default: return 'default'
    }
  }

  const columns = [
    {
      title: 'Temp Code',
      dataIndex: 'temp_code',
      key: 'temp_code',
      width: 140,
      render: (code: string) => <Text code>{code}</Text>,
    },
    {
      title: 'Gate',
      dataIndex: 'gate_status',
      key: 'gate_status',
      width: 80,
      render: (status: string) => <Tag color={gateColor(status)}>{status}</Tag>,
    },
    {
      title: 'Score',
      dataIndex: 'quality_score',
      key: 'quality_score',
      width: 70,
      render: (score: number) => score?.toFixed(0),
    },
    {
      title: 'Description',
      dataIndex: 'original_description',
      key: 'original_description',
      ellipsis: true,
      render: (text: string, record: ProjectWorkItem) => {
        const wbs = parseWbs(record.wbs_context)
        return (
          <div>
            <div>{text}</div>
            {wbs?.section_path && (
              <Breadcrumb
                style={{ fontSize: 11, color: '#999', marginTop: 2 }}
                items={wbs.section_path.split(' > ').map((s: string) => ({ title: s }))}
              />
            )}
          </div>
        )
      },
    },
    {
      title: 'Resolution',
      dataIndex: 'resolution_status',
      key: 'resolution_status',
      width: 110,
      render: (status: string) => <Tag color={resolutionColor(status)}>{status}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: any, record: ProjectWorkItem) => (
        <Space>
          {record.resolution_status === 'UNRESOLVED' && (
            <Tooltip title="Resolve to Master Item">
              <Button
                type="primary"
                size="small"
                icon={<LinkOutlined />}
                onClick={() => {
                  setSelectedItem(record)
                  setResolveModalVisible(true)
                }}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <h2>Project Work Items Review</h2>

      {/* Stats cards */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={4}>
            <Card size="small">
              <Statistic title="Total" value={stats.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="Unresolved"
                value={stats.unresolved}
                valueStyle={{ color: stats.unresolved > 0 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="Approved" value={stats.approved} valueStyle={{ color: '#3f8600' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="RED" value={stats.by_gate_status?.RED || 0} valueStyle={{ color: '#cf1322' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="YELLOW" value={stats.by_gate_status?.YELLOW || 0} valueStyle={{ color: '#faad14' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic title="GREEN" value={stats.by_gate_status?.GREEN || 0} valueStyle={{ color: '#3f8600' }} />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Space style={{ marginBottom: 16 }}>
        <Select
          placeholder="Gate Status"
          allowClear
          style={{ width: 140 }}
          value={gateFilter}
          onChange={setGateFilter}
          options={[
            { label: 'All Gates', value: undefined },
            { label: 'RED', value: 'RED' },
            { label: 'YELLOW', value: 'YELLOW' },
            { label: 'GREEN', value: 'GREEN' },
          ]}
        />
        <Select
          placeholder="Resolution"
          allowClear
          style={{ width: 160 }}
          value={resolutionFilter}
          onChange={(v) => setResolutionFilter(v || 'UNRESOLVED')}
          options={[
            { label: 'Unresolved', value: 'UNRESOLVED' },
            { label: 'Matched', value: 'MATCHED' },
            { label: 'Approved', value: 'APPROVED' },
            { label: 'Merged', value: 'MERGED' },
          ]}
        />
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
          Refresh
        </Button>
      </Space>

      {/* Table */}
      <Table
        dataSource={items}
        columns={columns}
        rowKey="pwi_id"
        loading={isLoading}
        size="small"
        pagination={{ pageSize: 20 }}
        expandable={{
          expandedRowRender: (record: ProjectWorkItem) => {
            const structured = parseStructured(record.ai_structured_output)
            const wbs = parseWbs(record.wbs_context)
            return (
              <Row gutter={16}>
                <Col span={12}>
                  <Card title="Normalized" size="small">
                    <p>{record.normalized_description || 'N/A'}</p>
                  </Card>
                  {wbs && (
                    <Card title="WBS Context" size="small" style={{ marginTop: 8 }}>
                      <p><strong>Parent:</strong> {wbs.parent_title || 'N/A'}</p>
                      <p><strong>Path:</strong> {wbs.section_path || 'N/A'}</p>
                      <p><strong>Type:</strong> {wbs.section_type || 'N/A'}</p>
                      {wbs.neighbors?.length > 0 && (
                        <p><strong>Neighbors:</strong> {wbs.neighbors.join(', ')}</p>
                      )}
                    </Card>
                  )}
                </Col>
                <Col span={12}>
                  {structured && (
                    <Card title="AI Structured Output" size="small">
                      <p><strong>Group:</strong> {structured.group}</p>
                      <p><strong>Type:</strong> {structured.type}</p>
                      {structured.location && <p><strong>Location:</strong> {structured.location}</p>}
                      {structured.grade && <p><strong>Grade:</strong> {structured.grade}</p>}
                      {structured.material && <p><strong>Material:</strong> {structured.material}</p>}
                      {structured.dimension && <p><strong>Dimension:</strong> {structured.dimension}</p>}
                      <p><strong>Confidence:</strong> {(structured.confidence * 100).toFixed(0)}%</p>
                      {structured.ambiguous_fields?.length > 0 && (
                        <p>
                          <strong>Ambiguous:</strong>{' '}
                          {structured.ambiguous_fields.map((f: string) => (
                            <Tag key={f} color="orange">{f}</Tag>
                          ))}
                        </p>
                      )}
                    </Card>
                  )}
                </Col>
              </Row>
            )
          },
        }}
      />

      {/* Resolve Modal */}
      <Modal
        title={
          <span>
            <LinkOutlined /> Resolve Work Item
          </span>
        }
        open={resolveModalVisible}
        onCancel={() => {
          setResolveModalVisible(false)
          setSelectedItem(null)
          setSelectedMasterId(null)
          setMasterSearch('')
          setMasterSearchResults([])
        }}
        onOk={() => {
          if (!selectedItem || !selectedMasterId) {
            message.warning('Please select a master item')
            return
          }
          resolveMutation.mutate({ id: selectedItem.pwi_id, master_id: selectedMasterId })
        }}
        okText="Resolve"
        confirmLoading={resolveMutation.isPending}
        width={700}
      >
        {selectedItem && (
          <div>
            <Card size="small" style={{ marginBottom: 16 }}>
              <p><strong>Temp Code:</strong> {selectedItem.temp_code}</p>
              <p><strong>Original:</strong> {selectedItem.original_description}</p>
              <p><strong>Normalized:</strong> {selectedItem.normalized_description || 'N/A'}</p>
              <p>
                <strong>Gate:</strong>{' '}
                <Tag color={gateColor(selectedItem.gate_status)}>{selectedItem.gate_status}</Tag>
                <strong style={{ marginLeft: 16 }}>Score:</strong> {selectedItem.quality_score?.toFixed(0)}
              </p>
            </Card>

            <p><strong>Search Master Items:</strong></p>
            <Search
              placeholder="Search by description or work code..."
              value={masterSearch}
              onChange={(e) => handleMasterSearch(e.target.value)}
              style={{ marginBottom: 8 }}
            />

            {masterSearchResults.length > 0 && (
              <Table
                dataSource={masterSearchResults}
                rowKey="master_id"
                size="small"
                pagination={false}
                onRow={(record) => ({
                  onClick: () => setSelectedMasterId(record.master_id),
                  style: {
                    cursor: 'pointer',
                    background: selectedMasterId === record.master_id ? '#e6f7ff' : undefined,
                  },
                })}
                columns={[
                  { title: 'Code', dataIndex: 'work_code', width: 120 },
                  { title: 'Description', dataIndex: 'description', ellipsis: true },
                  { title: 'SEC', dataIndex: 'sec_code', width: 80 },
                  {
                    title: '',
                    width: 50,
                    render: (_: any, record: MasterItem) =>
                      selectedMasterId === record.master_id ? (
                        <CheckOutlined style={{ color: '#1890ff' }} />
                      ) : null,
                  },
                ]}
              />
            )}

            {selectedMasterId && (
              <p style={{ marginTop: 8, color: '#1890ff' }}>
                <CheckOutlined /> Selected master item: #{selectedMasterId}
              </p>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
