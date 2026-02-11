import { useState } from 'react'
import {
  Card,
  Table,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Typography,
  Statistic,
  Row,
  Col,
  message,
  Modal,
  Tooltip,
  List,
  Form,
  Popconfirm,
  Empty,
  Badge,
  Progress,
} from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DatabaseOutlined,
  FileExcelOutlined,
  EditOutlined,
  DeleteOutlined,
  DollarOutlined,
  TagsOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { masterItemsService, MasterItem } from '@/services/masterItemsService'
import { synonymService, Synonym, SynonymCreate } from '@/services/synonymService'
import PriceDrillDown from '@/components/PriceDrillDown'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography
const { Search } = Input

export default function MasterItems() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [secCodeFilter, setSecCodeFilter] = useState<string | undefined>()
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [tableTypeFilter, setTableTypeFilter] = useState<string | undefined>()
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 })

  // Price drill-down modal state
  const [priceDrillDownOpen, setPriceDrillDownOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<MasterItem | null>(null)

  // Synonym modal state
  const [synonymModalOpen, setSynonymModalOpen] = useState(false)
  const [synonymItem, setSynonymItem] = useState<MasterItem | null>(null)
  const [synonymForm] = Form.useForm()

  const handlePriceClick = (item: MasterItem) => {
    setSelectedItem(item)
    setPriceDrillDownOpen(true)
  }

  const handleSynonymClick = (item: MasterItem) => {
    setSynonymItem(item)
    setSynonymModalOpen(true)
  }

  // Fetch master items
  const {
    data: items,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: [
      'masterItems',
      search,
      secCodeFilter,
      verifiedOnly,
      tableTypeFilter,
      pagination,
    ],
    queryFn: () =>
      masterItemsService.list({
        search,
        sec_code: secCodeFilter,
        verified_only: verifiedOnly,
        item_table_type: tableTypeFilter,
        skip: pagination.skip,
        limit: pagination.limit,
      }),
  })

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['masterStatistics'],
    queryFn: masterItemsService.getStatistics,
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: masterItemsService.delete,
    onSuccess: () => {
      message.success('Master item deleted successfully')
      queryClient.invalidateQueries({ queryKey: ['masterItems'] })
      queryClient.invalidateQueries({ queryKey: ['masterStatistics'] })
    },
    onError: () => {
      message.error('Failed to delete master item')
    },
  })

  // Export CSV mutation
  const exportMutation = useMutation({
    mutationFn: masterItemsService.exportCSV,
    onSuccess: (data) => {
      message.success(`CSV exported: ${data.filename}`)
    },
    onError: () => {
      message.error('Failed to export CSV')
    },
  })

  // Fetch synonyms for selected item
  const { data: synonyms, refetch: refetchSynonyms, isLoading: synonymsLoading } = useQuery({
    queryKey: ['synonyms', synonymItem?.master_id],
    queryFn: () => synonymService.getSynonyms(synonymItem!.master_id),
    enabled: !!synonymItem,
  })

  // Add synonym mutation
  const addSynonymMutation = useMutation({
    mutationFn: ({ masterId, data }: { masterId: number; data: SynonymCreate }) =>
      synonymService.addSynonym(masterId, data),
    onSuccess: () => {
      message.success('Synonym added successfully')
      refetchSynonyms()
      synonymForm.resetFields()
    },
    onError: () => {
      message.error('Failed to add synonym')
    },
  })

  // Delete synonym mutation
  const deleteSynonymMutation = useMutation({
    mutationFn: synonymService.deleteSynonym,
    onSuccess: () => {
      message.success('Synonym deleted successfully')
      refetchSynonyms()
    },
    onError: () => {
      message.error('Failed to delete synonym')
    },
  })

  const handleDelete = (masterId: number) => {
    Modal.confirm({
      title: 'Delete Master Item',
      content: 'Are you sure you want to delete this master item?',
      onOk: () => deleteMutation.mutate(masterId),
    })
  }

  const columns: ColumnsType<MasterItem> = [
    {
      title: 'Type',
      dataIndex: 'item_table_type',
      key: 'item_table_type',
      width: 60,
      fixed: 'left',
      align: 'center',
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          A: 'blue',
          M: 'green',
          L: 'orange',
          E: 'purple',
        }
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: 'Discipline',
      dataIndex: 'discipline',
      key: 'discipline',
      width: 80,
      align: 'center',
      render: (disc: string) => disc ? <Tag>{disc}</Tag> : null,
    },
    {
      title: 'Code',
      dataIndex: 'instance_code',
      key: 'instance_code',
      width: 220,
      fixed: 'left',
      render: (_: string, record: MasterItem) => (
        <Tooltip title={record.sec_code_v4 ? `Ref: ${record.sec_code_v4}` : record.work_code}>
          <Text strong copyable>
            {record.instance_code || record.sec_code_v4 || record.work_code}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      width: 300,
      ellipsis: true,
    },
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
      width: 120,
      render: (code: string) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: 'Unit',
      dataIndex: 'unit_standard',
      key: 'unit_standard',
      width: 80,
    },
    {
      title: 'Avg Price',
      dataIndex: 'ref_unit_price_avg',
      key: 'ref_unit_price_avg',
      width: 150,
      align: 'right',
      render: (price: number | null, record: MasterItem) =>
        price ? (
          <Tooltip title="Click to see price history">
            <Button
              type="link"
              style={{ padding: 0, height: 'auto' }}
              onClick={() => handlePriceClick(record)}
              icon={<DollarOutlined style={{ marginRight: 4 }} />}
            >
              {price.toLocaleString('vi-VN')} VND
            </Button>
          </Tooltip>
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: 'Occurrences',
      dataIndex: 'occurrence_count',
      key: 'occurrence_count',
      width: 120,
      align: 'center',
      render: (count: number) => <Tag color="green">{count}</Tag>,
    },
    {
      title: 'Spec Status',
      dataIndex: 'spec_status',
      key: 'spec_status',
      width: 110,
      align: 'center',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          draft: 'default',
          detailed: 'processing',
          final: 'success',
        }
        return <Badge status={colorMap[status] as any || 'default'} text={status || 'draft'} />
      },
    },
    {
      title: 'Spec %',
      dataIndex: 'spec_completeness',
      key: 'spec_completeness',
      width: 100,
      align: 'center',
      render: (val: number) => (
        <Progress
          percent={Math.round((val || 0) * 100)}
          size="small"
          status={val >= 0.75 ? 'success' : val >= 0.5 ? 'normal' : 'exception'}
        />
      ),
    },
    {
      title: 'Verified',
      dataIndex: 'is_verified',
      key: 'is_verified',
      width: 100,
      align: 'center',
      render: (verified: boolean) =>
        verified ? (
          <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
        ) : (
          <CloseCircleOutlined style={{ color: '#d9d9d9', fontSize: 20 }} />
        ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="Synonyms">
            <Button
              type="text"
              icon={<TagsOutlined />}
              onClick={() => handleSynonymClick(record)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => {
                // TODO: Open edit modal
                message.info('Edit functionality coming soon')
              }}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.master_id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Statistics Cards */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Items"
                value={stats.total_master_items}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Verified"
                value={stats.verified_items}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Unverified"
                value={stats.unverified_items}
                prefix={<CloseCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="SEC Categories"
                value={Object.keys(stats.by_sec_code).length}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Table Card */}
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            <Title level={4} style={{ margin: 0 }}>
              Master Work Items
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<FileExcelOutlined />}
              onClick={() => exportMutation.mutate()}
              loading={exportMutation.isPending}
            >
              Export CSV
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
              Refresh
            </Button>
          </Space>
        }
      >
        {/* Filters */}
        <Space style={{ marginBottom: 16, width: '100%' }} wrap>
          <Search
            placeholder="Search description..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearch}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Filter by SEC Code"
            allowClear
            style={{ width: 200 }}
            onChange={setSecCodeFilter}
            options={
              stats?.by_sec_code
                ? Object.keys(stats.by_sec_code).map((code) => ({
                    label: `${code} (${stats.by_sec_code[code]})`,
                    value: code,
                  }))
                : []
            }
          />
          <Select
            placeholder="Table Type"
            allowClear
            style={{ width: 160 }}
            onChange={setTableTypeFilter}
            options={[
              { label: 'A - Activity', value: 'A' },
              { label: 'M - Material', value: 'M' },
              { label: 'L - Labour', value: 'L' },
              { label: 'E - Equipment', value: 'E' },
            ]}
          />
          <Select
            placeholder="Verification Status"
            style={{ width: 200 }}
            value={verifiedOnly ? 'verified' : 'all'}
            onChange={(value) => setVerifiedOnly(value === 'verified')}
            options={[
              { label: 'All Items', value: 'all' },
              { label: 'Verified Only', value: 'verified' },
            ]}
          />
        </Space>

        {/* Table */}
        <Table
          columns={columns}
          dataSource={items}
          rowKey="master_id"
          loading={isLoading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: pagination.limit,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} items`,
            onChange: (page, pageSize) => {
              setPagination({
                skip: (page - 1) * pageSize,
                limit: pageSize,
              })
            },
          }}
        />
      </Card>

      {/* Price Drill-Down Modal */}
      {selectedItem && (
        <PriceDrillDown
          masterId={selectedItem.master_id}
          workCode={selectedItem.work_code}
          description={selectedItem.description}
          open={priceDrillDownOpen}
          onClose={() => {
            setPriceDrillDownOpen(false)
            setSelectedItem(null)
          }}
        />
      )}

      {/* Synonym Modal */}
      <Modal
        title={
          <Space>
            <TagsOutlined />
            <span>Manage Synonyms</span>
            {synonymItem && <Tag color="blue">{synonymItem.work_code}</Tag>}
          </Space>
        }
        open={synonymModalOpen}
        onCancel={() => {
          setSynonymModalOpen(false)
          setSynonymItem(null)
          synonymForm.resetFields()
        }}
        footer={null}
        width={700}
      >
        {synonymItem && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Text strong>{synonymItem.description}</Text>
            </Card>

            {/* Add Synonym Form */}
            <Form
              form={synonymForm}
              layout="inline"
              style={{ marginBottom: 16 }}
              onFinish={(values) => {
                addSynonymMutation.mutate({
                  masterId: synonymItem.master_id,
                  data: values as SynonymCreate,
                })
              }}
            >
              <Form.Item
                name="synonym_text"
                rules={[{ required: true, message: 'Required' }]}
                style={{ flex: 1 }}
              >
                <Input placeholder="Enter synonym text..." />
              </Form.Item>
              <Form.Item
                name="synonym_type"
                rules={[{ required: true, message: 'Required' }]}
              >
                <Select
                  placeholder="Type"
                  style={{ width: 140 }}
                  options={[
                    { label: 'Alias', value: 'alias' },
                    { label: 'Abbreviation', value: 'abbreviation' },
                    { label: 'Regional', value: 'regional' },
                    { label: 'English', value: 'english' },
                  ]}
                />
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<PlusOutlined />}
                  loading={addSynonymMutation.isPending}
                >
                  Add
                </Button>
              </Form.Item>
            </Form>

            {/* Synonyms List */}
            {synonymsLoading ? (
              <div style={{ textAlign: 'center', padding: 24 }}>Loading...</div>
            ) : synonyms && synonyms.length > 0 ? (
              <List
                dataSource={synonyms}
                renderItem={(syn: Synonym) => (
                  <List.Item
                    actions={[
                      <Popconfirm
                        key="delete"
                        title="Delete this synonym?"
                        onConfirm={() => deleteSynonymMutation.mutate(syn.synonym_id)}
                      >
                        <Button
                          type="text"
                          danger
                          icon={<DeleteOutlined />}
                          loading={deleteSynonymMutation.isPending}
                        />
                      </Popconfirm>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Text>{syn.synonym_text}</Text>
                          <Tag
                            color={
                              syn.synonym_type === 'alias'
                                ? 'blue'
                                : syn.synonym_type === 'abbreviation'
                                ? 'green'
                                : syn.synonym_type === 'regional'
                                ? 'orange'
                                : 'purple'
                            }
                          >
                            {syn.synonym_type}
                          </Tag>
                          {!syn.is_active && <Tag color="red">Inactive</Tag>}
                        </Space>
                      }
                      description={`Source: ${syn.source || 'manual'}`}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="No synonyms yet. Add one above!" />
            )}

            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Badge count={synonyms?.length || 0} style={{ backgroundColor: '#1890ff' }}>
                <Text type="secondary">Total Synonyms</Text>
              </Badge>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}
