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
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { masterItemsService, MasterItem } from '@/services/masterItemsService'
import PriceDrillDown from '@/components/PriceDrillDown'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography
const { Search } = Input

export default function MasterItems() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [secCodeFilter, setSecCodeFilter] = useState<string | undefined>()
  const [verifiedOnly, setVerifiedOnly] = useState(false)
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 })

  // Price drill-down modal state
  const [priceDrillDownOpen, setPriceDrillDownOpen] = useState(false)
  const [selectedItem, setSelectedItem] = useState<MasterItem | null>(null)

  const handlePriceClick = (item: MasterItem) => {
    setSelectedItem(item)
    setPriceDrillDownOpen(true)
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
      pagination,
    ],
    queryFn: () =>
      masterItemsService.list({
        search,
        sec_code: secCodeFilter,
        verified_only: verifiedOnly,
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

  const handleDelete = (masterId: number) => {
    Modal.confirm({
      title: 'Delete Master Item',
      content: 'Are you sure you want to delete this master item?',
      onOk: () => deleteMutation.mutate(masterId),
    })
  }

  const columns: ColumnsType<MasterItem> = [
    {
      title: 'Work Code',
      dataIndex: 'work_code',
      key: 'work_code',
      width: 200,
      fixed: 'left',
      render: (code: string) => (
        <Text strong copyable>
          {code}
        </Text>
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
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
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
    </div>
  )
}
