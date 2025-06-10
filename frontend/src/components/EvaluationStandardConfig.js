import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Modal,
  Form,
  Checkbox,
  message,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Tooltip,
  Collapse,
  Badge,
  Empty,
  Divider
} from 'antd';
import {
  CheckOutlined,
  EditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  EyeOutlined
} from '@ant-design/icons';
import axios from 'axios';

// 配置API基础URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 增加到3分钟超时，适应大模型长时间处理
  headers: {
    'Content-Type': 'application/json',
  },
});

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const EvaluationStandardConfig = () => {
  const [loading, setLoading] = useState(false);
  const [dimensions, setDimensions] = useState([]);
  const [groupedDimensions, setGroupedDimensions] = useState({});
  const [selectedStandards, setSelectedStandards] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [viewingDimension, setViewingDimension] = useState(null);
  const [activeTab, setActiveTab] = useState('选股');
  const [categoryOptions, setCategoryOptions] = useState([]);

  // 加载分类选项
  const loadCategoryOptions = useCallback(async () => {
    try {
      console.log('🔧 Loading classification standards from:', `${API_BASE_URL}/classification-standards`);
      
      const response = await api.get('/classification-standards');
      if (response.data.standards) {
        // 从分类标准中提取唯一的二级分类
        const uniqueCategories = [...new Set(response.data.standards.map(item => item.level2))];
        const sortedCategories = uniqueCategories.sort();
        
        setCategoryOptions(sortedCategories);
        console.log('🔧 Category options loaded:', sortedCategories);
        
        // 如果当前activeTab不在新的分类列表中，设置为第一个分类
        if (!sortedCategories.includes(activeTab) && sortedCategories.length > 0) {
          setActiveTab(sortedCategories[0]);
        }
      } else {
        console.warn('未能获取分类标准');
        // 使用备用的默认分类
        const fallbackCategories = [
          '选股',
          '宏观经济分析',
          '大盘行业分析',
          '个股分析',
          '个股决策',
          '知识问答',
          '事实及指标类检索',
          '客服及交易',
          '无效问题（非金融问题）'
        ];
        setCategoryOptions(fallbackCategories);
      }
    } catch (error) {
      console.error('加载分类选项失败:', error);
      // 使用备用的默认分类
      const fallbackCategories = [
        '选股',
        '宏观经济分析', 
        '大盘行业分析',
        '个股分析',
        '个股决策',
        '知识问答',
        '事实及指标类检索',
        '客服及交易',
        '无效问题（非金融问题）'
      ];
      setCategoryOptions(fallbackCategories);
    }
  }, [activeTab]);

  // 层次选项
  const layerOptions = [
    '第一层指标',
    '第二层指标', 
    '第三层指标',
    '其他服务场景'
  ];

  // 加载所有维度数据
  const loadDimensions = useCallback(async () => {
    setLoading(true);
    try {
      console.log('🔧 Loading dimensions from:', `${API_BASE_URL}/dimensions`);
      
      const response = await api.get('/dimensions');
      if (response.data.success) {
        const dimensionsData = response.data.data;
        setDimensions(dimensionsData);
        
        // 按层次分组
        const grouped = dimensionsData.reduce((acc, dimension) => {
          const layer = dimension.layer || '其他';
          if (!acc[layer]) {
            acc[layer] = [];
          }
          acc[layer].push(dimension);
          return acc;
        }, {});
        
        setGroupedDimensions(grouped);
        console.log('🔧 Dimensions loaded successfully:', grouped);
      } else {
        message.error('加载维度数据失败');
      }
    } catch (error) {
      console.error('加载维度数据失败:', error);
      message.error('加载维度数据失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载已选择的标准配置
  const loadSelectedStandards = useCallback(async () => {
    try {
      console.log('🔧 Loading selected standards from:', `${API_BASE_URL}/standard-config`);
      const response = await api.get('/standard-config');
      
      if (response.data.success) {
        const allCategoryStandards = response.data.data;
        console.log('🔧 Loaded category standards:', allCategoryStandards);
        
        // 将所有分类的标准合并到一个数组中
        const allStandards = [];
        Object.keys(allCategoryStandards).forEach(category => {
          const categoryStandards = allCategoryStandards[category] || [];
          categoryStandards.forEach(standard => {
            allStandards.push({
              ...standard,
              category: category // 确保有分类信息
            });
          });
        });
        
        setSelectedStandards(allStandards);
        console.log('🔧 All selected standards loaded:', allStandards);
      } else {
        console.warn('加载已选择标准失败:', response.data.message);
        setSelectedStandards([]);
      }
    } catch (error) {
      console.error('加载已选择标准失败:', error);
      setSelectedStandards([]);
    }
  }, []);

  useEffect(() => {
    loadCategoryOptions();
    loadDimensions();
    loadSelectedStandards();
  }, [loadCategoryOptions, loadDimensions, loadSelectedStandards]);

  // 显示选择标准模态框
  const showSelectModal = () => {
    setModalVisible(true);
  };

  // 隐藏选择标准模态框
  const hideSelectModal = () => {
    setModalVisible(false);
  };

  // 查看维度详情
  const showDetailModal = (dimension) => {
    setViewingDimension(dimension);
    setDetailModalVisible(true);
  };

  // 隐藏详情模态框
  const hideDetailModal = () => {
    setDetailModalVisible(false);
    setViewingDimension(null);
  };

  // 处理标准选择
  const handleStandardSelection = (checkedValues, layer) => {
    const newSelected = selectedStandards.filter(item => item.layer !== layer);
    const layerDimensions = groupedDimensions[layer] || [];
    
    checkedValues.forEach(dimensionId => {
      const dimension = layerDimensions.find(d => d.id === dimensionId);
      if (dimension) {
        newSelected.push({
          ...dimension,
          category: activeTab // 记录选择时的分类
        });
      }
    });
    
    setSelectedStandards(newSelected);
  };

  // 保存选择的标准
  const handleSaveSelection = async () => {
    try {
      // 获取当前分类的已选择维度ID
      const currentCategoryStandards = selectedStandards.filter(s => s.category === activeTab);
      const dimensionIds = currentCategoryStandards.map(s => s.id);
      
      console.log('🔧 Saving standards for category:', activeTab, 'dimension_ids:', dimensionIds);
      
      const response = await api.post(`/standard-config/${activeTab}`, {
        dimension_ids: dimensionIds
      });
      
      if (response.data.success) {
        message.success(`${activeTab}分类的标准配置保存成功`);
        hideSelectModal();
        // 重新加载数据以确保状态同步
        await loadSelectedStandards();
        // 强制刷新UI状态
        setSelectedStandards(prevStandards => [...prevStandards]);
      } else {
        message.error('保存失败: ' + response.data.message);
      }
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败: ' + error.message);
    }
  };

  // 渲染评测标准
  const renderEvaluationCriteria = (criteria) => {
    if (!criteria || criteria.length === 0) {
      return <Text type="secondary">暂无评测标准</Text>;
    }

    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        {criteria.map((item, index) => (
          <div key={index} style={{ 
            padding: '8px 12px', 
            background: '#f5f5f5', 
            borderRadius: '4px',
            border: '1px solid #d9d9d9'
          }}>
            <Space>
              <Tag color="blue">{item.level}</Tag>
              <Text>{item.description}</Text>
              <Tag color="orange">{item.score}分</Tag>
            </Space>
          </div>
        ))}
      </Space>
    );
  };

  // 选择标准页面的列定义
  const selectionColumns = [
    {
      title: '选择',
      key: 'selection',
      width: 60,
      render: (_, record) => {
        // 检查当前维度是否已被当前分类选择
        const isSelected = selectedStandards.some(item => 
          item.id === record.id && item.category === activeTab
        );
        return (
          <Checkbox
            checked={isSelected}
            onChange={(e) => {
              if (e.target.checked) {
                // 添加到当前分类的选择中
                const newStandard = { ...record, category: activeTab };
                setSelectedStandards(prev => {
                  // 移除该维度在其他分类中的选择（如果存在）
                  const filtered = prev.filter(item => item.id !== record.id);
                  return [...filtered, newStandard];
                });
              } else {
                // 从当前分类的选择中移除
                setSelectedStandards(prev => 
                  prev.filter(item => !(item.id === record.id && item.category === activeTab))
                );
              }
            }}
          />
        );
      }
    },
    {
      title: '维度名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => showDetailModal(record)}
          >
            详情
          </Button>
        </Space>
      )
    },
    {
      title: '定义',
      dataIndex: 'definition',
      key: 'definition',
      ellipsis: {
        showTitle: false,
      },
      render: (text) => (
        <Tooltip title={text} placement="topLeft">
          <Text style={{ width: 200 }}>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => (
        <Tag color="geekblue">{category}</Tag>
      )
    },
    {
      title: '层次',
      dataIndex: 'layer',
      key: 'layer',
      width: 120,
      render: (layer) => (
        <Tag color="purple">{layer}</Tag>
      )
    }
  ];

  // 已选择标准的列定义
  const selectedColumns = [
    {
      title: '维度名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => showDetailModal(record)}
          >
            详情
          </Button>
        </Space>
      )
    },
    {
      title: '定义',
      dataIndex: 'definition',
      key: 'definition',
      ellipsis: {
        showTitle: false,
      },
      render: (text) => (
        <Tooltip title={text} placement="topLeft">
          <Text style={{ width: 200 }}>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => (
        <Tag color="geekblue">{category}</Tag>
      )
    },
    {
      title: '层次',
      dataIndex: 'layer',
      key: 'layer',
      width: 120,
      render: (layer) => (
        <Tag color="purple">{layer}</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_, record) => (
        <Button
          type="text"
          danger
          size="small"
          onClick={() => {
            setSelectedStandards(selectedStandards.filter(item => 
              !(item.id === record.id && item.category === record.category)
            ));
          }}
        >
          移除
        </Button>
      )
    }
  ];

  // 计算统计信息
  const getStatistics = (standards) => {
    if (!standards || standards.length === 0) {
      return { total: 0, layer1: 0, layer2: 0, layer3: 0, other: 0 };
    }
    
    const stats = {
      total: standards.length,
      layer1: standards.filter(s => s.layer === '第一层指标').length,
      layer2: standards.filter(s => s.layer === '第二层指标').length,
      layer3: standards.filter(s => s.layer === '第三层指标').length,
      other: standards.filter(s => s.layer === '其他服务场景').length
    };
    
    return stats;
  };

  // 按分类过滤已选择的标准
  const getSelectedStandardsByCategory = (category) => {
    return selectedStandards.filter(standard => standard.category === category);
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Title level={3}>
            <InfoCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            标准选择配置
          </Title>
          <Paragraph>
            从维度管理页面配置的维度中选择需要应用的评估标准。
            可以为每个二级分类选择不同层次的标准，支持多选。
          </Paragraph>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarExtraContent={
            <Space>
              <Button
                type="primary"
                icon={<CheckOutlined />}
                onClick={showSelectModal}
              >
                选择标准
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadDimensions}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          }
        >
          {categoryOptions.map(category => {
            const categoryStandards = getSelectedStandardsByCategory(category);
            const stats = getStatistics(categoryStandards);
            
            return (
              <TabPane
                tab={
                  <Space>
                    {category}
                    <Badge count={categoryStandards.length} showZero />
                  </Space>
                }
                key={category}
              >
                <div style={{ marginBottom: '16px' }}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="已选择标准"
                        value={stats.total}
                        prefix={<CheckCircleOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="第一层指标"
                        value={stats.layer1}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="第二层指标"
                        value={stats.layer2}
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="第三层指标"
                        value={stats.layer3}
                        valueStyle={{ color: '#faad14' }}
                      />
                    </Col>
                  </Row>
                </div>

                {categoryStandards.length === 0 ? (
                  <Alert
                    message="暂无选择的标准"
                    description={`${category}分类下还没有选择评估标准，请点击"选择标准"按钮进行选择。`}
                    type="info"
                    showIcon
                    style={{ marginTop: '16px' }}
                  />
                ) : (
                  <Table
                    columns={selectedColumns}
                    dataSource={categoryStandards}
                    rowKey="id"
                    loading={loading}
                    pagination={false}
                    size="middle"
                    bordered
                  />
                )}
              </TabPane>
            );
          })}
        </Tabs>
      </Card>

      {/* 选择标准模态框 */}
      <Modal
        title="选择评估标准"
        open={modalVisible}
        onOk={handleSaveSelection}
        onCancel={hideSelectModal}
        width={1200}
        okText="保存选择"
        cancelText="取消"
        style={{ top: 20 }}
      >
        <div style={{ marginBottom: '16px' }}>
          <Alert
            message="选择说明"
            description={`当前正在为"${activeTab}"分类选择评估标准。您可以从不同层次的维度中选择需要的标准，支持多选。`}
            type="info"
            showIcon
          />
        </div>

        <Collapse defaultActiveKey={layerOptions}>
          {layerOptions.map(layer => {
            const layerDimensions = groupedDimensions[layer] || [];
            const selectedInLayer = selectedStandards.filter(s => 
              s.layer === layer && s.category === activeTab
            );
            
            return (
              <Panel
                header={
                  <Space>
                    <Text strong>{layer}</Text>
                    <Badge count={layerDimensions.length} showZero style={{ backgroundColor: '#52c41a' }} />
                    <Text type="secondary">
                      已选择: {selectedInLayer.length}
                    </Text>
                  </Space>
                }
                key={layer}
              >
                {layerDimensions.length === 0 ? (
                  <Empty description={`${layer}暂无可选择的维度`} />
                ) : (
                  <Table
                    columns={selectionColumns}
                    dataSource={layerDimensions}
                    rowKey="id"
                    pagination={false}
                    size="small"
                  />
                )}
              </Panel>
            );
          })}
        </Collapse>
      </Modal>

      {/* 维度详情模态框 */}
      <Modal
        title="维度详情"
        open={detailModalVisible}
        onCancel={hideDetailModal}
        footer={[
          <Button key="close" onClick={hideDetailModal}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {viewingDimension && (
          <div>
            <Row gutter={16} style={{ marginBottom: '16px' }}>
              <Col span={12}>
                <Card size="small" title="基本信息">
                  <p><Text strong>维度名称：</Text>{viewingDimension.name}</p>
                  <p><Text strong>分类：</Text><Tag color="geekblue">{viewingDimension.category}</Tag></p>
                  <p><Text strong>层次：</Text><Tag color="purple">{viewingDimension.layer}</Tag></p>
                  <p><Text strong>状态：</Text>
                    {viewingDimension.is_active ? 
                      <Tag color="green">启用</Tag> : 
                      <Tag color="red">禁用</Tag>
                    }
                  </p>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="排序信息">
                  <p><Text strong>排序序号：</Text>{viewingDimension.sort_order}</p>
                  <p><Text strong>创建时间：</Text>{viewingDimension.created_at}</p>
                  <p><Text strong>更新时间：</Text>{viewingDimension.updated_at}</p>
                </Card>
              </Col>
            </Row>

            <Card size="small" title="维度定义" style={{ marginBottom: '16px' }}>
              <Paragraph>{viewingDimension.definition}</Paragraph>
            </Card>

            <Card size="small" title="评测标准" style={{ marginBottom: '16px' }}>
              {renderEvaluationCriteria(viewingDimension.evaluation_criteria)}
            </Card>

            {viewingDimension.examples && (
              <Card size="small" title="示例说明">
                <Paragraph>{viewingDimension.examples}</Paragraph>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default EvaluationStandardConfig; 