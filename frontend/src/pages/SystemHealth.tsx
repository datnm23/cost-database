import { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Tag,
  Typography,
  Statistic,
  Row,
  Col,
  message,
  Descriptions,
  Progress,
  Alert,
  Spin,
  Divider,
} from 'antd'
import {
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  CloudServerOutlined,
  ClearOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { systemService, MatcherHealth, MatcherStats } from '@/services/systemService'

const { Title, Text } = Typography

export default function SystemHealth() {
  const queryClient = useQueryClient()
  const [rebuilding, setRebuilding] = useState(false)

  // Fetch matcher health
  const {
    data: health,
    isLoading: healthLoading,
    refetch: refetchHealth,
    error: healthError,
  } = useQuery({
    queryKey: ['matcherHealth'],
    queryFn: systemService.getMatcherHealth,
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Fetch matcher stats
  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useQuery({
    queryKey: ['matcherStats'],
    queryFn: systemService.getMatcherStats,
    refetchInterval: 30000,
  })

  // Rebuild mutation
  const rebuildMutation = useMutation({
    mutationFn: systemService.rebuildMatcher,
    onMutate: () => setRebuilding(true),
    onSuccess: (data) => {
      message.success(
        `Index rebuilt in ${data.duration_ms}ms. Indexed ${data.vectors_indexed} vectors.`
      )
      queryClient.invalidateQueries({ queryKey: ['matcherHealth'] })
      queryClient.invalidateQueries({ queryKey: ['matcherStats'] })
    },
    onError: () => {
      message.error('Failed to rebuild matcher index')
    },
    onSettled: () => setRebuilding(false),
  })

  // Clear cache mutation
  const clearCacheMutation = useMutation({
    mutationFn: systemService.clearCache,
    onSuccess: (data) => {
      message.success(`Cache cleared: ${data.cleared} entries removed`)
      queryClient.invalidateQueries({ queryKey: ['matcherHealth'] })
      queryClient.invalidateQueries({ queryKey: ['matcherStats'] })
    },
    onError: () => {
      message.error('Failed to clear cache')
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'up':
      case 'ready':
      case 'enabled':
      case 'connected':
        return 'success'
      case 'degraded':
        return 'warning'
      case 'unhealthy':
      case 'down':
      case 'not_ready':
      case 'disabled':
      case 'disconnected':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'up':
      case 'ready':
      case 'enabled':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'degraded':
        return <WarningOutlined style={{ color: '#faad14' }} />
      case 'unhealthy':
      case 'down':
      case 'not_ready':
      case 'disabled':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return null
    }
  }

  const handleRefresh = () => {
    refetchHealth()
    refetchStats()
  }

  if (healthError) {
    return (
      <div>
        <Title level={3}>
          <CloudServerOutlined /> System Health
        </Title>
        <Alert
          type="error"
          message="Failed to load system health"
          description="The system health endpoint may not be available. Please check the backend service."
          action={
            <Button onClick={handleRefresh}>Retry</Button>
          }
        />
      </div>
    )
  }

  return (
    <div>
      <Title level={3}>
        <CloudServerOutlined /> System Health
      </Title>
      <Text type="secondary">
        Monitor matcher service health and performance
      </Text>

      {/* Action Buttons */}
      <Space style={{ marginTop: 16, marginBottom: 24 }}>
        <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
          Refresh
        </Button>
        <Button
          icon={<SyncOutlined spin={rebuilding} />}
          onClick={() => rebuildMutation.mutate()}
          loading={rebuildMutation.isPending}
          type="primary"
        >
          Rebuild Index
        </Button>
        <Button
          icon={<ClearOutlined />}
          onClick={() => clearCacheMutation.mutate()}
          loading={clearCacheMutation.isPending}
          danger
        >
          Clear Cache
        </Button>
      </Space>

      <Spin spinning={healthLoading || statsLoading}>
        {/* Health Status Cards */}
        <Row gutter={[16, 16]}>
          {/* Overall Status */}
          <Col xs={24} md={12} lg={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">Overall Status</Text>
                <Space>
                  {health && getStatusIcon(health.status)}
                  <Text strong style={{ fontSize: 20, textTransform: 'capitalize' }}>
                    {health?.status || 'Unknown'}
                  </Text>
                </Space>
                <Tag color={getStatusColor(health?.status || '')}>
                  {health?.matcher_type || 'Hybrid Matcher'}
                </Tag>
              </Space>
            </Card>
          </Col>

          {/* Embedding Service */}
          <Col xs={24} md={12} lg={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">Embedding Service</Text>
                <Space>
                  {health?.embedding_service && getStatusIcon(health.embedding_service.status)}
                  <Text strong style={{ fontSize: 20, textTransform: 'capitalize' }}>
                    {health?.embedding_service?.status || 'Unknown'}
                  </Text>
                </Space>
                {health?.embedding_service && (
                  <>
                    <Text type="secondary">Model: {health.embedding_service.model}</Text>
                    {health.embedding_service.latency_ms && (
                      <Text type="secondary">
                        Latency: {health.embedding_service.latency_ms}ms
                      </Text>
                    )}
                  </>
                )}
              </Space>
            </Card>
          </Col>

          {/* FAISS Index */}
          <Col xs={24} md={12} lg={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">FAISS Index</Text>
                <Space>
                  {health?.faiss_index && getStatusIcon(health.faiss_index.status)}
                  <Text strong style={{ fontSize: 20, textTransform: 'capitalize' }}>
                    {health?.faiss_index?.status || 'Unknown'}
                  </Text>
                </Space>
                {health?.faiss_index && (
                  <>
                    <Text type="secondary">
                      Vectors: {health.faiss_index.vectors_count?.toLocaleString()}
                    </Text>
                    <Text type="secondary">Dimension: {health.faiss_index.dimension}</Text>
                  </>
                )}
              </Space>
            </Card>
          </Col>

          {/* Cache */}
          <Col xs={24} md={12} lg={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">Cache</Text>
                <Space>
                  {health?.cache && getStatusIcon(health.cache.status)}
                  <Text strong style={{ fontSize: 20, textTransform: 'capitalize' }}>
                    {health?.cache?.status || 'Unknown'}
                  </Text>
                </Space>
                {health?.cache && (
                  <>
                    <Text type="secondary">
                      Size: {health.cache.size} / {health.cache.max_size}
                    </Text>
                    <Progress
                      percent={Math.round((health.cache.size / health.cache.max_size) * 100)}
                      size="small"
                      status={
                        health.cache.size / health.cache.max_size > 0.9 ? 'exception' : 'active'
                      }
                    />
                  </>
                )}
              </Space>
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* Statistics */}
        {stats && (
          <>
            <Title level={4}>
              <ThunderboltOutlined /> Matcher Statistics
            </Title>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Total Matches"
                    value={stats.total_matches}
                    prefix={<DatabaseOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Matches Today"
                    value={stats.matches_today}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Avg Latency"
                    value={stats.avg_latency_ms}
                    suffix="ms"
                    valueStyle={{ color: stats.avg_latency_ms < 100 ? '#52c41a' : '#faad14' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Card>
                  <Statistic
                    title="Cache Hit Rate"
                    value={Math.round(stats.hit_rate * 100)}
                    suffix="%"
                    valueStyle={{ color: stats.hit_rate > 0.5 ? '#52c41a' : '#faad14' }}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col xs={24} md={12}>
                <Card title="By Match Type" size="small">
                  <Space wrap>
                    {stats.by_match_type &&
                      Object.entries(stats.by_match_type).map(([type, count]) => (
                        <Tag key={type} color="blue">
                          {type}: {count}
                        </Tag>
                      ))}
                  </Space>
                </Card>
              </Col>
              <Col xs={24} md={12}>
                <Card title="By Tier" size="small">
                  <Space wrap>
                    {stats.by_tier &&
                      Object.entries(stats.by_tier).map(([tier, count]) => (
                        <Tag key={tier} color="green">
                          {tier}: {count}
                        </Tag>
                      ))}
                  </Space>
                </Card>
              </Col>
            </Row>

            <Card title="Cache Details" size="small" style={{ marginTop: 16 }}>
              <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 4 }}>
                <Descriptions.Item label="Cache Hits">{stats.cache_hits}</Descriptions.Item>
                <Descriptions.Item label="Cache Misses">{stats.cache_misses}</Descriptions.Item>
                <Descriptions.Item label="Hit Rate">
                  {Math.round(stats.hit_rate * 100)}%
                </Descriptions.Item>
                <Descriptions.Item label="Total Requests">
                  {stats.cache_hits + stats.cache_misses}
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </>
        )}
      </Spin>
    </div>
  )
}
