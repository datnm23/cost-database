import { useState } from 'react'
import {
  Modal,
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Select,
  DatePicker,
  Spin,
  Empty,
  Typography,
  Space,
  Tag,
} from 'antd'
import {
  DollarOutlined,
  BarChartOutlined,
  ProjectOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  masterItemsService,
  PriceHistoryResponse,
  PriceChartData,
} from '@/services/masterItemsService'

const { Text, Title } = Typography
const { RangePicker } = DatePicker

interface PriceDrillDownProps {
  masterId: number
  workCode: string
  description: string
  open: boolean
  onClose: () => void
}

export default function PriceDrillDown({
  masterId,
  workCode,
  description,
  open,
  onClose,
}: PriceDrillDownProps) {
  const [region, setRegion] = useState<string | undefined>()
  const [projectType, setProjectType] = useState<string | undefined>()

  // Fetch price history
  const { data: priceHistory, isLoading } = useQuery({
    queryKey: ['priceHistory', masterId, region, projectType],
    queryFn: () =>
      masterItemsService.getPriceHistory(masterId, {
        region,
        project_type: projectType,
        limit: 100,
      }),
    enabled: open && masterId > 0,
  })

  // Fetch chart data
  const { data: chartData } = useQuery({
    queryKey: ['priceChartData', masterId],
    queryFn: () => masterItemsService.getPriceChartData(masterId, 10),
    enabled: open && masterId > 0,
  })

  // Fetch available regions
  const { data: regionsData } = useQuery({
    queryKey: ['priceHistoryRegions', masterId],
    queryFn: () => masterItemsService.getPriceHistoryRegions(masterId),
    enabled: open && masterId > 0,
  })

  const columns = [
    {
      title: 'Project',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 200,
      ellipsis: true,
      render: (name: string, record: any) => (
        <Space direction="vertical" size="small">
          <Text strong>{name}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>
            {record.project_code}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Unit Price',
      dataIndex: 'unit_price',
      key: 'unit_price',
      width: 150,
      align: 'right' as const,
      render: (price: number) => (
        <Text strong>{price?.toLocaleString('vi-VN')} VND</Text>
      ),
    },
    {
      title: 'Quantity',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 100,
      align: 'right' as const,
      render: (qty: number) => qty?.toLocaleString() || '-',
    },
    {
      title: 'Region',
      dataIndex: 'region',
      key: 'region',
      width: 120,
      render: (region: string) =>
        region ? <Tag>{region}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: 'Type',
      dataIndex: 'project_type',
      key: 'project_type',
      width: 120,
      render: (type: string) => {
        const colors: Record<string, string> = {
          residential: 'blue',
          commercial: 'green',
          industrial: 'orange',
          infrastructure: 'purple',
        }
        return type ? (
          <Tag color={colors[type] || 'default'}>{type}</Tag>
        ) : (
          '-'
        )
      },
    },
    {
      title: 'Recorded',
      dataIndex: 'recorded_at',
      key: 'recorded_at',
      width: 120,
      render: (date: string) =>
        date ? new Date(date).toLocaleDateString('vi-VN') : '-',
    },
  ]

  // Simple histogram visualization
  const renderHistogram = () => {
    if (!chartData || !chartData.buckets || chartData.buckets.length === 0) {
      return <Empty description="No chart data available" />
    }

    const maxCount = Math.max(...chartData.buckets.map((b) => b.count))

    return (
      <div style={{ padding: '16px 0' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            height: 120,
            gap: 2,
          }}
        >
          {chartData.buckets.map((bucket, idx) => (
            <div
              key={idx}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              <div
                style={{
                  width: '100%',
                  height: maxCount > 0 ? (bucket.count / maxCount) * 100 : 0,
                  backgroundColor: '#1890ff',
                  borderRadius: '4px 4px 0 0',
                  minHeight: bucket.count > 0 ? 4 : 0,
                }}
                title={`${bucket.range_start.toLocaleString()} - ${bucket.range_end.toLocaleString()}: ${bucket.count} records`}
              />
            </div>
          ))}
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: 4,
            fontSize: 11,
            color: '#888',
          }}
        >
          <span>{chartData.min_price?.toLocaleString()}</span>
          <span>{chartData.max_price?.toLocaleString()}</span>
        </div>
        <div style={{ textAlign: 'center', marginTop: 4, fontSize: 11, color: '#888' }}>
          Price Range (VND)
        </div>
      </div>
    )
  }

  return (
    <Modal
      title={
        <Space>
          <DollarOutlined />
          <span>Price Drill-Down</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={1000}
    >
      {/* Header */}
      <div style={{ marginBottom: 16 }}>
        <Title level={5} style={{ marginBottom: 4 }}>
          {workCode}
        </Title>
        <Text type="secondary">{description}</Text>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
        </div>
      ) : !priceHistory || priceHistory.total_records === 0 ? (
        <Empty description="No price history available for this item" />
      ) : (
        <>
          {/* Statistics Cards */}
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="Average Price"
                  value={priceHistory.distribution.avg}
                  suffix="VND"
                  valueStyle={{ color: '#1890ff' }}
                  formatter={(value) => value?.toLocaleString()}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="Min Price"
                  value={priceHistory.distribution.min}
                  suffix="VND"
                  valueStyle={{ color: '#52c41a' }}
                  formatter={(value) => value?.toLocaleString()}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="Max Price"
                  value={priceHistory.distribution.max}
                  suffix="VND"
                  valueStyle={{ color: '#faad14' }}
                  formatter={(value) => value?.toLocaleString()}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <Statistic
                  title="Data Points"
                  value={priceHistory.distribution.count}
                  prefix={<ProjectOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* Histogram */}
          <Card
            size="small"
            title={
              <Space>
                <BarChartOutlined />
                <span>Price Distribution</span>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {renderHistogram()}
            <Row gutter={16} style={{ marginTop: 8 }}>
              <Col span={8}>
                <Text type="secondary">Median: </Text>
                <Text strong>
                  {priceHistory.distribution.median?.toLocaleString()} VND
                </Text>
              </Col>
              {priceHistory.distribution.p25 && (
                <Col span={8}>
                  <Text type="secondary">25th Percentile: </Text>
                  <Text>
                    {priceHistory.distribution.p25?.toLocaleString()} VND
                  </Text>
                </Col>
              )}
              {priceHistory.distribution.p75 && (
                <Col span={8}>
                  <Text type="secondary">75th Percentile: </Text>
                  <Text>
                    {priceHistory.distribution.p75?.toLocaleString()} VND
                  </Text>
                </Col>
              )}
            </Row>
          </Card>

          {/* Filters */}
          <Space style={{ marginBottom: 16 }}>
            <Select
              placeholder="Filter by Region"
              allowClear
              style={{ width: 200 }}
              onChange={setRegion}
              options={regionsData?.regions?.map((r) => ({
                label: r,
                value: r,
              }))}
            />
            <Select
              placeholder="Filter by Project Type"
              allowClear
              style={{ width: 200 }}
              onChange={setProjectType}
              options={[
                { label: 'Residential', value: 'residential' },
                { label: 'Commercial', value: 'commercial' },
                { label: 'Industrial', value: 'industrial' },
                { label: 'Infrastructure', value: 'infrastructure' },
              ]}
            />
          </Space>

          {/* Source Projects Table */}
          <Card
            size="small"
            title={
              <Space>
                <ProjectOutlined />
                <span>Source Projects ({priceHistory.total_records})</span>
              </Space>
            }
          >
            <Table
              columns={columns}
              dataSource={priceHistory.source_projects}
              rowKey={(record) =>
                `${record.project_id}-${record.recorded_at}`
              }
              size="small"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} records`,
              }}
              scroll={{ x: 800 }}
            />
          </Card>
        </>
      )}
    </Modal>
  )
}
