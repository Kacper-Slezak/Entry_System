import React from 'react';
import { Form, Input, Button, Card, Typography, Space, message } from 'antd';
import type { FormInstance } from 'antd/es/form';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';

const { Title } = Typography;

interface LoginFormData {
  username: string;
  password: string;
}


const LoginPage: React.FC = () => {
  const formRef = React.useRef<FormInstance>(null);
  const navigate = useNavigate();

  const handleSubmit = async (values: LoginFormData) => {
    try {
      const formData = new URLSearchParams();
      formData.append('username', values.username);
      formData.append('password', values.password);

      const response = await fetch('http://localhost:8000/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Login failed');
        message.error("Invalid credentials. Please check your email and password.");
      }
        const data = await response.json();

      Cookies.set('access_token', data.access_token, {
        expires: data.expiresIn ? data.expiresIn / (24 * 60 * 60) : 1/24, // 1 hour default
        secure: true,
        sameSite: 'strict',
        path: '/',
      });

      if (data.refreshToken) {
        Cookies.set('refreshToken', data.refreshToken, {
          expires: 7, // 7 days
          secure: true,
          sameSite: 'strict',
          path: '/',
        });
      }

      // Redirect to dashboard or home
      navigate('/logs');
    } catch (error) {
      console.error('Login error:', error);
      formRef.current?.scrollToField('email');
      formRef.current?.setFields([
        {
          name: 'email',
          errors: ['Invalid credentials. Please check your email and password.'],
        },
      ]);
    }
  };

  return (
    <Space
      direction="vertical"
      size="large"
      style={{
        display: 'flex',
        width: '100%',
        height: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f0f2f5',
      }}
    >
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
        <Title level={2} style={{ textAlign: 'center', marginBottom: 24, color: '#1890ff' }}>
          Login
        </Title>

        <Form
          ref={formRef}
          name="login"
          layout="vertical"
          onFinish={handleSubmit}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            label="Username"
            rules={[
              { required: true, message: 'Please input your username!' },
            ]}
          >
            <Input placeholder="Enter your username" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password placeholder="Enter your password" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              block
              size="large"
              style={{ height: 50 }}
              loading={false} // Add loading state if needed
            >
              Sign In
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </Space>
  );
};
export default LoginPage;
