import { useState } from 'react'
import { Form, Input, Button, Card, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authService } from '@/services/authService'
import { useAuthStore } from '@/store/authStore'

export default function Login() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login } = useAuthStore()

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const response = await authService.login(values)
      login(response.access_token, response.user)
      message.success('Login successful!')
      navigate('/')
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f0f2f5' }}>
      <Card title="BOQ System Login" style={{ width: 400 }}>
        <Form name="login" onFinish={onFinish} autoComplete="off">
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please input your username!' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Username" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Password" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              Log in
            </Button>
          </Form.Item>
        </Form>
        <div style={{ marginTop: 16, fontSize: 12, color: '#888' }}>
          <p>Demo credentials:</p>
          <p>Username: admin | Password: admin123</p>
        </div>
      </Card>
    </div>
  )
}
