import React, { useState } from 'react';
import { Button, Menu, Avatar } from 'antd';
import Sider from 'antd/es/layout/Sider';
import {
  MenuOutlined,
  DashboardOutlined,
  FileTextOutlined,
  UserOutlined,
  SolutionOutlined,
  ApartmentOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons';


function App() {
  const [message, setMessage] = useState('');
  const [collapsed, setCollapsed] = useState(true);

  // Example user data
  const user = {
    name: 'othmane Doe',
    email: 'john.doe@example.com',
  };

  return (
    <div>
      <Button 
        type="primary" 
        onClick={() => setCollapsed(!collapsed)}
        style={{ 
          position: 'fixed', 
          top: '10px', 
          left: collapsed ? '10px' : '210px',
          zIndex: 1001,
          transition: 'left 0.2s'
        }}
      >
        <MenuOutlined />
      </Button>
      
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        collapsedWidth={0}
        trigger={null}
        style={{
          background: '#ffffff',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          zIndex: 1000,
          boxShadow: '0 0 16px rgba(0, 21, 41, 0.2)',
          borderRadius: '0 8px 8px 0',
        }}
      >
        {/* User Profile Section */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '20px',
          borderBottom: '1px solid #f0f0f0',
          marginBottom: '10px'
        }}>
          <Avatar size={40} icon={<UserOutlined />} />
          <div style={{ marginLeft: '12px' }}>
            <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{user.name}</div>
            <div style={{ fontSize: '12px', color: '#888' }}>{user.email}</div>
          </div>
        </div>

        <Menu
          mode="inline"
          defaultSelectedKeys={['1']}
          items={[
            { key: '1', label: 'Tableau de bord', icon: <DashboardOutlined /> },
            { key: '2', label: 'Candidatures', icon: <FileTextOutlined /> },
            { key: '3', label: 'Candidats', icon: <UserOutlined /> },
            { key: '4', label: 'Offres d\'emploi', icon: <SolutionOutlined /> },
            { key: '5', label: 'Départements', icon: <ApartmentOutlined /> },
            { key: '6', label: 'Statistiques', icon: <BarChartOutlined /> },
            { key: '7', label: 'Paramètres', icon: <SettingOutlined /> },
          ]}

          style={{ 
            height: '100%', 
            borderRight: 0, 
            justifyItems: 'center', 
            paddingTop: '20px',
            disabled: collapsed,
          }}
          onBlur={() => setCollapsed(!collapsed)}
          className="custom-menu"
        />
      </Sider>
      <style>
        {`
          .custom-menu .ant-menu-item {
            margin-bottom: 16px;
          }
          .custom-menu .ant-menu-item:last-child {
            margin-bottom: 0;
          }
        `}
      </style>
    </div>
  );
}

export default App;
