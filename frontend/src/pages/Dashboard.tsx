import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Spin, Alert } from 'antd'
import {
  ProjectOutlined,
  FileOutlined,
  UnorderedListOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  PercentageOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { analyticsService, DashboardStats } from '@/services/analyticsService'
import { Line, Pie } from '@ant-design/plots'

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: analyticsService.getDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Loading dashboard..." />
      </div>
    )
  }

  if (error) {
    return (
      <Alert
        message="Error Loading Dashboard"
        description="Failed to load dashboard data. Please try again later."
        type="error"
        showIcon
      />
    )
  }

  const activityColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colors: Record<string, string> = {
          upload: 'blue',
          classification: 'green',
          verification: 'purple',
          project: 'orange',
        }
        return <Tag color={colors[type] || 'default'}>{type}</Tag>
      },
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => new Date(timestamp).toLocaleString(),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Dashboard</h1>
      
      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Projects"
              value={stats?.total_projects || 0}
              prefix={<ProjectOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Files"
              value={stats?.total_files || 0}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Line Items"
              value={stats?.total_line_items || 0}
              prefix={<UnorderedListOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Classification Accuracy"
              value={stats?.classification_accuracy || 0}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#fa8c16' }}
              precision={1}
            />
          </Card>
        </Col>
      </Row>

      {/* Status Overview */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} md={12}>
          <Card title="Verification Status" bordered={false}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Verified Items"
                  value={stats?.verified_items || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Pending Review"
                  value={stats?.pending_items || 0}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Quick Stats" bordered={false}>
            <p>Total Items: <strong>{(stats?.verified_items || 0) + (stats?.pending_items || 0)}</strong></p>
            <p>Verification Rate: <strong>
              {stats?.total_line_items 
                ? ((stats.verified_items / stats.total_line_items) * 100).toFixed(1) 
                : 0}%
            </strong></p>
            <p>Avg Items per File: <strong>
              {stats?.total_files 
                ? (stats.total_line_items / stats.total_files).toFixed(0) 
                : 0}
            </strong></p>
          </Card>
        </Col>
      </Row>

      {/* Recent Activity */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title="Recent Activity" bordered={false}>
            <Table
              columns={activityColumns}
              dataSource={stats?.recent_activity || []}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
