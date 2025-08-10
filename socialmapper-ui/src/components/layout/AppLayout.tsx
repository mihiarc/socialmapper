/**
 * Main application layout component
 * Provides consistent header, navigation, and content structure
 */
import React, { useEffect } from 'react';
import { Layout, Menu, Button, Typography, Space, Dropdown, Avatar } from 'antd';
import { useLocation, useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  DashboardOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  BulbOutlined,
  MoonOutlined,
} from '@ant-design/icons';

import type { RootState } from '@store/index';
import { toggleSidebar, setTheme } from '@store/slices/uiSlice';
import NotificationCenter from '@components/common/NotificationCenter';
import ProgressPanel from '@components/common/ProgressPanel';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

interface AppLayoutProps {
  children: React.ReactNode;
}

/**
 * Application layout with navigation, header, and responsive sidebar
 */
const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useDispatch();
  
  const { sidebarCollapsed, theme, showProgressPanel } = useSelector(
    (state: RootState) => state.ui
  );
  const { activeJobs } = useSelector(
    (state: RootState) => state.analysis
  );

  // Menu items configuration
  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/demo',
      icon: <ExperimentOutlined />,
      label: 'Demo Scenarios',
    },
    {
      key: '/analysis',
      icon: <BarChartOutlined />,
      label: 'Analysis Wizard',
    },
  ];

  // User menu items
  const userMenuItems = [
    {
      key: 'theme',
      icon: theme === 'light' ? <MoonOutlined /> : <BulbOutlined />,
      label: `Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`,
      onClick: () => dispatch(setTheme(theme === 'light' ? 'dark' : 'light')),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign Out',
    },
  ];

  // Handle menu navigation
  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
          case 'b':
            event.preventDefault();
            dispatch(toggleSidebar());
            break;
          case '1':
            event.preventDefault();
            navigate('/');
            break;
          case '2':
            event.preventDefault();
            navigate('/demo');
            break;
          case '3':
            event.preventDefault();
            navigate('/analysis');
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [dispatch, navigate]);

  return (
    <Layout className="app-layout" style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={sidebarCollapsed}
        width={240}
        theme="light"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
        }}
      >
        {/* Logo section */}
        <div className="logo" style={{ 
          padding: '16px', 
          textAlign: 'center',
          borderBottom: '1px solid #f0f0f0',
          height: '64px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {!sidebarCollapsed ? (
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              🗺️ SocialMapper
            </Title>
          ) : (
            <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
              🗺️
            </Title>
          )}
        </div>

        {/* Navigation menu */}
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
          style={{ borderRight: 0, paddingTop: '8px' }}
        />

        {/* Active jobs indicator */}
        {activeJobs.length > 0 && (
          <div style={{ 
            position: 'absolute', 
            bottom: '16px', 
            left: '16px', 
            right: '16px',
            padding: '8px',
            background: '#e6f7ff',
            borderRadius: '6px',
            fontSize: '12px',
            color: '#1890ff'
          }}>
            {!sidebarCollapsed && (
              <>
                {activeJobs.length} active job{activeJobs.length > 1 ? 's' : ''}
              </>
            )}
          </div>
        )}
      </Sider>

      <Layout style={{ marginLeft: sidebarCollapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 99,
          }}
        >
          {/* Left side - collapse trigger */}
          <Button
            type="text"
            icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => dispatch(toggleSidebar())}
            style={{ fontSize: '16px', width: '40px', height: '40px' }}
          />

          {/* Right side - user menu and notifications */}
          <Space size="middle">
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Button type="text" style={{ height: '40px' }}>
                <Space>
                  <Avatar size="small" icon={<UserOutlined />} />
                  {!sidebarCollapsed && 'User'}
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            margin: 0,
            minHeight: 'calc(100vh - 64px)',
            overflow: 'auto',
          }}
        >
          {children}
        </Content>
      </Layout>

      {/* Global components */}
      <NotificationCenter />
      {showProgressPanel && <ProgressPanel />}
    </Layout>
  );
};

export default AppLayout;