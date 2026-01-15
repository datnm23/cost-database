import { Card, Tabs, Form, Input, Button, Switch, Select, message, Divider } from 'antd'
import { UserOutlined, LockOutlined, BellOutlined, SettingOutlined } from '@ant-design/icons'
import { useAuthStore } from '@/store/authStore'
import { useState } from 'react'

const { TabPane } = Tabs
const { Option } = Select

export default function Settings() {
  const { user } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const handleUpdateProfile = async (values: any) => {
    setLoading(true)
    try {
      // TODO: Implement profile update API call
      console.log('Update profile:', values)
      message.success('Profile updated successfully')
    } catch (error) {
      message.error('Failed to update profile')
    } finally {
      setLoading(false)
    }
  }

  const handleChangePassword = async (values: any) => {
    setLoading(true)
    try {
      // TODO: Implement password change API call
      console.log('Change password:', values)
      message.success('Password changed successfully')
    } catch (error) {
      message.error('Failed to change password')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdatePreferences = async (values: any) => {
    setLoading(true)
    try {
      // TODO: Implement preferences update API call
      console.log('Update preferences:', values)
      message.success('Preferences updated successfully')
    } catch (error) {
      message.error('Failed to update preferences')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>Settings</h1>

      <Card>
        <Tabs defaultActiveKey="profile">
          <TabPane
            tab={
              <span>
                <UserOutlined />
                Profile
              </span>
            }
            key="profile"
          >
            <Form
              layout="vertical"
              initialValues={{
                username: user?.username,
                email: user?.email,
                full_name: user?.full_name,
              }}
              onFinish={handleUpdateProfile}
              style={{ maxWidth: 600 }}
            >
              <Form.Item label="Username" name="username">
                <Input disabled />
              </Form.Item>

              <Form.Item
                label="Full Name"
                name="full_name"
                rules={[{ required: true, message: 'Please enter your full name' }]}
              >
                <Input />
              </Form.Item>

              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { required: true, message: 'Please enter your email' },
                  { type: 'email', message: 'Please enter a valid email' },
                ]}
              >
                <Input />
              </Form.Item>

              <Form.Item label="Phone" name="phone">
                <Input />
              </Form.Item>

              <Form.Item label="Department" name="department">
                <Input />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Update Profile
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={
              <span>
                <LockOutlined />
                Security
              </span>
            }
            key="security"
          >
            <Form
              layout="vertical"
              onFinish={handleChangePassword}
              style={{ maxWidth: 600 }}
            >
              <Form.Item
                label="Current Password"
                name="current_password"
                rules={[{ required: true, message: 'Please enter your current password' }]}
              >
                <Input.Password />
              </Form.Item>

              <Form.Item
                label="New Password"
                name="new_password"
                rules={[
                  { required: true, message: 'Please enter a new password' },
                  { min: 8, message: 'Password must be at least 8 characters' },
                ]}
              >
                <Input.Password />
              </Form.Item>

              <Form.Item
                label="Confirm New Password"
                name="confirm_password"
                dependencies={['new_password']}
                rules={[
                  { required: true, message: 'Please confirm your new password' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('Passwords do not match'))
                    },
                  }),
                ]}
              >
                <Input.Password />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Change Password
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={
              <span>
                <BellOutlined />
                Notifications
              </span>
            }
            key="notifications"
          >
            <Form
              layout="vertical"
              initialValues={{
                email_notifications: true,
                processing_complete: true,
                classification_updates: false,
                weekly_report: true,
              }}
              onFinish={handleUpdatePreferences}
              style={{ maxWidth: 600 }}
            >
              <Form.Item
                label="Email Notifications"
                name="email_notifications"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Divider />

              <h4>Notification Types</h4>

              <Form.Item
                label="File Processing Complete"
                name="processing_complete"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="Classification Updates"
                name="classification_updates"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                label="Weekly Summary Report"
                name="weekly_report"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Save Preferences
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          <TabPane
            tab={
              <span>
                <SettingOutlined />
                Preferences
              </span>
            }
            key="preferences"
          >
            <Form
              layout="vertical"
              initialValues={{
                language: 'en',
                timezone: 'UTC',
                date_format: 'MM/DD/YYYY',
                items_per_page: 50,
              }}
              onFinish={handleUpdatePreferences}
              style={{ maxWidth: 600 }}
            >
              <Form.Item label="Language" name="language">
                <Select>
                  <Option value="en">English</Option>
                  <Option value="es">Spanish</Option>
                  <Option value="fr">French</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Timezone" name="timezone">
                <Select showSearch>
                  <Option value="UTC">UTC</Option>
                  <Option value="America/New_York">Eastern Time</Option>
                  <Option value="America/Chicago">Central Time</Option>
                  <Option value="America/Denver">Mountain Time</Option>
                  <Option value="America/Los_Angeles">Pacific Time</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Date Format" name="date_format">
                <Select>
                  <Option value="MM/DD/YYYY">MM/DD/YYYY</Option>
                  <Option value="DD/MM/YYYY">DD/MM/YYYY</Option>
                  <Option value="YYYY-MM-DD">YYYY-MM-DD</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Items Per Page" name="items_per_page">
                <Select>
                  <Option value={25}>25</Option>
                  <Option value={50}>50</Option>
                  <Option value={100}>100</Option>
                  <Option value={200}>200</Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading}>
                  Save Preferences
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}
