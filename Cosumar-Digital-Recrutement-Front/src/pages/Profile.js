import React, { useEffect, useState } from 'react';
import { Card, Typography, Descriptions } from 'antd';

const { Title } = Typography;
const cosumarBlue = '#005baa';

export default function Profile() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Assume user data is stored in localStorage as 'user' after login
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  if (!user) {
    return <div style={{ textAlign: 'center', marginTop: 40 }}>Aucune information utilisateur trouvée.</div>;
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Card style={{ width: 'auto', minWidth: 320, maxWidth: 500, boxShadow: '0 2px 16px rgba(0,0,0,0.08)' }}>
        <Title level={3} style={{ color: cosumarBlue, textAlign: 'center' }}>Profil Utilisateur</Title>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="ID Utilisateur">{user.user_id}</Descriptions.Item>
          <Descriptions.Item label="Email">{user.email}</Descriptions.Item>
          <Descriptions.Item label="Rôle">{user.role}</Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  );
} 