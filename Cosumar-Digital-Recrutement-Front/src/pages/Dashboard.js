import React from 'react';
import { Card, Row, Col, Statistic, List, Avatar, Typography } from 'antd';
import { UserOutlined, FileTextOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title } = Typography;
const cosumarBlue = '#005baa';
const cosumarGreen = '#7ac143';
const cosumarSecondaryBlue = '#009fe3';
const cosumarLightBlue = '#e6f2fb';
const cosumarLightGreen = '#eafbe6';
const cosumarGold = '#ffd700';

const stats = [
  { title: 'Candidats', value: 128, icon: <UserOutlined style={{ color: cosumarBlue }} />, bg: cosumarLightBlue },
  { title: 'Offres publiées', value: 12, icon: <FileTextOutlined style={{ color: cosumarSecondaryBlue }} />, bg: cosumarGold },
  { title: 'Recrutements', value: 5, icon: <CheckCircleOutlined style={{ color: cosumarGreen }} />, bg: cosumarLightGreen },
];

const activities = [
  { title: 'Nouveau candidat inscrit', description: 'Othmane Rabat', icon: <UserOutlined />, color: cosumarBlue },
  { title: 'Offre publiée', description: 'Développeur Frontend', icon: <FileTextOutlined />, color: cosumarSecondaryBlue },
  { title: 'Candidat recruté', description: 'Sara El Amrani', icon: <CheckCircleOutlined />, color: cosumarGreen },
];

export default function Dashboard() {
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', width: '100%' }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card style={{
            background: `linear-gradient(90deg, ${cosumarBlue} 0%, ${cosumarSecondaryBlue} 60%, ${cosumarGreen} 100%)`,
            color: '#fff',
            borderRadius: 16,
            boxShadow: '0 4px 24px 0 rgba(0,0,0,0.08)',
          }}>
            <Title level={2} style={{ color: '#fff', margin: 0 }}>Bienvenue sur le tableau de bord Cosumar Digital Recrutement !</Title>
            <p style={{ color: '#e6f2fb', fontSize: 18, margin: 0 }}>Gérez vos offres, candidats et recrutements en un seul endroit.</p>
          </Card>
        </Col>
        <Col span={24}>
          <Row gutter={24}>
            {stats.map((stat, idx) => (
              <Col xs={24} sm={8} key={stat.title}>
                <Card style={{
                  borderRadius: 14,
                  textAlign: 'center',
                  background: stat.bg,
                  boxShadow: '0 2px 12px 0 rgba(0,0,0,0.06)',
                }}>
                  <Statistic
                    title={<span style={{ color: cosumarBlue }}>{stat.title}</span>}
                    value={stat.value}
                    prefix={stat.icon}
                    valueStyle={{ color: cosumarSecondaryBlue, fontWeight: 700, fontSize: 28 }}
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </Col>
        <Col span={24}>
          <Card title={<span style={{ color: cosumarBlue }}>Activité récente</span>} style={{ borderRadius: 14, background: '#fff', boxShadow: '0 2px 12px 0 rgba(0,0,0,0.06)' }}>
            <List
              itemLayout="horizontal"
              dataSource={activities}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar style={{ background: item.color }}>{item.icon}</Avatar>}
                    title={item.title}
                    description={item.description}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
} 