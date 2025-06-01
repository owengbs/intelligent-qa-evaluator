import React, { useState } from 'react';
import { Layout, Menu, Typography, Space, Button } from 'antd';
import { 
  HomeOutlined, 
  SettingOutlined, 
  QuestionCircleOutlined,
  GithubOutlined,
  BulbOutlined,
  ToolOutlined
} from '@ant-design/icons';
import EvaluationForm from './components/EvaluationForm';
import ClassificationConfig from './components/ClassificationConfig';
import EvaluationStandardConfig from './components/EvaluationStandardConfig';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Text } = Typography;

function App() {
  const [selectedMenu, setSelectedMenu] = useState('evaluation');

  const menuItems = [
    {
      key: 'evaluation',
      icon: <HomeOutlined />,
      label: '质量评估',
    },
    {
      key: 'classification',
      icon: <SettingOutlined />,
      label: '分类配置',
    },
    {
      key: 'evaluationStandard',
      icon: <ToolOutlined />,
      label: '评估标准',
    }
  ];

  const renderContent = () => {
    switch (selectedMenu) {
      case 'evaluation':
        return <EvaluationForm />;
      case 'classification':
        return <ClassificationConfig />;
      case 'evaluationStandard':
        return <EvaluationStandardConfig />;
      default:
        return <EvaluationForm />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center',
        background: 'linear-gradient(90deg, #1890ff 0%, #722ed1 100%)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}>
        <div style={{ 
          color: 'white', 
          fontSize: '20px', 
          fontWeight: 'bold',
          marginRight: '40px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <BulbOutlined />
          问AI评估系统
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[selectedMenu]}
          items={menuItems}
          onClick={({ key }) => setSelectedMenu(key)}
          style={{
            flex: 1,
            minWidth: 0,
            backgroundColor: 'transparent',
            borderBottom: 'none'
          }}
          theme="dark"
        />
        <Space>
          <Button 
            type="text" 
            icon={<GithubOutlined />} 
            style={{ color: 'white' }}
            href="https://github.com"
            target="_blank"
          >
            GitHub
          </Button>
          <Button 
            type="text" 
            icon={<QuestionCircleOutlined />} 
            style={{ color: 'white' }}
          >
            帮助
          </Button>
        </Space>
      </Header>

      <Content style={{ 
        padding: '24px 50px',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        minHeight: 'calc(100vh - 134px)'
      }}>
        {/* 主要内容区域 */}
        {renderContent()}
      </Content>

      <Footer style={{ 
        textAlign: 'center',
        background: '#f0f2f5',
        borderTop: '1px solid #d9d9d9'
      }}>
        <Space direction="vertical" size={4}>
          <Text strong>问AI评估系统 v2.1.0</Text>
          <Text type="secondary">
            基于大语言模型的自动化评估 · 支持多维度评分 · 智能分类识别 · 时间因素考虑 · 评估标准配置
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            Powered by React + Flask + DeepSeek LLM © 2025
          </Text>
        </Space>
      </Footer>
    </Layout>
  );
}

export default App; 