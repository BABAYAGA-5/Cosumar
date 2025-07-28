import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button } from 'antd';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { MenuUnfoldOutlined ,
  DashboardOutlined,
  MenuFoldOutlined,
  UserOutlined,
  LogoutOutlined
        
} from '@ant-design/icons';


const { Header, Content, Sider } = Layout;
const cosumarBlue = '#005baa';
const cosumarGreen = '#7ac143';

function ErrorPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
      <h1 style={{ color: cosumarBlue, fontSize: 48, marginBottom: 16 }}>Erreur d'accès</h1>
      <p style={{ color: '#333', fontSize: 20 }}>Vous devez être connecté pour accéder à cette page.</p>
    </div>
  );
}

export default function LayoutWithSidebar() {
  const [collapsed, setCollapsed] = useState(true);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    const token = localStorage.getItem('token');
    if (userData && token) {
      setUser(JSON.parse(userData));
    } else {
      setUser(null);
    }
  }, [location.pathname]);

  const handleMenuClick = (e) => {
    if (e.key === 'dashboard') navigate('/dashboard');
    if (e.key === 'profile') navigate('/profile');
    if (e.key === 'logout') {
      localStorage.removeItem('user');
      localStorage.removeItem('token'); // Remove JWT token
      navigate('/login');
    }
  };

  // Determine selected key based on current path
  let selectedKey = 'dashboard';
  if (location.pathname.startsWith('/profile')) selectedKey = 'profile';
  if (location.pathname.startsWith('/dashboard')) selectedKey = 'dashboard';

  if (!user) {
    return <ErrorPage />;
  }

  return (
    <Layout style={{ minHeight: '100vh', background: '#f6fff7' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={200}
        style={{
          background: cosumarBlue,
          boxShadow: '2px 0 12px 0 rgba(0,0,0,0.10)',
          zIndex: 1000,
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        breakpoint="lg"
        collapsedWidth={80}
        zIndex={1000}
      >
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          padding: '16px 0 0 0',
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{
              color: '#fff',
              fontSize: 20,
              marginBottom: 16,
              transition: 'opacity 0.3s, transform 0.3s',
              opacity: 1,
              transform: collapsed ? 'scale(1)' : 'scale(1.1)',
            }}
            shape="circle"
          />
          <div style={{
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 'bold',
            fontSize: 20,
            width: '100%',
            transition: 'opacity 0.3s, transform 0.3s',
            opacity: collapsed ? 0 : 1,
            transform: collapsed ? 'translateX(-20px)' : 'translateX(0)',
          }}>
            Cosumar
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          style={{
            flex: 1,
            borderRight: 0,
            background: cosumarBlue,
            color: '#fff',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start',
            minHeight: 0,
          }}
          onClick={handleMenuClick}
          theme="dark"
        >
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>Tableau de bord</Menu.Item>
          <Menu.Item key="profile" icon={<UserOutlined />}>Profil</Menu.Item>
        </Menu>
        <div style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: collapsed ? '12px 0' : '24px 0',
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'transparent',
          transition: 'all 0.3s',
        }}>
          <Button
            type="primary"
            icon={<LogoutOutlined />}
            onClick={() => handleMenuClick({ key: 'logout' })}
            style={{ background: cosumarGreen, borderColor: cosumarGreen, width: collapsed ? 40 : 160, transition: 'all 0.3s' }}
          >
            {!collapsed && 'Se déconnecter'}
          </Button>
        </div>
      </Sider>
      <Layout>
        <Header style={{ background: cosumarBlue, display: 'flex', alignItems: 'center', padding: '0 24px', justifyContent: 'flex-start' }}>
          <span style={{ color: '#fff', fontWeight: 600, fontSize: 22 }}>Cosumar Digital Recrutement</span>
        </Header>
        <Content style={{ padding: 40, minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
} 