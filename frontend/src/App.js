import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography, Space } from 'antd';
import { 
  HomeOutlined, 
  BarChartOutlined, 
  HistoryOutlined,
  RobotOutlined,
  SettingOutlined,
  TagsOutlined,
  ControlOutlined
} from '@ant-design/icons';
import { Provider } from 'react-redux';
import { store } from './store/store';
import EvaluationForm from './components/EvaluationForm';
import EvaluationHistory from './components/EvaluationHistory';
import DimensionStatistics from './components/DimensionStatistics';
import ClassificationConfig from './components/ClassificationConfig';
import EvaluationStandardConfig from './components/EvaluationStandardConfig';
import DimensionManagement from './components/DimensionManagement';
import './App.css';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

// 分离出内部组件来使用useLocation
function AppLayout() {
  const location = useLocation();
  const [selectedKey, setSelectedKey] = React.useState('1');

  // 使用useMemo来优化menuItems，避免ESLint警告
  const menuItems = React.useMemo(() => [
    {
      key: '1',
      icon: <HomeOutlined />,
      label: '评估中心',
      path: '/'
    },
    {
      key: '2',
      icon: <HistoryOutlined />,
      label: '历史管理',
      path: '/history'
    },
    {
      key: '3',
      icon: <BarChartOutlined />,
      label: '维度统计',
      path: '/statistics'
    },
    {
      key: '4',
      icon: <TagsOutlined />,
      label: '分类管理',
      path: '/classification'
    },
    {
      key: '5',
      icon: <SettingOutlined />,
      label: '评估标准',
      path: '/standards'
    },
    {
      key: '6',
      icon: <ControlOutlined />,
      label: '维度管理',
      path: '/dimensions'
    }
  ], []);

  // 根据当前路径设置选中的菜单项
  useEffect(() => {
    const currentItem = menuItems.find(item => item.path === location.pathname);
    if (currentItem) {
      setSelectedKey(currentItem.key);
    }
  }, [location.pathname, menuItems]);

  const handleMenuClick = ({ key }) => {
    setSelectedKey(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
        padding: '0 24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          height: '100%' 
        }}>
          <Space size={16}>
            <RobotOutlined style={{ fontSize: '32px', color: 'white' }} />
            <Title level={3} style={{ 
              margin: 0, 
              color: 'white',
              fontWeight: 600
            }}>
              问AI评估系统
            </Title>
          </Space>
          <div style={{ marginLeft: 'auto' }}>
            <Space>
              <span style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                v2.1.0
              </span>
            </Space>
          </div>
        </div>
      </Header>
      
      <Layout>
        <Sider 
          width={200} 
          style={{ 
            background: '#fff',
            boxShadow: '2px 0 8px rgba(0,0,0,0.1)'
          }}
        >
          <Menu
            mode="inline"
            selectedKeys={[selectedKey]}
            onClick={handleMenuClick}
            style={{ 
              height: '100%', 
              borderRight: 0,
              paddingTop: '16px'
            }}
            items={menuItems.map(item => ({
              key: item.key,
              icon: item.icon,
              label: (
                <Link 
                  to={item.path}
                  style={{ textDecoration: 'none' }}
                >
                  {item.label}
                </Link>
              )
            }))}
          />
        </Sider>
        
        <Layout style={{ padding: 0 }}>
          <Content style={{ 
            margin: 0,
            minHeight: 280,
            background: '#f0f2f5'
          }}>
            <Routes>
              <Route path="/" element={<EvaluationForm />} />
              <Route path="/history" element={<EvaluationHistory />} />
              <Route path="/statistics" element={<DimensionStatistics />} />
              <Route path="/classification" element={<ClassificationConfig />} />
              <Route path="/standards" element={<EvaluationStandardConfig />} />
              <Route path="/dimensions" element={<DimensionManagement />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}

function App() {
  return (
    <Provider store={store}>
      <Router>
        <AppLayout />
      </Router>
    </Provider>
  );
}

export default App; 