import { useState } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Statistic,
  Table,
  Space,
  Spin,
  Alert,
  Tag,
} from 'antd'
import {
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  RiseOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Column, Pie, Line } from '@ant-design/plots'
import { analyticsService } from '@/services/analyticsService'
import { projectService, Project } from '@/services/projectService'

const { Option } = Select
const { RangePicker } = DatePicker

export default function Analytics() {
  const [selectedProject, setSelectedProject] = useState<number | undefined>(undefined)

  // Fetch projects
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: () => projectService.getProjects(),
  })

  // Fetch analytics data
  const { data: projectStats, isLoading: loadingStats } = useQuery({
    queryKey: ['projectStats', selectedProject],
    queryFn: () => selectedProject 
      ? analyticsService.getProjectStats(selectedProject)
      : Promise.resolve(null),
    enabled: !!selectedProject,
  })

  const { data: secDistribution, isLoading: loadingDistribution } = useQuery({
    queryKey: ['secDistribution', selectedProject],
    queryFn: () => analyticsService.getSECDistribution(selectedProject),
  })

  const { data: classificationAccuracy, isLoading: loadingAccuracy } = useQuery({
    queryKey: ['classificationAccuracy', selectedProject],
    queryFn: () => analyticsService.getClassificationAccuracy(selectedProject),
  })

  const isLoading = loadingStats || loadingDistribution || loadingAccuracy

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Loading analytics..." />
      </div>
    )
  }

  // Prepare chart data
  const distributionChartData = secDistribution?.slice(0, 10).map(item => ({
    sec_code: item.sec_code,
    count: item.count,
    percentage: item.percentage,
  })) || []

  const distributionPieData = secDistribution?.slice(0, 8).map(item => ({
    type: item.sec_code,
    value: item.count,
  })) || []

  const costBySecData = secDistribution?.slice(0, 10).map(item => ({
    sec_code: item.sec_code,
    cost: item.total_cost || 0,
  })) || []

  const accuracyByMethodData = classificationAccuracy?.by_method?.map(item => ({
    method: item.method.toUpperCase(),
    accuracy: (item.accuracy * 100).toFixed(1),
    count: item.count,
  })) || []

  // Column chart config for SEC distribution
  const distributionConfig = {
    data: distributionChartData,
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
        autoRotate: true,
      },
    },
    meta: {
      sec_code: {
        alias: 'SEC Code',
      },
      count: {
        alias: 'Number of Items',
      },
    },
  }

  // Pie chart config
  const pieConfig = {
    data: distributionPieData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer' as const,
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'element-active',
      },
    ],
  }

  // Cost analysis chart config
  const costConfig = {
    data: costBySecData,
    xField: 'sec_code',
    yField: 'cost',
    label: {
      position: 'top' as const,
      formatter: (datum: any) => `$${(datum.cost / 1000).toFixed(1)}K`,
    },
    meta: {
      cost: {
        alias: 'Total Cost ($)',
      },
    },
  }

  const distributionColumns = [
    {
      title: 'Rank',
      key: 'rank',
      render: (_: any, __: any, index: number) => index + 1,
      width: 60,
    },
    {
      title: 'SEC Code',
      dataIndex: 'sec_code',
      key: 'sec_code',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      render: (val: number) => <strong>{val}</strong>,
    },
    {
      title: 'Percentage',
      dataIndex: 'percentage',
      key: 'percentage',
      render: (val: number) => `${val.toFixed(1)}%`,
    },
    {
      title: 'Total Cost',
      dataIndex: 'total_cost',
      key: 'total_cost',
      render: (val: number) => val ? `$${val.toLocaleString()}` : '-',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Analytics & Reports</h1>
        <Space>
          <Select
            placeholder="Select Project"
            style={{ width: 250 }}
            value={selectedProject}
            onChange={setSelectedProject}
            allowClear
          >
            {projects?.map((project) => (
              <Option key={project.id} value={project.id}>
                {project.name}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      {/* Project Overview Stats */}
      {selectedProject && projectStats && (
        <Card title="Project Overview" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Total Files"
                value={projectStats.total_files}
                prefix={<BarChartOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Total Line Items"
                value={projectStats.total_line_items}
                prefix={<LineChartOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Verified Items"
                value={projectStats.verified_items}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Classification Accuracy"
                value={projectStats.classification_accuracy}
                suffix="%"
                precision={1}
                valueStyle={{ color: '#1890ff' }}
                prefix={<RiseOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Classification Accuracy */}
      {classificationAccuracy && (
        <Card title="Classification Accuracy" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="Total Classified"
                value={classificationAccuracy.total_classified}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Total Verified"
                value={classificationAccuracy.total_verified}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Accuracy Rate"
                value={classificationAccuracy.accuracy_rate * 100}
                suffix="%"
                precision={1}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
          </Row>
          
          {accuracyByMethodData.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <h4>Accuracy by Classification Method</h4>
              <Space size="large" style={{ marginTop: 16 }}>
                {accuracyByMethodData.map((item) => (
                  <Card key={item.method} size="small" style={{ minWidth: 150 }}>
                    <Statistic
                      title={item.method}
                      value={item.accuracy}
                      suffix="%"
                      valueStyle={{ fontSize: 20 }}
                    />
                    <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                      {item.count} items
                    </div>
                  </Card>
                ))}
              </Space>
            </div>
          )}
        </Card>
      )}

      {/* SEC Code Distribution Charts */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="SEC Code Distribution (Top 10)" extra={<PieChartOutlined />}>
            {distributionChartData.length > 0 ? (
              <Column {...distributionConfig} height={300} />
            ) : (
              <Alert message="No data available" type="info" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Distribution Breakdown" extra={<PieChartOutlined />}>
            {distributionPieData.length > 0 ? (
              <Pie {...pieConfig} height={300} />
            ) : (
              <Alert message="No data available" type="info" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Cost Analysis */}
      {costBySecData.length > 0 && costBySecData.some(d => d.cost > 0) && (
        <Card title="Cost Analysis by SEC Code (Top 10)" style={{ marginBottom: 16 }}>
          <Column {...costConfig} height={300} />
        </Card>
      )}

      {/* Distribution Table */}
      <Card title="Detailed SEC Code Distribution">
        <Table
          columns={distributionColumns}
          dataSource={secDistribution}
          rowKey="sec_code"
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>
    </div>
  )
}
