import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Progress,
  Statistic,
  Table,
  Tag,
  Spin,
  Empty,
  Tabs,
  Space,
  Button,
  Badge,
  Modal,
  message,
  Divider,
  Alert
} from 'antd';
import {
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  ReloadOutlined,
  LineChartOutlined,
  RobotOutlined,
  BulbOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;

// 配置axios - 使用环境变量中的API地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const DimensionStatistics = () => {
  const [loading, setLoading] = useState(false);
  const [statisticsData, setStatisticsData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // AI总结相关状态
  const [summaryModal, setSummaryModal] = useState({
    visible: false,
    loading: false,
    category: '',
    data: null
  });

  // 获取维度统计数据
  const fetchDimensionStatistics = useCallback(async () => {
    try {
      setLoading(true);
      
      // 并行获取维度统计和badcase统计
      const [dimensionResponse, badcaseResponse] = await Promise.all([
        api.get('/dimension-statistics'),
        api.get('/badcase-statistics')
      ]);
      
      if (dimensionResponse.data.success) {
        const data = dimensionResponse.data.data;
        
        // 添加badcase统计数据
        if (badcaseResponse.data.success) {
          data.badcase_statistics = badcaseResponse.data.data;
        }
        
        setStatisticsData(data);
      } else {
        console.error('获取维度统计失败:', dimensionResponse.data.message);
      }
    } catch (error) {
      console.error('获取维度统计失败:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // 初始化数据
  useEffect(() => {
    fetchDimensionStatistics();
  }, [fetchDimensionStatistics]);

  // AI总结功能
  const handleAISummary = async (category) => {
    try {
      setSummaryModal({
        visible: true,
        loading: true,
        category: category,
        data: null
      });

      const response = await api.post(`/badcase-summary/${encodeURIComponent(category)}`);
      
      if (response.data.success) {
        setSummaryModal(prev => ({
          ...prev,
          loading: false,
          data: response.data.data
        }));
        message.success('AI总结生成完成');
      } else {
        throw new Error(response.data.message || 'AI总结生成失败');
      }
    } catch (error) {
      console.error('AI总结失败:', error);
      message.error(error.response?.data?.message || error.message || 'AI总结生成失败');
      setSummaryModal(prev => ({
        ...prev,
        loading: false,
        visible: false
      }));
    }
  };

  const closeSummaryModal = () => {
    setSummaryModal({
      visible: false,
      loading: false,
      category: '',
      data: null
    });
  };

  // 跳转到badcase管理页面
  const handleNavigateToBadcase = (category = null, badcaseType = null) => {
    // 构建跳转URL到外部badcase页面
    const baseUrl = 'http://9.135.87.101:8701/badcase';
    const params = new URLSearchParams();
    
    // 如果指定了badcase类型，设置筛选条件
    if (badcaseType) {
      params.append('badcase_type', badcaseType);
    }
    
    // 如果指定了分类，设置分类筛选条件
    if (category) {
      params.append('category', category);
    }
    
    // 构建完整URL
    const targetUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
    
    // 使用window.open在新标签页打开
    window.open(targetUrl, '_blank');
  };

  // 获取百分比对应的颜色
  const getPercentageColor = (percentage) => {
    if (percentage >= 80) return '#52c41a';
    if (percentage >= 60) return '#1890ff';
    if (percentage >= 40) return '#faad14';
    return '#ff4d4f';
  };

  // 获取百分比对应的等级
  const getPercentageLevel = (percentage) => {
    if (percentage >= 80) return { text: '优秀', color: 'success' };
    if (percentage >= 60) return { text: '良好', color: 'processing' };
    if (percentage >= 40) return { text: '一般', color: 'warning' };
    return { text: '需改进', color: 'error' };
  };

  // 维度图标映射（支持新维度体系）
  const getDimensionIcon = (dimensionName) => {
    const iconMap = {
      // 新维度体系（优先级最高）
      '数据准确性': '🎯',
      '数据时效性': '⏰',
      '内容完整性': '📋',
      '用户视角': '👤',
      // 兼容旧维度
      '准确性': '🎯',
      'accuracy': '🎯',
      '完整性': '📋',
      'completeness': '📋',
      '流畅性': '💬',
      'fluency': '💬',
      '安全性': '🛡️',
      'safety': '🛡️',
      '相关性': '🔗',
      'relevance': '🔗',
      '清晰度': '💡',
      'clarity': '💡',
      '时效性': '⏰',
      'timeliness': '⏰',
      '可用性': '⚡',
      'usability': '⚡',
      '合规性': '✅',
      'compliance': '✅'
    };
    
    // 精确匹配
    if (iconMap[dimensionName]) {
      return iconMap[dimensionName];
    }
    
    // 模糊匹配（针对新维度体系）
    if (dimensionName.includes('准确性') || dimensionName.includes('accuracy')) {
      return '🎯';
    }
    if (dimensionName.includes('时效性') || dimensionName.includes('timeliness')) {
      return '⏰';
    }
    if (dimensionName.includes('完整性') || dimensionName.includes('completeness')) {
      return '📋';
    }
    if (dimensionName.includes('用户') || dimensionName.includes('视角')) {
      return '👤';
    }
    
    // 其他模糊匹配
    for (const [key, icon] of Object.entries(iconMap)) {
      if (dimensionName.includes(key) || key.includes(dimensionName)) {
        return icon;
      }
    }
    
    return '📊'; // 默认图标
  };

  // 获取AI和人工评估数据（在组件顶层定义）
  const aiData = statisticsData?.ai_evaluation || {};
  const humanData = statisticsData?.human_evaluation || {};
  const summary = statisticsData?.summary || {};

  // 渲染概览页面
  const renderOverview = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '80px 20px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text style={{ fontSize: '16px', color: '#666' }}>
              正在加载维度统计数据...
            </Text>
          </div>
        </div>
      );
    }

    // 检查是否有任何评估数据（AI或人工）
    const hasAnyData = statisticsData && (
      (Object.keys(aiData).length > 0) ||
      (Object.keys(humanData).length > 0)
    );

    if (!hasAnyData) {
      return (
        <div style={{ padding: '24px' }}>
          {/* 新维度体系介绍 */}
          <Card 
            style={{ 
              marginBottom: 32, 
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)',
              border: '2px solid #e8f4fd'
            }}
            bodyStyle={{ padding: '32px' }}
          >
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <Title level={2} style={{ color: '#1890ff', marginBottom: 16 }}>
                🎯 新维度体系已启用
              </Title>
              <Text style={{ fontSize: '16px', color: '#666' }}>
                系统已完成数据库重构，现在使用全新的四维度评估体系
              </Text>
            </div>
            
            <Row gutter={[24, 24]}>
              <Col xs={24} sm={12} md={6}>
                <Card
                  size="small"
                  style={{
                    textAlign: 'center',
                    height: '180px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    color: 'white'
                  }}
                  bodyStyle={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>🎯</div>
                  <Title level={4} style={{ color: 'white', margin: '0 0 8px 0' }}>
                    数据准确性
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                    Data Accuracy
                  </Text>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '11px', marginTop: '8px' }}>
                    评估数据的准确性和可靠性
                  </Text>
                </Card>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <Card
                  size="small"
                  style={{
                    textAlign: 'center',
                    height: '180px',
                    background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    border: 'none',
                    color: 'white'
                  }}
                  bodyStyle={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>⏰</div>
                  <Title level={4} style={{ color: 'white', margin: '0 0 8px 0' }}>
                    数据时效性
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                    Data Timeliness
                  </Text>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '11px', marginTop: '8px' }}>
                    评估数据的时效性和及时性
                  </Text>
                </Card>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <Card
                  size="small"
                  style={{
                    textAlign: 'center',
                    height: '180px',
                    background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    border: 'none',
                    color: 'white'
                  }}
                  bodyStyle={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>📋</div>
                  <Title level={4} style={{ color: 'white', margin: '0 0 8px 0' }}>
                    内容完整性
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                    Content Completeness
                  </Text>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '11px', marginTop: '8px' }}>
                    评估内容的完整性和全面性
                  </Text>
                </Card>
              </Col>
              
              <Col xs={24} sm={12} md={6}>
                <Card
                  size="small"
                  style={{
                    textAlign: 'center',
                    height: '180px',
                    background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                    border: 'none',
                    color: 'white'
                  }}
                  bodyStyle={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}
                >
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>👤</div>
                  <Title level={4} style={{ color: 'white', margin: '0 0 8px 0' }}>
                    用户视角
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '12px' }}>
                    User Perspective
                  </Text>
                  <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '11px', marginTop: '8px' }}>
                    从用户角度评估体验和实用性
                  </Text>
                </Card>
              </Col>
            </Row>
          </Card>
          
          {/* 使用指南 */}
          <Row gutter={[24, 24]}>
            <Col xs={24} md={16}>
              <Card 
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>📊</span>
                    <Text strong style={{ fontSize: '16px' }}>开始使用新维度体系</Text>
                  </div>
                }
                style={{ height: '100%' }}
              >
                <Space direction="vertical" size={16} style={{ width: '100%' }}>
                  <div>
                    <Text strong style={{ color: '#1890ff' }}>第一步：配置评估标准</Text>
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">
                        访问 <Text code>标准配置</Text> 页面，为不同分类配置新维度体系的评估标准
                      </Text>
                    </div>
                  </div>
                  
                  <div>
                    <Text strong style={{ color: '#52c41a' }}>第二步：进行评估测试</Text>
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">
                        前往 <Text code>AI评估</Text> 或 <Text code>人工评估</Text> 页面，提交问题进行评估
                      </Text>
                    </div>
                  </div>
                  
                  <div>
                    <Text strong style={{ color: '#fa8c16' }}>第三步：查看统计数据</Text>
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary">
                        完成评估后，回到此页面查看基于新维度体系的统计分析
                      </Text>
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
            
            <Col xs={24} md={8}>
              <Card 
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '20px' }}>ℹ️</span>
                    <Text strong style={{ fontSize: '16px' }}>系统状态</Text>
                  </div>
                }
                style={{ height: '100%' }}
              >
                <Space direction="vertical" size={12} style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>数据库状态</Text>
                    <Tag color="green">✅ 已重构</Tag>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>维度体系</Text>
                    <Tag color="blue">🎯 新版本</Tag>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>评估记录</Text>
                    <Tag color="orange">📊 等待数据</Tag>
                  </div>
                  
                  <div style={{ marginTop: 16, textAlign: 'center' }}>
                    <Button type="primary" onClick={fetchDimensionStatistics} style={{ width: '100%' }}>
                      刷新统计数据
                    </Button>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </div>
      );
    }

    // 计算整体统计
    const totalEvaluations = summary.ai_total_evaluations + summary.human_total_evaluations;
    
    // 合并所有维度数据用于计算整体性能
    const allDimensions = [];
    
    // 添加AI评估维度
    Object.entries(aiData).forEach(([category, categoryData]) => {
      if (categoryData.dimensions) {
        Object.entries(categoryData.dimensions).forEach(([key, data]) => {
          allDimensions.push({ key, ...data, category, source: 'AI' });
        });
      }
    });
    
    // 添加人工评估维度
    Object.entries(humanData).forEach(([category, categoryData]) => {
      if (categoryData.dimensions) {
        Object.entries(categoryData.dimensions).forEach(([key, data]) => {
          allDimensions.push({ key, ...data, category, source: '人工' });
        });
      }
    });

    const avgPerformance = allDimensions.length > 0 ? 
      (allDimensions.reduce((sum, d) => sum + (d.avg_percentage || 0), 0) / allDimensions.length).toFixed(1) : 0;

    return (
      <div style={{ padding: '0 8px' }}>
        {/* 总体统计概览 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
          <Col xs={24} sm={12} md={6}>
            <Card 
              style={{ 
                textAlign: 'center', 
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                color: 'white'
              }}
              bodyStyle={{ padding: '24px 20px' }}
            >
              <Statistic
                title={<Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>总评估次数</Text>}
                value={totalEvaluations}
                prefix={<BarChartOutlined style={{ color: 'white', fontSize: '20px' }} />}
                valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              style={{ 
                textAlign: 'center', 
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                border: 'none',
                color: 'white'
              }}
              bodyStyle={{ padding: '24px 20px' }}
            >
              <Statistic
                title={<Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>分类数量</Text>}
                value={summary.ai_categories + summary.human_categories}
                prefix={<PieChartOutlined style={{ color: 'white', fontSize: '20px' }} />}
                valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
              />
              <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>
                AI: {summary.ai_categories} | 人工: {summary.human_categories}
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              style={{ 
                textAlign: 'center', 
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                border: 'none',
                color: 'white'
              }}
              bodyStyle={{ padding: '24px 20px' }}
            >
              <Statistic
                title={<Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>维度总数</Text>}
                value={allDimensions.length}
                prefix={<LineChartOutlined style={{ color: 'white', fontSize: '20px' }} />}
                valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card 
              style={{ 
                textAlign: 'center', 
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                border: 'none',
                color: 'white'
              }}
              bodyStyle={{ padding: '24px 20px' }}
            >
              <Statistic
                title={<Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: '14px' }}>平均表现</Text>}
                value={avgPerformance}
                suffix="%"
                prefix={<TrophyOutlined style={{ color: 'white', fontSize: '20px' }} />}
                valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        </Row>

        {/* AI评估与人工评估对比 */}
        <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
          {/* AI评估结果 */}
          <Col xs={24} lg={12}>
            <Card 
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>🤖</span>
                  <Text strong style={{ fontSize: '18px', color: '#722ed1' }}>
                    AI评估结果
                  </Text>
                  <Text type="secondary" style={{ fontSize: '14px' }}>
                    ({summary.ai_total_evaluations}条记录)
                  </Text>
                </div>
              }
              style={{ 
                borderRadius: '16px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
                border: '2px solid #f0f2ff'
              }}
              bodyStyle={{ padding: '24px' }}
            >
              {Object.keys(aiData).length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
                  <Text type="secondary">暂无AI评估数据</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      进行AI评估后将在此处显示统计结果
                    </Text>
                  </div>
                </div>
              ) : (
                <Row gutter={[16, 16]}>
                  {Object.entries(aiData).map(([category, categoryData]) => (
                    <Col xs={24} key={`ai-${category}`}>
                      <div style={{ marginBottom: '16px' }}>
                        <Text strong style={{ fontSize: '16px', color: '#722ed1' }}>
                          {category}
                        </Text>
                        <Text type="secondary" style={{ marginLeft: '8px' }}>
                          ({categoryData.total_evaluations}次评估)
                        </Text>
                      </div>
                      <Row gutter={[12, 12]}>
                        {Object.entries(categoryData.dimensions || {}).map(([dimKey, dimData]) => (
                          <Col xs={12} sm={8} key={`ai-${category}-${dimKey}`}>
                            <Card size="small" style={{ textAlign: 'center', background: '#f8f9ff' }}>
                              <div style={{ fontSize: '16px', marginBottom: '4px' }}>
                                {getDimensionIcon(dimData.dimension_name)}
                              </div>
                              <Text style={{ fontSize: '12px', display: 'block' }}>
                                {dimData.dimension_name}
                              </Text>
                              <Text strong style={{ color: '#722ed1' }}>
                                {dimData.avg_percentage.toFixed(1)}%
                              </Text>
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    </Col>
                  ))}
                </Row>
              )}
            </Card>
          </Col>

          {/* 人工评估结果 */}
          <Col xs={24} lg={12}>
            <Card 
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '20px' }}>👤</span>
                  <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                    人工评估结果
                  </Text>
                  <Text type="secondary" style={{ fontSize: '14px' }}>
                    ({summary.human_total_evaluations}条记录)
                  </Text>
                </div>
              }
              style={{ 
                borderRadius: '16px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.1)',
                border: '2px solid #e6f7ff'
              }}
              bodyStyle={{ padding: '24px' }}
            >
              {Object.keys(humanData).length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: '#999' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>👤</div>
                  <Text type="secondary">暂无人工评估数据</Text>
                  <div style={{ marginTop: '8px' }}>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      进行人工评估后将在此处显示统计结果
                    </Text>
                  </div>
                </div>
              ) : (
                <Row gutter={[16, 16]}>
                  {Object.entries(humanData).map(([category, categoryData]) => (
                    <Col xs={24} key={`human-${category}`}>
                      <div style={{ marginBottom: '16px' }}>
                        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                          {category}
                        </Text>
                        <Text type="secondary" style={{ marginLeft: '8px' }}>
                          ({categoryData.total_evaluations}次评估)
                        </Text>
                      </div>
                      <Row gutter={[12, 12]}>
                        {Object.entries(categoryData.dimensions || {}).map(([dimKey, dimData]) => (
                          <Col xs={12} sm={8} key={`human-${category}-${dimKey}`}>
                            <Card size="small" style={{ textAlign: 'center', background: '#f6ffed' }}>
                              <div style={{ fontSize: '16px', marginBottom: '4px' }}>
                                {getDimensionIcon(dimData.dimension_name)}
                              </div>
                              <Text style={{ fontSize: '12px', display: 'block' }}>
                                {dimData.dimension_name}
                              </Text>
                              <Text strong style={{ color: '#1890ff' }}>
                                {dimData.avg_percentage.toFixed(1)}%
                              </Text>
                            </Card>
                          </Col>
                        ))}
                      </Row>
                    </Col>
                  ))}
                </Row>
              )}
            </Card>
          </Col>
        </Row>

        {/* 各维度整体表现 */}
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>🎯</span>
              <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                各维度整体表现 (AI + 人工)
              </Text>
            </div>
          }
          style={{ 
            marginBottom: 32, 
            borderRadius: '16px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
          }}
          bodyStyle={{ padding: '32px 24px' }}
        >
          <Row gutter={[24, 24]}>
            {/* 按维度分组统计 */}
            {Object.entries(
              allDimensions.reduce((acc, dim) => {
                if (!acc[dim.dimension_name]) {
                  acc[dim.dimension_name] = {
                    name: dim.dimension_name,
                    totalEvals: 0,
                    totalScore: 0,
                    totalMaxScore: 0,
                    evaluations: []
                  };
                }
                acc[dim.dimension_name].totalEvals += dim.total_evaluations;
                acc[dim.dimension_name].totalScore += dim.avg_score * dim.total_evaluations;
                acc[dim.dimension_name].totalMaxScore += dim.max_possible_score * dim.total_evaluations;
                acc[dim.dimension_name].evaluations.push(dim);
                return acc;
              }, {})
            ).map(([dimName, dimData]) => {
              const avgPercentage = dimData.totalMaxScore > 0 ? 
                ((dimData.totalScore / dimData.totalMaxScore) * 100) : 0;
              
              return (
                <Col xs={24} sm={12} md={8} lg={6} key={dimName}>
                  <Card
                    style={{
                      background: 'linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%)',
                      border: '2px solid #e8f4fd',
                      borderRadius: '16px',
                      height: '260px',
                      transition: 'all 0.3s ease',
                      cursor: 'pointer'
                    }}
                    hoverable
                    bodyStyle={{ padding: '24px 20px', height: '100%' }}
                  >
                    <div style={{ 
                      textAlign: 'center', 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column', 
                      justifyContent: 'space-between',
                      minHeight: '220px'
                    }}>
                      <div style={{ flex: '0 0 auto' }}>
                                              <div style={{ fontSize: '32px', marginBottom: '10px' }}>
                        {getDimensionIcon(dimName)}
                      </div>
                        <Title level={5} style={{ 
                          margin: '0 0 8px 0', 
                          color: '#1890ff', 
                          fontSize: '16px',
                          fontWeight: 'bold'
                        }}>
                          {dimName}
                        </Title>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {dimData.totalEvals} 次评估
                        </Text>
                        <div style={{ marginTop: '4px' }}>
                          {dimData.evaluations.map((evaluation, idx) => (
                            <Text key={idx} style={{ 
                              fontSize: '10px', 
                              marginRight: '4px',
                              padding: '2px 6px',
                              borderRadius: '8px',
                              background: evaluation.source === 'AI' ? '#f0f2ff' : '#f6ffed',
                              color: evaluation.source === 'AI' ? '#722ed1' : '#1890ff'
                            }}>
                              {evaluation.source}
                            </Text>
                          ))}
                        </div>
                      </div>
                      
                      <div style={{ flex: '1 1 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '16px 0' }}>
                        <Progress
                          type="circle"
                          percent={Math.round(avgPercentage)}
                          size={80}
                          strokeColor={getPercentageColor(avgPercentage)}
                          strokeWidth={8}
                          format={percent => (
                            <span style={{ 
                              fontSize: '16px', 
                              fontWeight: 'bold',
                              color: getPercentageColor(avgPercentage)
                            }}>
                              {percent}%
                            </span>
                          )}
                        />
                      </div>
                      
                      <div style={{ flex: '0 0 auto', paddingTop: '8px' }}>
                        <Tag 
                          color={getPercentageLevel(avgPercentage).color} 
                          style={{ 
                            fontSize: '12px',
                            fontWeight: 'bold',
                            padding: '6px 16px',
                            borderRadius: '12px',
                            border: 'none',
                            height: '28px',
                            lineHeight: '16px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}
                        >
                          {getPercentageLevel(avgPercentage).text}
                        </Tag>
                      </div>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </Card>

        {/* 分类表现对比 */}
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>📈</span>
              <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                分类表现对比
              </Text>
            </div>
          }
          style={{ 
            borderRadius: '16px',
            boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
          }}
          bodyStyle={{ padding: '32px 24px' }}
        >
          <Row gutter={[24, 24]}>
            {/* 合并AI和人工评估的分类 */}
            {[...new Set([...Object.keys(aiData), ...Object.keys(humanData)])].map(category => {
              const aiCategoryData = aiData[category];
              const humanCategoryData = humanData[category];
              
              // 合并维度数据
              const allDimensionsForCategory = [];
              
              if (aiCategoryData?.dimensions) {
                Object.entries(aiCategoryData.dimensions).forEach(([key, data]) => {
                  allDimensionsForCategory.push({...data, source: 'AI'});
                });
              }
              
              if (humanCategoryData?.dimensions) {
                Object.entries(humanCategoryData.dimensions).forEach(([key, data]) => {
                  allDimensionsForCategory.push({...data, source: '人工'});
                });
              }
              
              const totalEvaluations = (aiCategoryData?.total_evaluations || 0) + (humanCategoryData?.total_evaluations || 0);
              const avgPerformance = allDimensionsForCategory.length > 0 ? 
                (allDimensionsForCategory.reduce((sum, d) => sum + d.avg_percentage, 0) / allDimensionsForCategory.length).toFixed(1) : 0;

              return (
                <Col xs={24} sm={12} md={8} key={category}>
                  <Card
                    style={{
                      background: 'linear-gradient(135deg, #fff9f0 0%, #ffffff 100%)',
                      border: '2px solid #ffe7ba',
                      borderRadius: '16px',
                      height: '180px'
                    }}
                    bodyStyle={{ padding: '20px' }}
                  >
                    <div style={{ textAlign: 'center' }}>
                      <Title level={5} style={{ 
                        margin: '0 0 12px 0', 
                        color: '#fa8c16',
                        fontSize: '16px'
                      }}>
                        {category}
                      </Title>
                      
                      <div style={{ margin: '16px 0' }}>
                        <Statistic
                          value={avgPerformance}
                          suffix="%"
                          valueStyle={{ 
                            color: getPercentageColor(parseFloat(avgPerformance)),
                            fontSize: '24px',
                            fontWeight: 'bold'
                          }}
                        />
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {totalEvaluations} 次评估
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {allDimensionsForCategory.length} 个维度
                        </Text>
                      </div>
                      
                      <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'center', gap: '4px' }}>
                        {aiCategoryData && (
                          <Text style={{ 
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '8px',
                            background: '#f0f2ff',
                            color: '#722ed1'
                          }}>
                            AI
                          </Text>
                        )}
                        {humanCategoryData && (
                          <Text style={{ 
                            fontSize: '10px',
                            padding: '2px 6px',
                            borderRadius: '8px',
                            background: '#f6ffed',
                            color: '#1890ff'
                          }}>
                            人工
                          </Text>
                        )}
                      </div>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </Card>
      </div>
    );
  };

  // 渲染分类详情页面
  const renderCategoryDetail = (category) => {
    const aiCategoryData = aiData[category];
    const humanCategoryData = humanData[category];
    
    if (!aiCategoryData && !humanCategoryData) return null;

    // 合并AI和人工评估的维度数据
    const allDimensions = [];
    
    if (aiCategoryData?.dimensions) {
      Object.entries(aiCategoryData.dimensions).forEach(([key, data]) => {
        allDimensions.push([key, {...data, source: 'AI'}]);
      });
    }
    
    if (humanCategoryData?.dimensions) {
      Object.entries(humanCategoryData.dimensions).forEach(([key, data]) => {
        allDimensions.push([key, {...data, source: '人工'}]);
      });
    }
    
    const dimensions = allDimensions;

    // 表格列定义
    const columns = [
      {
        title: '维度',
        dataIndex: 'dimension_name',
        key: 'dimension_name',
        width: 140,
        fixed: 'left',
        render: (text, record) => (
          <Space size={8}>
            <span style={{ fontSize: '18px' }}>
              {getDimensionIcon(text)}
            </span>
            <Text strong style={{ color: '#1890ff' }}>{text}</Text>
          </Space>
        )
      },
      {
        title: '评估类型',
        dataIndex: 'source',
        key: 'source',
        width: 90,
        align: 'center',
        render: (source) => (
          <Tag color={source === 'AI' ? 'purple' : 'blue'} style={{ 
            fontSize: '12px',
            fontWeight: 'bold',
            padding: '4px 8px',
            borderRadius: '8px',
            border: 'none'
          }}>
            {source}
          </Tag>
        )
      },
      {
        title: '评估次数',
        dataIndex: 'total_evaluations',
        key: 'total_evaluations',
        width: 100,
        align: 'center',
        sorter: (a, b) => a.total_evaluations - b.total_evaluations,
        render: (count) => (
          <Tag color="blue" style={{ 
            fontSize: '12px',
            height: '24px',
            lineHeight: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 8px'
          }}>
            {count} 次
          </Tag>
        )
      },
      {
        title: '平均分数',
        dataIndex: 'avg_score',
        key: 'avg_score',
        width: 130,
        align: 'center',
        render: (score, record) => (
          <div style={{ textAlign: 'center' }}>
            <div>
              <Text strong style={{ fontSize: '16px', color: '#52c41a' }}>
                {score}
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                /{record.max_possible_score}
              </Text>
            </div>
          </div>
        ),
        sorter: (a, b) => a.avg_score - b.avg_score
      },
      {
        title: '百分比表现',
        dataIndex: 'avg_percentage',
        key: 'avg_percentage',
        width: 180,
        align: 'center',
        render: (percentage) => (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            <Progress
              percent={Math.round(percentage)}
              size="small"
              strokeColor={getPercentageColor(percentage)}
              strokeWidth={8}
              showInfo={false}
              style={{ width: '100px' }}
            />
            <Text style={{ 
              color: getPercentageColor(percentage), 
              fontWeight: 'bold',
              fontSize: '14px'
            }}>
              {percentage.toFixed(1)}%
            </Text>
          </div>
        ),
        sorter: (a, b) => a.avg_percentage - b.avg_percentage
      },
      {
        title: '表现等级',
        dataIndex: 'avg_percentage',
        key: 'level',
        width: 100,
        align: 'center',
        render: (percentage) => {
          const level = getPercentageLevel(percentage);
          return (
            <Tag 
              color={level.color} 
              style={{ 
                fontSize: '12px',
                fontWeight: 'bold',
                padding: '4px 12px',
                borderRadius: '8px',
                border: 'none',
                height: '26px',
                lineHeight: '18px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {level.text}
            </Tag>
          );
        }
      }
    ];

    // 准备表格数据
    const tableData = dimensions.map(([dimensionKey, dimensionData]) => ({
      key: `${dimensionData.source}-${dimensionKey}`,
      dimension_key: dimensionKey,
      dimension_name: dimensionData.dimension_name,
      source: dimensionData.source,
      total_evaluations: dimensionData.total_evaluations,
      avg_score: dimensionData.avg_score,
      max_possible_score: dimensionData.max_possible_score,
      avg_percentage: dimensionData.avg_percentage,
      min_percentage: dimensionData.min_percentage,
      max_percentage: dimensionData.max_percentage
    }));

    return (
      <div style={{ padding: '0 4px' }}>
        {/* 分类统计概览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title={<Text style={{ color: '#666', fontSize: '14px' }}>总评估次数</Text>}
                value={(aiCategoryData?.total_evaluations || 0) + (humanCategoryData?.total_evaluations || 0)}
                prefix={<BarChartOutlined style={{ color: '#1890ff' }} />}
                valueStyle={{ color: '#1890ff', fontSize: '24px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title={<Text style={{ color: '#666', fontSize: '14px' }}>维度数量</Text>}
                value={dimensions.length}
                prefix={<PieChartOutlined style={{ color: '#52c41a' }} />}
                valueStyle={{ color: '#52c41a', fontSize: '24px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title={<Text style={{ color: '#666', fontSize: '14px' }}>平均表现</Text>}
                value={dimensions.length > 0 ? 
                  (dimensions.reduce((sum, [, d]) => sum + d.avg_percentage, 0) / dimensions.length).toFixed(1) : 0
                }
                suffix="%"
                prefix={<TrophyOutlined style={{ color: '#faad14' }} />}
                valueStyle={{ color: '#faad14', fontSize: '24px', fontWeight: 'bold' }}
              />
            </Card>
          </Col>
        </Row>

        {/* 维度表现卡片 - 优化布局 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
          {dimensions.map(([dimensionKey, dimensionData]) => (
            <Col xs={24} sm={12} md={8} lg={6} key={dimensionKey}>
              <Card
                size="small"
                style={{
                  background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)',
                  border: '1px solid #e8f4fd',
                  borderRadius: '16px',
                  height: '260px',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
                  transition: 'all 0.3s ease',
                  cursor: 'pointer',
                  overflow: 'visible'
                }}
                hoverable
                bodyStyle={{ 
                  padding: '24px 20px', 
                  height: 'calc(100% - 2px)',
                  display: 'flex',
                  flexDirection: 'column'
                }}
              >
                <div style={{ 
                  textAlign: 'center', 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  justifyContent: 'space-between',
                  minHeight: '220px'
                }}>
                  <div style={{ flex: '0 0 auto', marginBottom: '8px' }}>
                    <div style={{ fontSize: '28px', marginBottom: '8px' }}>
                      {getDimensionIcon(dimensionData.dimension_name)}
                    </div>
                    <Title level={5} style={{ margin: '0 0 6px 0', color: '#1890ff', fontSize: '16px' }}>
                      {dimensionData.dimension_name}
                    </Title>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {dimensionData.total_evaluations} 次评估
                    </Text>
                  </div>
                  
                  <div style={{ flex: '1 1 auto', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '16px 0' }}>
                    <Progress
                      type="circle"
                      percent={Math.round(dimensionData.avg_percentage)}
                      size={70}
                      strokeColor={getPercentageColor(dimensionData.avg_percentage)}
                      strokeWidth={6}
                      format={percent => (
                        <span style={{ 
                          fontSize: '14px', 
                          fontWeight: 'bold',
                          color: getPercentageColor(dimensionData.avg_percentage)
                        }}>
                          {percent}%
                        </span>
                      )}
                    />
                  </div>
                  
                  <div style={{ flex: '0 0 auto', paddingTop: '8px', paddingBottom: '8px' }}>
                    <Tag 
                      color={getPercentageLevel(dimensionData.avg_percentage).color} 
                      style={{ 
                        fontSize: '12px',
                        fontWeight: 'bold',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        border: 'none',
                        height: '28px',
                        lineHeight: '16px',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {getPercentageLevel(dimensionData.avg_percentage).text}
                    </Tag>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>

        {/* 详细数据表格 - 优化样式 */}
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px' }}>📊</span>
              <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                详细统计数据
              </Text>
            </div>
          }
          style={{ borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.05)' }}
          bodyStyle={{ padding: '24px' }}
        >
          <Table
            columns={columns}
            dataSource={tableData}
            pagination={false}
            size="middle"
            scroll={{ x: 650 }}
            rowClassName={(record, index) => 
              index % 2 === 0 ? 'table-row-light' : 'table-row-dark'
            }
            style={{
              background: '#fff',
              borderRadius: '8px'
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="暂无数据"
                />
              )
            }}
          />
        </Card>
        
        {/* 添加自定义样式 */}
        <style jsx>{`
          .table-row-light {
            background-color: #fafafa;
          }
          .table-row-dark {
            background-color: #ffffff;
          }
          .ant-table-tbody > tr:hover > td {
            background-color: #e6f7ff !important;
          }
        `}</style>
      </div>
    );
  };

  // 渲染AI评估页面
  const renderAIEvaluation = () => {
    if (Object.keys(aiData).length === 0) {
      return (
        <div style={{ padding: '60px 20px', textAlign: 'center' }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: '64px', opacity: 0.3, marginBottom: 16 }}>🤖</div>
            <Title level={3} style={{ color: '#722ed1', marginBottom: 8 }}>
              暂无AI评估数据
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              系统尚未生成AI评估结果，请先进行一些评估操作
            </Text>
          </div>
          <Button type="primary" ghost onClick={fetchDimensionStatistics}>
            刷新数据
          </Button>
        </div>
      );
    }

    // 如果有AI数据，使用类似humanData的展示方式
    return renderEvaluationData(aiData, '🤖 AI评估数据', '#722ed1');
  };

  // 渲染人工评估页面
  const renderHumanEvaluation = () => {
    if (Object.keys(humanData).length === 0) {
      return (
        <div style={{ padding: '60px 20px', textAlign: 'center' }}>
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: '64px', opacity: 0.3, marginBottom: 16 }}>👤</div>
            <Title level={3} style={{ color: '#1890ff', marginBottom: 8 }}>
              暂无人工评估数据
            </Title>
            <Text type="secondary" style={{ fontSize: '16px' }}>
              尚未进行人工评估，请先添加一些评估记录
            </Text>
          </div>
          <Button type="primary" onClick={fetchDimensionStatistics}>
            刷新数据
          </Button>
        </div>
      );
    }

    return renderEvaluationData(humanData, '👤 人工评估数据', '#1890ff');
  };

  // 渲染汇总页面
  const renderSummary = () => {
    return (
      <div style={{ padding: '24px' }}>
        <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="🤖 AI评估总数"
                value={summary.ai_total_evaluations || 0}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="👤 人工评估总数"
                value={summary.human_total_evaluations || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="🤖 AI评估分类"
                value={summary.ai_categories || 0}
                valueStyle={{ color: '#722ed1' }}
                suffix="个"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="👤 人工评估分类"
                value={summary.human_categories || 0}
                valueStyle={{ color: '#1890ff' }}
                suffix="个"
              />
            </Card>
          </Col>
        </Row>

        {/* 对比分析 */}
        <Card title="📊 AI vs 人工评估对比" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card size="small" title="🤖 AI评估状态" headStyle={{ backgroundColor: '#f0f2ff' }}>
                {Object.keys(aiData).length > 0 ? (
                  <div>
                    <Text>已有 {summary.ai_categories || 0} 个分类的AI评估数据</Text>
                  </div>
                ) : (
                  <Text type="secondary">暂无AI评估数据</Text>
                )}
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card size="small" title="👤 人工评估状态" headStyle={{ backgroundColor: '#e6f7ff' }}>
                {Object.keys(humanData).length > 0 ? (
                  <div>
                    <Text>已有 {summary.human_categories || 0} 个分类的人工评估数据</Text>
                  </div>
                ) : (
                  <Text type="secondary">暂无人工评估数据</Text>
                )}
              </Card>
            </Col>
          </Row>
        </Card>
      </div>
    );
  };

  // 通用评估数据渲染函数
  const renderEvaluationData = (data, title, themeColor) => {
    const categories = Object.keys(data);
    
    if (categories.length === 0) {
      return (
        <div style={{ padding: '60px 20px', textAlign: 'center' }}>
          <Empty description="暂无数据" />
        </div>
      );
    }

    return (
      <div style={{ padding: '24px' }}>
        <Title level={3} style={{ color: themeColor, marginBottom: 24 }}>
          {title}
        </Title>
        
        {categories.map(category => (
          <Card key={category} style={{ marginBottom: 24 }}>
            <Title level={4} style={{ color: themeColor, marginBottom: 16 }}>{category}</Title>
            {renderSingleSourceCategoryDetail(data[category], themeColor)}
          </Card>
        ))}
      </div>
    );
  };

  // 渲染badcase分析页面
  const renderBadcaseAnalysis = () => {
    if (!statisticsData.badcase_statistics) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Empty description="暂无Badcase统计数据" />
        </div>
      );
    }
    
    const badcaseData = statisticsData.badcase_statistics;
    const { overall, by_category } = badcaseData;
    
    // 获取百分比对应的状态
    const getBadcaseStatus = (percentage) => {
      if (percentage <= 5) return { text: '质量优秀', color: 'success', icon: '✅' };
      if (percentage <= 15) return { text: '质量一般', color: 'warning', icon: '⚠️' };
      return { text: '需要关注', color: 'error', icon: '🚨' };
    };
    
    const overallStatus = getBadcaseStatus(overall.total_badcase_percentage);
    
    return (
      <div>
        {/* 总体Badcase统计 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
          <Col xs={24} sm={6}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title="总评估记录"
                value={overall.total_records}
                valueStyle={{ color: '#1890ff' }}
                prefix="📊"
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card 
              style={{ 
                textAlign: 'center', 
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                border: '1px solid #d9d9d9'
              }}
              hoverable
              onClick={() => handleNavigateToBadcase()}
            >
              <Statistic
                title="Badcase总数"
                value={overall.total_badcases}
                valueStyle={{ color: '#ff4d4f' }}
                prefix="🚨"
              />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                点击查看详情
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title="AI判断Badcase"
                value={overall.ai_badcases}
                suffix={`(${overall.ai_badcase_percentage}%)`}
                valueStyle={{ color: '#faad14' }}
                prefix="🤖"
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card style={{ textAlign: 'center', borderRadius: '12px' }}>
              <Statistic
                title="人工标记Badcase"
                value={overall.human_badcases}
                suffix={`(${overall.human_badcase_percentage}%)`}
                valueStyle={{ color: '#722ed1' }}
                prefix="👤"
              />
            </Card>
          </Col>
        </Row>
        
        {/* 总体质量评估 */}
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={16} align="middle">
            <Col span={12}>
              <Progress
                type="circle"
                percent={overall.total_badcase_percentage}
                status={overallStatus.color}
                format={(percent) => `${percent}%`}
                width={120}
                strokeColor={overallStatus.color === 'error' ? '#ff4d4f' : overallStatus.color === 'warning' ? '#faad14' : '#52c41a'}
              />
            </Col>
            <Col span={12}>
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  {overallStatus.icon} 系统质量评估
                </Title>
                <div style={{ marginTop: 8 }}>
                  <Tag color={overallStatus.color} style={{ fontSize: '14px' }}>
                    {overallStatus.text}
                  </Tag>
                </div>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">
                    总计 {overall.total_records} 条记录中有 {overall.total_badcases} 条Badcase
                  </Text>
                </div>
              </div>
            </Col>
          </Row>
        </Card>
        
        {/* 各分类Badcase统计 */}
        <Card title="各分类Badcase统计">
          <Row gutter={[16, 16]}>
            {Object.entries(by_category).map(([category, stats]) => {
              const categoryStatus = getBadcaseStatus(stats.badcase_percentage);
              
              return (
                <Col xs={24} sm={12} md={8} lg={6} key={category}>
                  <Card
                    size="small"
                    style={{
                      background: categoryStatus.color === 'error' ? 
                        'linear-gradient(135deg, #fff2f0 0%, #ffffff 100%)' :
                        categoryStatus.color === 'warning' ?
                        'linear-gradient(135deg, #fffbe6 0%, #ffffff 100%)' :
                        'linear-gradient(135deg, #f6ffed 0%, #ffffff 100%)',
                      border: categoryStatus.color === 'error' ? 
                        '1px solid #ffccc7' :
                        categoryStatus.color === 'warning' ?
                        '1px solid #ffe58f' :
                        '1px solid #d9f7be'
                    }}
                  >
                    <div style={{ textAlign: 'center' }}>
                      <Title level={5} style={{ margin: '0 0 8px 0' }}>
                        {category}
                      </Title>
                      <div style={{ margin: '12px 0' }}>
                        <Text style={{ fontSize: '24px', fontWeight: 'bold', color: categoryStatus.color === 'error' ? '#ff4d4f' : categoryStatus.color === 'warning' ? '#faad14' : '#52c41a' }}>
                          {stats.badcase_percentage.toFixed(1)}%
                        </Text>
                      </div>
                      <div>
                        <Text 
                          type="secondary" 
                          style={{ 
                            fontSize: '12px',
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            color: '#1890ff'
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleNavigateToBadcase(category, 'human');
                          }}
                        >
                          {stats.badcase_count}/{stats.total_records} 条
                        </Text>
                      </div>
                      <div style={{ marginTop: 8 }}>
                        <Tag color={categoryStatus.color} size="small">
                          {categoryStatus.icon} {categoryStatus.text}
                        </Tag>
                      </div>
                      <div style={{ marginTop: 12 }}>
                        <Button
                          type="primary"
                          size="small"
                          icon={<RobotOutlined />}
                          onClick={() => handleAISummary(category)}
                          style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none',
                            borderRadius: '6px'
                          }}
                        >
                          智能分析
                        </Button>
                      </div>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </Card>
        
        {/* 质量评估说明 */}
        <Card style={{ marginTop: 16 }}>
          <Title level={5}>质量评估标准</Title>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Tag color="success">✅ 质量优秀</Tag>
              <Text type="secondary">Badcase率 ≤ 5%</Text>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Tag color="warning">⚠️ 质量一般</Tag>
              <Text type="secondary">Badcase率 5% - 15%</Text>
            </div>
                         <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
               <Tag color="error">🚨 需要关注</Tag>
               <Text type="secondary">Badcase率 &gt; 15%</Text>
             </div>
          </div>
        </Card>
      </div>
    );
  };

  // 渲染单一数据源的分类详情（AI或人工）
  const renderSingleSourceCategoryDetail = (categoryData, themeColor) => {
    if (!categoryData || !categoryData.dimensions) {
      return <Empty description="暂无数据" />;
    }

    const dimensions = Object.entries(categoryData.dimensions);

    // 表格列定义 - 简化版，只用于单一数据源
    const columns = [
      {
        title: '维度',
        dataIndex: 'dimension_name',
        key: 'dimension_name',
        width: 150,
        render: (text) => (
          <Space size={8}>
            <span style={{ fontSize: '18px' }}>
              {getDimensionIcon(text)}
            </span>
            <Text strong style={{ color: themeColor }}>{text}</Text>
          </Space>
        )
      },
      {
        title: '评估次数',
        dataIndex: 'total_evaluations',
        key: 'total_evaluations',
        width: 100,
        align: 'center',
        render: (count) => (
          <Tag color="blue" style={{ 
            fontSize: '12px',
            height: '24px',
            lineHeight: '12px',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '0 8px'
          }}>
            {count} 次
          </Tag>
        )
      },
      {
        title: '平均分数',
        dataIndex: 'avg_score',
        key: 'avg_score',
        width: 130,
        align: 'center',
        render: (score, record) => (
          <div style={{ textAlign: 'center' }}>
            <Text strong style={{ fontSize: '16px', color: '#52c41a' }}>
              {score}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              /{record.max_possible_score}
            </Text>
          </div>
        )
      },
      {
        title: '百分比表现',
        dataIndex: 'avg_percentage',
        key: 'avg_percentage',
        width: 180,
        align: 'center',
        render: (percentage) => (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
            <Progress
              percent={Math.round(percentage)}
              size="small"
              strokeColor={getPercentageColor(percentage)}
              strokeWidth={8}
              showInfo={false}
              style={{ width: '100px' }}
            />
            <Text style={{ 
              color: getPercentageColor(percentage), 
              fontWeight: 'bold',
              fontSize: '14px'
            }}>
              {percentage.toFixed(1)}%
            </Text>
          </div>
        )
      },
      {
        title: '表现等级',
        dataIndex: 'avg_percentage',
        key: 'level',
        width: 100,
        align: 'center',
        render: (percentage) => {
          const level = getPercentageLevel(percentage);
          return (
            <Tag 
              color={level.color} 
              style={{ 
                fontSize: '12px',
                fontWeight: 'bold',
                padding: '4px 12px',
                borderRadius: '8px',
                border: 'none',
                height: '26px',
                lineHeight: '18px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              {level.text}
            </Tag>
          );
        }
      }
    ];

    // 准备表格数据
    const tableData = dimensions.map(([dimensionKey, dimensionData]) => ({
      key: dimensionKey,
      dimension_key: dimensionKey,
      dimension_name: dimensionData.dimension_name,
      total_evaluations: dimensionData.total_evaluations,
      avg_score: dimensionData.avg_score,
      max_possible_score: dimensionData.max_possible_score,
      avg_percentage: dimensionData.avg_percentage
    }));

    return (
      <div>
        {/* 统计概览 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={8}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="总评估次数"
                value={categoryData.total_evaluations}
                valueStyle={{ fontSize: '18px', color: themeColor }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="维度数量"
                value={dimensions.length}
                valueStyle={{ fontSize: '18px', color: themeColor }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card size="small" style={{ textAlign: 'center' }}>
              <Statistic
                title="平均表现"
                value={dimensions.length > 0 ? 
                  (dimensions.reduce((sum, [, d]) => sum + d.avg_percentage, 0) / dimensions.length).toFixed(1) : 0
                }
                suffix="%"
                valueStyle={{ fontSize: '18px', color: themeColor }}
              />
            </Card>
          </Col>
        </Row>

        {/* 维度详情表格 */}
        <Table
          columns={columns}
          dataSource={tableData}
          pagination={false}
          size="middle"
          locale={{ emptyText: <Empty description="暂无数据" /> }}
        />
      </div>
    );
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载维度统计数据...</Text>
        </div>
      </div>
    );
  }

  if (!statisticsData || Object.keys(statisticsData).length === 0) {
    return (
      <div style={{ padding: '24px' }}>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>
            <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            维度统计分析
          </Title>
          <Text type="secondary">
            各个分类下各维度的评分表现统计分析
          </Text>
        </div>
        
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无统计数据，请先进行一些评估"
          >
            <Button type="primary" onClick={fetchDimensionStatistics}>
              刷新数据
            </Button>
          </Empty>
        </Card>
      </div>
    );
  }

      // 构建标签页
    const tabItems = [
      {
        key: 'overview',
        label: '总览',
        children: renderOverview()
      },
      {
        key: 'ai_evaluation',
        label: (
          <span>
            🤖 AI评估
            {summary.ai_total_evaluations > 0 && (
              <Badge count={summary.ai_total_evaluations} style={{ marginLeft: 8 }} />
            )}
          </span>
        ),
        children: renderAIEvaluation()
      },
      {
        key: 'human_evaluation',
        label: (
          <span>
            👤 人工评估
            {summary.human_total_evaluations > 0 && (
              <Badge count={summary.human_total_evaluations} style={{ marginLeft: 8 }} />
            )}
          </span>
        ),
        children: renderHumanEvaluation()
      },
      {
        key: 'badcase_analysis',
        label: (
          <span>
            🚨 Badcase分析
            {statisticsData.badcase_statistics && statisticsData.badcase_statistics.overall.total_badcases > 0 && (
              <Badge count={statisticsData.badcase_statistics.overall.total_badcases} style={{ marginLeft: 8 }} />
            )}
          </span>
        ),
        children: renderBadcaseAnalysis()
      },
      {
        key: 'summary',
        label: '数据汇总',
        children: renderSummary()
      }
    ];

  // 渲染AI总结结果
  const renderSummaryContent = () => {
    if (summaryModal.loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
                            <Text>AI正在进行智能分析，请稍候...</Text>
          </div>
        </div>
      );
    }

    if (!summaryModal.data) {
      return null;
    }

    const { summary, total_reasons } = summaryModal.data;

    if (summary.parse_error) {
      return (
        <div>
          <Alert
            message="总结格式解析失败"
            description="AI返回的内容格式不规范，以下是原始总结内容："
            type="warning"
            style={{ marginBottom: 16 }}
          />
          <div style={{ 
            background: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '8px',
            whiteSpace: 'pre-wrap'
          }}>
            {summary.summary}
          </div>
        </div>
      );
    }

    return (
      <div>
        {/* 概览信息 */}
        <div style={{ marginBottom: 24, padding: '16px', background: '#f6f9fc', borderRadius: '8px' }}>
          <Alert
            message="分析说明"
            description="此分析基于人工评估标记的Badcase原因，通过AI进行智能总结和归纳"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          <Row gutter={16}>
            <Col span={12}>
              <Statistic
                title="人工评估原因总数"
                value={total_reasons}
                prefix={<BulbOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="识别的主要问题"
                value={summary.main_issues ? summary.main_issues.length : 0}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
          </Row>
        </div>

        {/* 整体总结 */}
        {summary.summary && (
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>📋 整体总结</Title>
            <Alert
              message={summary.summary}
              type="info"
              style={{ marginBottom: 16 }}
            />
          </div>
        )}

        {/* 主要问题类型 */}
        {summary.main_issues && summary.main_issues.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>🎯 主要问题类型</Title>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {summary.main_issues.map((issue, index) => (
                <Card key={index} size="small" style={{ border: '1px solid #f0f0f0' }}>
                  <Row gutter={16} align="middle">
                    <Col span={16}>
                      <div>
                        <Text strong style={{ fontSize: '16px' }}>{issue.type}</Text>
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary">{issue.description}</Text>
                        </div>
                      </div>
                    </Col>
                    <Col span={8} style={{ textAlign: 'right' }}>
                      <div>
                        <Tag color={issue.severity === '高' ? 'red' : issue.severity === '中' ? 'orange' : 'green'}>
                          {issue.severity}
                        </Tag>
                      </div>
                      <div style={{ marginTop: 4 }}>
                        <Text strong>{issue.percentage}</Text>
                        <Text type="secondary" style={{ marginLeft: 4 }}>({issue.frequency})</Text>
                      </div>
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* 根本原因 */}
        {summary.root_causes && summary.root_causes.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>🔍 根本原因分析</Title>
            <ul style={{ paddingLeft: '20px' }}>
              {summary.root_causes.map((cause, index) => (
                <li key={index} style={{ marginBottom: '8px' }}>
                  <Text>{cause}</Text>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 改进建议 */}
        {summary.improvement_suggestions && summary.improvement_suggestions.length > 0 && (
          <div>
            <Title level={4}>💡 改进建议</Title>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {summary.improvement_suggestions.map((suggestion, index) => (
                <Card key={index} size="small" style={{ border: '1px solid #e6f7ff', background: '#f6ffed' }}>
                  <Row gutter={16}>
                    <Col span={18}>
                      <div>
                        <Text strong>{suggestion.problem}</Text>
                        <div style={{ marginTop: 4 }}>
                          <Text>{suggestion.suggestion}</Text>
                        </div>
                      </div>
                    </Col>
                    <Col span={6} style={{ textAlign: 'right' }}>
                      <Tag color={suggestion.priority === '高' ? 'red' : suggestion.priority === '中' ? 'orange' : 'blue'}>
                        {suggestion.priority}优先级
                      </Tag>
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>
              <BarChartOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              维度统计分析
            </Title>
            <Text type="secondary">
              各个分类下各维度的评分表现统计分析
            </Text>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={fetchDimensionStatistics}
              loading={loading}
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </div>

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab} 
        type="card"
        items={tabItems}
      />

      {/* AI总结Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <RobotOutlined style={{ color: '#667eea' }} />
            <span>Badcase智能分析 - {summaryModal.category}</span>
          </div>
        }
        open={summaryModal.visible}
        onCancel={closeSummaryModal}
        footer={[
          <Button key="close" onClick={closeSummaryModal}>
            关闭
          </Button>
        ]}
        width={800}
        style={{ top: 20 }}
      >
        {renderSummaryContent()}
      </Modal>
    </div>
  );
};

export default DimensionStatistics; 