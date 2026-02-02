import { Card, Row, Col, Statistic, Typography, Spin, Alert, Space, Tag } from 'antd'
import {
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  TagsOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { masterItemsService } from '@/services/masterItemsService'
import { Pie, Column } from '@ant-design/plots'

const { Title, Text } = Typography

export default function MasterStatistics() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['masterStatistics'],
    queryFn: masterItemsService.getStatistics,
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" tip="Loading statistics..." />
      </div>
    )
  }

  if (error) {
    return (
      <Alert
        message="Error Loading Statistics"
        description="Failed to load master database statistics."
        type="error"
        showIcon
      />
    )
  }

  if (!stats) return null

  // Prepare chart data
  const secCodeData = Object.entries(stats.by_sec_code).map(([code, count]) => ({
    sec_code: code,
    count,
  }))

  const materialGradeData = stats.by_material_grade
    ? Object.entries(stats.by_material_grade).map(([grade, count]) => ({
        grade,
        count,
      }))
    : []

  const pieConfig = {
    data: secCodeData,
    angleField: 'count',
    colorField: 'sec_code',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} ({percentage})',
    },
    interactions: [
      {
        type: 'element-active',
      },
    ],
  }

  const columnConfig = {
    data: secCodeData,
    xField: 'sec_code',
    yField: 'count',
    label: {
      position: 'top' as const,
      style: {
        fill: '#000000',
        opacity: 0.6,
      },
    },
    xAxis: {
      label: {
        autoHide: true,
        autoRotate: false,
      },
    },
    meta: {
      sec_code: {
        alias: 'SEC Code',
      },
      count: {
        alias: 'Count',
      },
    },
  }

  const materialGradeColumnConfig = {
    data: materialGradeData,
    xField: 'grade',
    yField: 'count',
    label: {
      position: 'top' as const,
      style: {
        fill: '#000000',
        opacity: 0.6,
      },
    },
    color: '#FF6B6B',
    meta: {
      grade: {
        alias: 'Material Grade',
      },
      count: {
        alias: 'Count',
      },
    },
  }

  const verificationRate =
    stats.total_master_items > 0
      ? ((stats.verified_items / stats.total_master_items) * 100).toFixed(1)
      : 0

  return (
    <div>
      <Title level={3}>
        <DatabaseOutlined /> Master Database Statistics
      </Title>

      {/* Summary Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Master Items"
              value={stats.total_master_items}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Verified Items"
              value={stats.verified_items}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={
                <Text type="secondary" style={{ fontSize: 14 }}>
                  / {stats.total_master_items}
                </Text>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Unverified Items"
              value={stats.unverified_items}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Verification Rate"
              value={Number(verificationRate)}
              prefix={<BarChartOutlined />}
              suffix="%"
              valueStyle={{
                color: Number(verificationRate) > 50 ? '#52c41a' : '#faad14',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Distribution by SEC Code */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <TagsOutlined />
                <Text>Distribution by SEC Code (Pie Chart)</Text>
              </Space>
            }
          >
            <Pie {...pieConfig} />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <BarChartOutlined />
                <Text>Distribution by SEC Code (Bar Chart)</Text>
              </Space>
            }
          >
            <Column {...columnConfig} />
          </Card>
        </Col>
      </Row>

      {/* SEC Code Details */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="SEC Code Breakdown">
            <Space wrap size={[8, 16]}>
              {Object.entries(stats.by_sec_code)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(([code, count]) => (
                  <Tag
                    key={code}
                    color="blue"
                    style={{ padding: '8px 16px', fontSize: 14 }}
                  >
                    {code}: {count} items
                  </Tag>
                ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Material Grades */}
      {materialGradeData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={16}>
            <Card title="Distribution by Material Grade">
              <Column {...materialGradeColumnConfig} />
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card title="Material Grade Summary">
              <Space direction="vertical" style={{ width: '100%' }}>
                {materialGradeData
                  .sort((a, b) => b.count - a.count)
                  .map(({ grade, count }) => (
                    <div
                      key={grade}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: 8,
                        borderBottom: '1px solid #f0f0f0',
                      }}
                    >
                      <Tag color="orange" style={{ fontSize: 14 }}>
                        {grade}
                      </Tag>
                      <Text strong>{count} items</Text>
                    </div>
                  ))}
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {/* Summary Info */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="Summary">
            <Space direction="vertical" size="middle">
              <Text>
                <strong>Total Categories:</strong>{' '}
                {Object.keys(stats.by_sec_code).length} SEC codes
              </Text>
              {materialGradeData.length > 0 && (
                <Text>
                  <strong>Material Grades:</strong> {materialGradeData.length}{' '}
                  different grades detected
                </Text>
              )}
              <Text>
                <strong>Coverage:</strong> All major SEC categories (00-05) are
                represented
              </Text>
              <Text type="secondary">
                Last updated: {new Date().toLocaleString('vi-VN')}
              </Text>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
