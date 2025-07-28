import React, { useState } from 'react';
import { Form, Input, Button, Typography, Card, message } from 'antd';
import { Link, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../config';

const { Title } = Typography;

const cosumarBlue = '#005baa';
const cosumarGreen = '#7ac143';

function AnimatedBackground() {
  return (
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      zIndex: 0,
      overflow: 'hidden',
      pointerEvents: 'none',
    }}>
      {/* Multi-stop gradient */}
      <div style={{
        position: 'absolute',
        width: '100%',
        height: '100%',
        background: 'linear-gradient(120deg, #e6f2fb 0%, #b3e0c7 50%, #f6fff7 100%)',
      }} />
      {/* Animated floating circles */}
      <div className="floating-circle" style={{
        position: 'absolute', left: '10vw', top: '20vh', width: 180, height: 180, background: '#7ac14333', borderRadius: '50%', filter: 'blur(8px)', animation: 'float1 8s ease-in-out infinite',
      }} />
      <div className="floating-circle" style={{
        position: 'absolute', left: '70vw', top: '60vh', width: 120, height: 120, background: '#005baa33', borderRadius: '50%', filter: 'blur(8px)', animation: 'float2 10s ease-in-out infinite',
      }} />
      <div className="floating-circle" style={{
        position: 'absolute', left: '50vw', top: '10vh', width: 90, height: 90, background: '#7ac14322', borderRadius: '50%', filter: 'blur(6px)', animation: 'float3 12s ease-in-out infinite',
      }} />
      <style>{`
        @keyframes float1 {
          0% { transform: translateY(0) scale(1); }
          50% { transform: translateY(-30px) scale(1.08); }
          100% { transform: translateY(0) scale(1); }
        }
        @keyframes float2 {
          0% { transform: translateY(0) scale(1); }
          50% { transform: translateY(40px) scale(1.12); }
          100% { transform: translateY(0) scale(1); }
        }
        @keyframes float3 {
          0% { transform: translateY(0) scale(1); }
          50% { transform: translateY(-20px) scale(1.05); }
          100% { transform: translateY(0) scale(1); }
        }
      `}</style>
    </div>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [formError, setFormError] = useState('');
  const onFinish = (values) => {
    fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(values),
    })
      .then(res => res.json())
      .then(data => {
        console.log('API response:', data);
        if (data.user && data.user.auth === true && data.token) {
          localStorage.setItem('user', JSON.stringify(data.user));
          localStorage.setItem('token', data.token); // Store JWT token
          navigate('/dashboard');
        } else {
          setFormError(data.error || 'Email ou mot de passe incorrect');
        }
      })
      .catch(err => {
        console.error('API error:', err);
        setFormError('Erreur de connexion au serveur');
      });
  };
  return (
    <div style={{ minHeight: '100vh', position: 'relative', background: 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
      <AnimatedBackground />
      <Card style={{
        width: 370,
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.18)',
        zIndex: 1,
        backdropFilter: 'blur(8px)',
        background: 'rgba(255,255,255,0.75)',
        borderRadius: 18,
        border: '1px solid #e6f2fb',
      }}>
        <Title level={2} style={{ color: cosumarBlue, textAlign: 'center', marginBottom: 24 }}>Cosumar Digital Recrutement</Title>
        <Form
  layout="vertical"
  onFinish={onFinish}
  onFinishFailed={(error) => console.log('Validation error:', error)}
>
  <Form.Item
    label="Email"
    name="email"
    rules={[{ required: true, message: 'Veuillez saisir votre email !' }]}
  >
    <Input />
  </Form.Item>

  <Form.Item
    label="Mot de passe"
    name="mot_de_passe"
    rules={[{ required: true, message: 'Veuillez saisir votre mot de passe !' }]}
  >
    <Input.Password />
  </Form.Item>

  <Form.Item
    help={formError}
    validateStatus={formError ? "error" : ""}
  >
    <Button
      type="primary"
      htmlType="submit"
      block
      style={{ background: cosumarGreen, borderColor: cosumarGreen }}
    >
      Se connecter
    </Button>
  </Form.Item>
</Form>

        <div style={{ textAlign: 'center' }}>
          <span>Vous n'avez pas de compte ? </span>
          <Link to="/signup" style={{ color: cosumarBlue }}>S'inscrire</Link>
        </div>
      </Card>
    </div>
  );
} 