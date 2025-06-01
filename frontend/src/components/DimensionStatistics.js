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
  Button
} from 'antd';
import {
  BarChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  ReloadOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;

// 配置axios
const api = axios.create({
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const DimensionStatistics = () => {
  const [loading, setLoading] = useState(false);
  const [statisticsData, setStatisticsData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // 获取维度统计数据
  const fetchDimensionStatistics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/dimension-statistics');
      
      if (response.data.success) {
        setStatisticsData(response.data.data);
      } else {
        console.error('获取维度统计失败:', response.data.message);
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

  // 维度图标映射
  const dimensionIcons = {
    accuracy: '🎯',
    completeness: '📋',
    fluency: '💬',
    safety: '🛡️',
    relevance: '🔗',
    clarity: '💡',
    timeliness: '⏰',
    usability: '⚡',
    compliance: '✅'
  };

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

    if (!statisticsData || Object.keys(statisticsData).length === 0) {
      return (
        <div style={{ padding: '24px', textAlign: 'center' }}>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <div>
                <Text style={{ fontSize: '16px', color: '#666' }}>
                  暂无统计数据
                </Text>
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">
                    请先进行一些评估后再查看统计信息
                  </Text>
                </div>
              </div>
            }
          >
            <Button type="primary" onClick={fetchDimensionStatistics}>
              刷新数据
            </Button>
          </Empty>
        </div>
      );
    }

    // 计算整体统计
    const categories = Object.keys(statisticsData);
    const totalEvaluations = categories.reduce((sum, cat) => 
      sum + (statisticsData[cat]?.total_evaluations || 0), 0
    );
    
    const allDimensions = [];
    categories.forEach(cat => {
      if (statisticsData[cat]?.dimensions) {
        Object.entries(statisticsData[cat].dimensions).forEach(([key, data]) => {
          allDimensions.push({ key, ...data, category: cat });
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
                value={categories.length}
                prefix={<PieChartOutlined style={{ color: 'white', fontSize: '20px' }} />}
                valueStyle={{ color: 'white', fontSize: '28px', fontWeight: 'bold' }}
              />
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

        {/* 各维度整体表现 */}
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '20px' }}>🎯</span>
              <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                各维度整体表现
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
                          {Object.keys(dimensionIcons).find(key => 
                            dimensionIcons[key] && dimName.includes(key.slice(-2))
                          ) ? dimensionIcons[Object.keys(dimensionIcons).find(key => 
                            dimName.includes(key.slice(-2))
                          )] : '📊'}
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
            {categories.map(category => {
              const categoryData = statisticsData[category];
              const dimensions = Object.entries(categoryData.dimensions || {});
              const avgPerformance = dimensions.length > 0 ? 
                (dimensions.reduce((sum, [, d]) => sum + d.avg_percentage, 0) / dimensions.length).toFixed(1) : 0;

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
                          {categoryData.total_evaluations} 次评估
                        </Text>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {dimensions.length} 个维度
                        </Text>
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
    if (!statisticsData || !statisticsData[category]) return null;

    const categoryData = statisticsData[category];
    const dimensions = Object.entries(categoryData.dimensions);

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
              {dimensionIcons[record.dimension_key] || '📊'}
            </span>
            <Text strong style={{ color: '#1890ff' }}>{text}</Text>
          </Space>
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
      key: dimensionKey,
      dimension_key: dimensionKey,
      dimension_name: dimensionData.dimension_name,
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
                value={categoryData.total_evaluations}
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
                      {dimensionIcons[dimensionKey] || '📊'}
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

  const categories = Object.keys(statisticsData);

  const tabItems = [
    {
      key: 'overview',
      label: '总览',
      children: renderOverview()
    },
    ...categories.map(category => ({
      key: category,
      label: category,
      children: renderCategoryDetail(category)
    }))
  ];

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
    </div>
  );
};

export default DimensionStatistics; 