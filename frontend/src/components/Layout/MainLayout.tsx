import { ReactNode } from 'react'
import { Layout, Menu, Button } from 'antd'
import {
  DashboardOutlined,
  FolderOutlined,
  UploadOutlined,
  UnorderedListOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  PieChartOutlined,
  AuditOutlined,
  StopOutlined,
  ToolOutlined,
  CloudServerOutlined,
  TagsOutlined,
  BarcodeOutlined,
  EditOutlined,
  CloudUploadOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/store/authStore'

const { Header, Sider, Content } = Layout

interface MainLayoutProps {
  children: ReactNode
}

export default function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const menuItems = [
    { key: '/', label: 'Dashboard', icon: <DashboardOutlined /> },
    { key: '/projects', label: 'Projects', icon: <FolderOutlined /> },
    { key: '/upload', label: 'Upload BOQ', icon: <UploadOutlined /> },
    { key: '/line-items', label: 'Line Items', icon: <UnorderedListOutlined /> },
    {
      key: 'master-group',
      label: 'Master Database',
      icon: <DatabaseOutlined />,
      children: [
        { key: '/master-items', label: 'Master Items', icon: <DatabaseOutlined /> },
        { key: '/work-code-generator', label: 'Code Generator', icon: <ThunderboltOutlined /> },
        { key: '/master-statistics', label: 'Statistics', icon: <PieChartOutlined /> },
      ],
    },
    {
      key: 'tools-group',
      label: 'Tools',
      icon: <ToolOutlined />,
      children: [
        { key: '/boq-processing', label: 'BOQ Processing', icon: <CloudUploadOutlined /> },
        { key: '/templates', label: 'Mapping Templates', icon: <FileTextOutlined /> },
        { key: '/naming-tools', label: 'Naming Tools', icon: <EditOutlined /> },
        { key: '/code-management', label: 'Code Systems', icon: <BarcodeOutlined /> },
      ],
    },
    {
      key: 'approval-group',
      label: 'Approval Workflow',
      icon: <AuditOutlined />,
      children: [
        { key: '/pending-items', label: 'Pending Review', icon: <AuditOutlined /> },
        { key: '/quarantine-log', label: 'Quarantine Log', icon: <StopOutlined /> },
      ],
    },
    {
      key: 'admin-group',
      label: 'Admin',
      icon: <SettingOutlined />,
      children: [
        { key: '/synonyms', label: 'Synonyms', icon: <TagsOutlined /> },
        { key: '/system-health', label: 'System Health', icon: <CloudServerOutlined /> },
      ],
    },
    { key: '/analytics', label: 'Analytics', icon: <BarChartOutlined /> },
    { key: '/settings', label: 'Settings', icon: <SettingOutlined /> },
  ]

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="dark" width={250}>
        <div style={{ padding: '16px', color: 'white', fontSize: '18px', fontWeight: 'bold', textAlign: 'center' }}>
          BOQ System
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
        <div style={{ position: 'absolute', bottom: 16, width: '100%', padding: '0 16px' }}>
          <Button
            type="text"
            icon={<LogoutOutlined />}
            onClick={handleLogout}
            style={{ width: '100%', color: 'white' }}
          >
            Logout
          </Button>
        </div>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0 }}>Bill of Quantities Management</h2>
          <span>Welcome, {user?.full_name || user?.username}</span>
        </Header>
        <Content style={{ margin: '24px 16px', padding: 24, background: '#fff', minHeight: 280 }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}
