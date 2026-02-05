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
  Upload,
  Modal,
} from 'antd'
import {
  SearchOutlined,
  ReloadOutlined,
  TagsOutlined,
  UploadOutlined,
  SyncOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { synonymService, SynonymWithMaster, SynonymStats } from '@/services/synonymService'
import type { ColumnsType } from 'antd/es/table'
import type { UploadProps } from 'antd'

const { Title, Text } = Typography
const { Search } = Input

export default function SynonymManagement() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState<string | undefined>()
  const [pagination, setPagination] = useState({ skip: 0, limit: 50 })

  // Fetch synonyms
  const {
    data: synonyms,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ['allSynonyms', search, typeFilter, pagination],
    queryFn: () =>
      synonymService.listAll({
        search,
        type: typeFilter,
        skip: pagination.skip,
        limit: pagination.limit,
      }),
  })

  // Fetch statistics
  const { data: stats } = useQuery({
    queryKey: ['synonymStats'],
    queryFn: synonymService.getStatistics,
  })

  // Rebuild cache mutation
  const rebuildMutation = useMutation({
    mutationFn: synonymService.rebuildCache,
    onSuccess: (data) => {
      message.success(`Cache rebuilt: ${data.synonyms_cached} synonyms cached`)
    },
    onError: () => {
      message.error('Failed to rebuild cache')
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: synonymService.deleteSynonym,
    onSuccess: () => {
      message.success('Synonym deleted')
      queryClient.invalidateQueries({ queryKey: ['allSynonyms'] })
      queryClient.invalidateQueries({ queryKey: ['synonymStats'] })
    },
    onError: () => {
      message.error('Failed to delete synonym')
    },
  })

  // Import mutation
  const importMutation = useMutation({
    mutationFn: synonymService.importFromCSV,
    onSuccess: (data) => {
      message.success(`Imported ${data.imported} synonyms, skipped ${data.skipped}`)
      if (data.errors.length > 0) {
        Modal.warning({
          title: 'Import Warnings',
          content: (
            <ul>
              {data.errors.slice(0, 10).map((e, i) => (
                <li key={i}>{e}</li>
              ))}
              {data.errors.length > 10 && <li>...and {data.errors.length - 10} more</li>}
            </ul>
          ),
        })
      }
      queryClient.invalidateQueries({ queryKey: ['allSynonyms'] })
      queryClient.invalidateQueries({ queryKey: ['synonymStats'] })
    },
    onError: () => {
      message.error('Failed to import synonyms')
    },
  })

  const uploadProps: UploadProps = {
    accept: '.csv',
    showUploadList: false,
    beforeUpload: (file) => {
      importMutation.mutate(file)
      return false
    },
  }

  const handleDelete = (synonymId: number) => {
    Modal.confirm({
      title: 'Delete Synonym',
      content: 'Are you sure you want to delete this synonym?',
      onOk: () => deleteMutation.mutate(synonymId),
    })
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'alias':
        return 'blue'
      case 'abbreviation':
        return 'green'
      case 'regional':
        return 'orange'
      case 'english':
        return 'purple'
      default:
        return 'default'
    }
  }

  const columns: ColumnsType<SynonymWithMaster> = [
    {
      title: 'Synonym',
      dataIndex: 'synonym_text',
      key: 'synonym_text',
      width: 250,
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: 'Type',
      dataIndex: 'synonym_type',
      key: 'synonym_type',
      width: 120,
      render: (type: string) => <Tag color={getTypeColor(type)}>{type}</Tag>,
    },
    {
      title: 'Master Work Code',
      dataIndex: 'master_work_code',
      key: 'master_work_code',
      width: 180,
      render: (code: string) => <Text copyable>{code}</Text>,
    },
    {
      title: 'Master Description',
      dataIndex: 'master_description',
      key: 'master_description',
      ellipsis: true,
    },
    {
      title: 'Source',
      dataIndex: 'source',
      key: 'source',
      width: 100,
      render: (source: string) => <Tag>{source || 'manual'}</Tag>,
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      align: 'center',
      render: (active: boolean) =>
        active ? (
          <Tag color="success">Yes</Tag>
        ) : (
          <Tag color="error">No</Tag>
        ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Button
          type="text"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDelete(record.synonym_id)}
        />
      ),
    },
  ]

  return (
    <div>
      <Title level={3}>
        <TagsOutlined /> Synonym Management
      </Title>
      <Text type="secondary">
        Manage synonyms across all master items for better matching accuracy
      </Text>

      {/* Statistics Cards */}
      {stats && (
        <Row gutter={16} style={{ marginTop: 24, marginBottom: 24 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Total Synonyms"
                value={stats.total_synonyms}
                prefix={<TagsOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Items with Synonyms"
                value={stats.items_with_synonyms}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Avg per Item"
                value={stats.avg_synonyms_per_item?.toFixed(1) || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text type="secondary">By Type</Text>
                <div>
                  {stats.by_type &&
                    Object.entries(stats.by_type).map(([type, count]) => (
                      <Tag key={type} color={getTypeColor(type)} style={{ marginBottom: 4 }}>
                        {type}: {count}
                      </Tag>
                    ))}
                </div>
              </Space>
            </Card>
          </Col>
        </Row>
      )}

      {/* Main Table Card */}
      <Card
        title={
          <Space>
            <TagsOutlined />
            <Title level={4} style={{ margin: 0 }}>
              All Synonyms
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Upload {...uploadProps}>
              <Button
                icon={<UploadOutlined />}
                loading={importMutation.isPending}
              >
                Import CSV
              </Button>
            </Upload>
            <Button
              icon={<SyncOutlined />}
              onClick={() => rebuildMutation.mutate()}
              loading={rebuildMutation.isPending}
            >
              Rebuild Cache
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
            placeholder="Search synonyms or descriptions..."
            allowClear
            style={{ width: 300 }}
            onSearch={setSearch}
            prefix={<SearchOutlined />}
          />
          <Select
            placeholder="Filter by type"
            allowClear
            style={{ width: 200 }}
            onChange={setTypeFilter}
            options={[
              { label: 'Alias', value: 'alias' },
              { label: 'Abbreviation', value: 'abbreviation' },
              { label: 'Regional', value: 'regional' },
              { label: 'English', value: 'english' },
            ]}
          />
        </Space>

        {/* Table */}
        <Table
          columns={columns}
          dataSource={synonyms}
          rowKey="synonym_id"
          loading={isLoading}
          scroll={{ x: 1100 }}
          pagination={{
            pageSize: pagination.limit,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} synonyms`,
            onChange: (page, pageSize) => {
              setPagination({
                skip: (page - 1) * pageSize,
                limit: pageSize,
              })
            },
          }}
        />
      </Card>
    </div>
  )
}
