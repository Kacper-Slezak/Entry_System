import React, { useState } from 'react';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UploadOutlined,
  UserOutlined,
  DashboardOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { Button, Layout, Menu, theme } from 'antd';
import { Link, useLocation } from 'react-router-dom';

const { Header, Sider, Content } = Layout;

const LayoutMain: React.FC<{children: React.ReactNode}> = ({children}) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Mapowanie ścieżek do kluczy menu, aby podświetlał się aktywny element
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path === '/logs') return ['1'];
    if (path === '/employees') return ['2'];
    if (path === '/add-employee') return ['3'];
    return ['1'];
  };

  return (
    <Layout style={{ width: '100%', height: '100%' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div className="demo-logo-vertical" />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={getSelectedKey()}
          items={[
            {
              key: '1',
              icon: <FileTextOutlined />,
              label: <Link to="/logs">Logs</Link>,
            },
            {
              key: '2',
              icon: <UserOutlined />,
              label: <Link to="/employees">Employees</Link>,
            },
            {
              key: '3',
              icon: <UploadOutlined />,
              label: <Link to="/add-employee">Add Employee</Link>,
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              fontSize: '16px',
              width: 64,
              height: 64,
            }}
          />
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default LayoutMain;
