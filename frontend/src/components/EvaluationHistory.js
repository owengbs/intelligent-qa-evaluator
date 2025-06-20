import React, { useState, useEffect, useCallback } from 'react';
import {
  Table,
  Card,
  Button,
  DatePicker,
  Select,
  Space,
  Tag,
  Modal,
  message,
  Popconfirm,
  Row,
  Col,
  Statistic,
  Typography,
  Tooltip,
  Empty,
  Spin,
  Image,
  Form,
  Input,
  InputNumber,
  Switch,
  Divider
} from 'antd';
import {
  EyeOutlined,
  DeleteOutlined,
  ReloadOutlined,
  FileTextOutlined,
  CalendarOutlined,
  FilterOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

// 配置axios - 使用环境变量中的API地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 增加到3分钟超时，适应大模型长时间处理
  headers: {
    'Content-Type': 'application/json',
  },
});

const EvaluationHistory = () => {
  const [loading, setLoading] = useState(false);
  const [historyData, setHistoryData] = useState([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [filters, setFilters] = useState({
    classification_level2: null,
    dateRange: null,
    searchText: ''
  });
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [statisticsData, setStatisticsData] = useState(null);
  const [statisticsLoading, setStatisticsLoading] = useState(false);
  
  // 编辑相关状态
  const [isEditing, setIsEditing] = useState(false);
  const [editForm] = Form.useForm();
  const [editData, setEditData] = useState(null);

  // 动态分类选项
  const [categoryOptions, setCategoryOptions] = useState([]);

  // 获取评估历史数据
  const fetchHistoryData = useCallback(async (page = 1, pageSize = 20) => {
    try {
      setLoading(true);
      
      const params = {
        page,
        per_page: pageSize,
        sort_by: 'created_at',
        sort_order: 'desc'
      };

      if (filters.classification_level2) {
        params.classification_level2 = filters.classification_level2;
      }

      if (filters.dateRange && filters.dateRange.length === 2) {
        params.start_date = filters.dateRange[0].startOf('day').toISOString();
        params.end_date = filters.dateRange[1].endOf('day').toISOString();
      }

      const response = await api.get('/evaluation-history', { params });
      
      if (response.data.success) {
        setHistoryData(response.data.data.items);
        setPagination({
          current: response.data.data.pagination.page,
          pageSize: response.data.data.pagination.per_page,
          total: response.data.data.pagination.total
        });
      } else {
        message.error('获取历史数据失败');
      }
    } catch (error) {
      console.error('获取历史数据失败:', error);
      message.error('获取历史数据失败');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      setStatisticsLoading(true);
      const response = await api.get('/evaluation-statistics');
      
      if (response.data.success) {
        setStatisticsData(response.data.data);
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
    } finally {
      setStatisticsLoading(false);
    }
  }, []);

  // 获取分类选项
  const fetchCategories = useCallback(async () => {
    try {
      const response = await api.get('/categories');
      
      if (response.data.success && response.data.data.categories) {
        setCategoryOptions(response.data.data.categories);
      }
    } catch (error) {
      console.error('获取分类选项失败:', error);
      // 如果API失败，使用默认分类
      setCategoryOptions([
        '个股决策', '个股分析', '事实检索', '客服咨询', '大盘行业分析', 
        '宏观经济分析', '知识咨询', '选股'
      ]);
    }
  }, []);

  // 初始化数据
  useEffect(() => {
    fetchHistoryData();
    fetchStatistics();
    fetchCategories();
  }, [fetchHistoryData, fetchStatistics, fetchCategories]);

  // 当筛选条件改变时重新获取数据
  useEffect(() => {
    fetchHistoryData(1, pagination.pageSize);
  }, [filters, fetchHistoryData, pagination.pageSize]);

  // 删除评估记录
  const handleDelete = async (historyId) => {
    try {
      const response = await api.delete(`/evaluation-history/${historyId}`);
      
      if (response.data.success) {
        message.success('删除成功');
        fetchHistoryData(pagination.current, pagination.pageSize);
        fetchStatistics(); // 刷新统计数据
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  // 查看详情
  const handleViewDetail = (record) => {
    setSelectedRecord(record);
    setDetailModalVisible(true);
    setIsEditing(false);
    setEditData(null);
  };

  // 开始编辑
  const handleStartEdit = () => {
    const initialData = {
      human_total_score: selectedRecord.human_total_score || 0,
      human_dimensions: selectedRecord.human_dimensions || {},
      human_is_badcase: selectedRecord.human_is_badcase || false,
      badcase_reason: selectedRecord.badcase_reason || ''
    };
    
    setEditData(initialData);
    setIsEditing(true);
    
    // 设置表单初值
    editForm.setFieldsValue(initialData);
  };

  // 取消编辑
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditData(null);
    editForm.resetFields();
  };

  // 保存编辑
  const handleSaveEdit = async (values) => {
    try {
      // 计算总分
      const dimensionScores = Object.values(values.human_dimensions || {});
      const totalScore = dimensionScores.reduce((sum, score) => sum + (score || 0), 0);
      
      const updateData = {
        ...values,
        human_total_score: totalScore
      };

      const response = await api.put(`/evaluation-history/${selectedRecord.id}/human-evaluation`, updateData);
      
      if (response.data.success) {
        message.success('更新成功');
        setIsEditing(false);
        setEditData(null);
        
        // 更新当前记录
        const updatedRecord = { ...selectedRecord, ...updateData };
        setSelectedRecord(updatedRecord);
        
        // 刷新列表数据
        fetchHistoryData(pagination.current, pagination.pageSize);
        fetchStatistics();
      } else {
        message.error('更新失败');
      }
    } catch (error) {
      console.error('更新失败:', error);
      message.error('更新失败');
    }
  };

  // 获取评分等级颜色
  const getScoreColor = (score) => {
    if (score >= 8) return '#52c41a';
    if (score >= 6) return '#1890ff';
    if (score >= 4) return '#faad14';
    return '#ff4d4f';
  };

  // 获取评分等级标签
  const getScoreLevel = (score) => {
    if (score >= 8) return { text: '优秀', color: 'success' };
    if (score >= 6) return { text: '良好', color: 'processing' };
    if (score >= 4) return { text: '一般', color: 'warning' };
    return { text: '需改进', color: 'error' };
  };

  // 获取维度标准配置
  const [standardsData, setStandardsData] = useState({});
  const [standardsLoading, setStandardsLoading] = useState(false);

  // 加载维度标准配置
  const fetchStandardsData = useCallback(async () => {
    try {
      setStandardsLoading(true);
      const response = await api.get('/standard-config');
      if (response.data.success) {
        setStandardsData(response.data.data);
      }
    } catch (error) {
      console.error('获取标准配置失败:', error);
    } finally {
      setStandardsLoading(false);
    }
  }, []);

  // 初始化时加载标准配置
  useEffect(() => {
    fetchStandardsData();
  }, [fetchStandardsData]);

  // 由于数据库已重构，直接显示维度名称，无需映射
  const getDimensionDisplayName = (dimensionKey, classification) => {
    // 数据库重构后，所有维度都已使用新维度体系保存
    // 直接返回原始维度名称即可
    return dimensionKey;
  };

  // 获取图片完整URL
  const getImageUrl = (imageUrl) => {
    if (!imageUrl) return '';
    
    // 如果已经是完整URL，直接返回
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return imageUrl;
    }
    
    // 如果是相对路径，拼接API地址
    if (imageUrl.startsWith('/api/')) {
      return `${API_BASE_URL.replace('/api', '')}${imageUrl}`;
    }
    
    // 默认返回原URL
    return imageUrl;
  };

  // 渲染图片历史组件
  const renderImageHistory = (images) => {
    if (!images || images.length === 0) {
      return (
        <div style={{ textAlign: 'center', padding: '16px', color: '#999' }}>
          <span>📷</span>
          <Text type="secondary"> 本次评估未使用图片</Text>
        </div>
      );
    }

    return (
      <div style={{ margin: '12px 0' }}>
        <Text strong style={{ color: '#1890ff', marginBottom: '8px', display: 'block' }}>
          📸 评估中使用的图片 ({images.length}张)
        </Text>
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '8px',
          maxHeight: '300px',
          overflowY: 'auto',
          padding: '8px',
          backgroundColor: '#fafafa',
          borderRadius: '6px',
          border: '1px solid #d9d9d9'
        }}>
          {images.map((image, index) => (
            <div key={image.id || index} style={{ position: 'relative' }}>
              <Image
                src={getImageUrl(image.previewUrl)}
                alt={image.name}
                width={100}
                height={100}
                style={{ 
                  objectFit: 'cover',
                  borderRadius: '4px',
                  border: '1px solid #d9d9d9',
                  cursor: 'pointer'
                }}
                preview={{
                  src: getImageUrl(image.previewUrl),
                  mask: (
                    <div style={{ textAlign: 'center' }}>
                      <EyeOutlined style={{ fontSize: '16px' }} />
                      <br />
                      <Text style={{ fontSize: '10px', color: 'white' }}>查看大图</Text>
                    </div>
                  )
                }}
                fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG8W+2V1JhQQzYEDHBOGGLkNHGBOOUEUKMLhD1YQhJW1YMcAV2gZLwBdgGBM4Y7QqKiQ3YCUNzFUtzuVJhw="
              />
              {image.ocrText && (
                <Tooltip 
                  title={
                    <div style={{ maxWidth: '300px' }}>
                      <Text strong style={{ color: '#fff' }}>OCR识别结果:</Text>
                      <br />
                      <Text style={{ color: '#fff' }}>
                        {image.ocrText.length > 200 
                          ? `${image.ocrText.substring(0, 200)}...` 
                          : image.ocrText
                        }
                      </Text>
                    </div>
                  }
                  placement="topLeft"
                >
                  <div style={{
                    position: 'absolute',
                    top: '-4px',
                    right: '-4px',
                    backgroundColor: '#52c41a',
                    borderRadius: '50%',
                    width: '20px',
                    height: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '12px',
                    color: 'white',
                    border: '2px solid white',
                    cursor: 'help'
                  }}>
                    ✓
                  </div>
                </Tooltip>
              )}
              <div style={{
                position: 'absolute',
                bottom: '2px',
                left: '2px',
                right: '2px',
                backgroundColor: 'rgba(0,0,0,0.7)',
                color: 'white',
                fontSize: '10px',
                padding: '2px 4px',
                borderRadius: '0 0 4px 4px',
                textAlign: 'center',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}>
                {image.name}
              </div>
            </div>
          ))}
        </div>
        
        {/* 图片统计信息 */}
        <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
          <Space split={<span>•</span>}>
            <span>总计 {images.length} 张图片</span>
            <span>已识别 {images.filter(img => img.ocrText).length} 张</span>
            <span>总大小 {(images.reduce((sum, img) => sum + (img.size || 0), 0) / 1024 / 1024).toFixed(2)} MB</span>
          </Space>
        </div>
      </div>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: true
    },
    {
      title: '用户问题',
      dataIndex: 'user_input',
      key: 'user_input',
      width: 300,
      ellipsis: {
        showTitle: false,
      },
      render: (text) => (
        <Tooltip title={text} placement="topLeft">
          <Text style={{ width: 280, display: 'block' }}>
            {text && text.length > 50 ? `${text.substring(0, 50)}...` : text}
          </Text>
        </Tooltip>
      )
    },
    {
      title: '分类',
      dataIndex: 'classification_level2',
      key: 'classification_level2',
      width: 120,
      render: (text) => (
        <Tag color="blue">{text || '未分类'}</Tag>
      ),
      filters: categoryOptions.map(cat => ({ text: cat, value: cat })),
      onFilter: (value, record) => record.classification_level2 === value
    },
    {
      title: '总分',
      dataIndex: 'human_total_score',
      key: 'total_score',
      width: 120,
      sorter: true,
      render: (humanScore, record) => {
        // 优先显示人工评分，没有则显示AI评分
        const displayScore = humanScore !== null && humanScore !== undefined ? humanScore : record.total_score;
        const isHumanScore = humanScore !== null && humanScore !== undefined;
        const level = getScoreLevel(displayScore);
        
        return (
          <Space direction="vertical" size={2}>
            <Space>
              <Text style={{ 
                color: getScoreColor(displayScore),
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                {displayScore}/10
              </Text>
              {isHumanScore && (
                <Text style={{ fontSize: '12px', color: '#722ed1' }}>👨‍💼</Text>
              )}
              {!isHumanScore && (
                <Text style={{ fontSize: '12px', color: '#1890ff' }}>🤖</Text>
              )}
            </Space>
            <Tag color={level.color} size="small">
              {level.text}
            </Tag>
          </Space>
        );
      }
    },
    {
      title: 'Badcase状态',
      dataIndex: 'is_badcase',
      key: 'badcase_status',
      width: 120,
      align: 'center',
      render: (isBadcase, record) => {
        if (isBadcase) {
          return (
            <Space direction="vertical" size={2}>
              <Tag color="red" style={{ fontSize: '12px' }}>
                🚨 Badcase
              </Tag>
              <div style={{ fontSize: '10px' }}>
                {record.ai_is_badcase && (
                  <Tag color="orange" size="small">AI</Tag>
                )}
                {record.human_is_badcase && (
                  <Tag color="purple" size="small">人工</Tag>
                )}
              </div>
            </Space>
          );
        } else {
          return (
            <Tag color="green" size="small">
              ✅ 正常
            </Tag>
          );
        }
      },
      filters: [
        { text: '正常记录', value: false },
        { text: 'Badcase', value: true }
      ],
      onFilter: (value, record) => record.is_badcase === value
    },
    {
      title: '维度评分',
      dataIndex: 'human_dimensions',
      key: 'dimensions',
      width: 280,
      render: (humanDimensions, record) => {
        // 优先显示人工维度评分，没有则显示AI维度评分
        const displayDimensions = (humanDimensions && Object.keys(humanDimensions).length > 0) 
          ? humanDimensions 
          : record.dimensions;
        const isHumanDimensions = humanDimensions && Object.keys(humanDimensions).length > 0;
        
        if (!displayDimensions || Object.keys(displayDimensions).length === 0) {
          return <Text type="secondary">无维度数据</Text>;
        }
        
        return (
          <div style={{ lineHeight: '1.2' }}>
            <Space wrap size={4} style={{ marginBottom: '4px' }}>
              {Object.entries(displayDimensions).map(([key, value]) => (
                <Tag 
                  key={key} 
                  size="small"
                  color={isHumanDimensions ? 'purple' : 'blue'}
                  style={{ margin: '1px' }}
                >
                  {getDimensionDisplayName(key, record.classification_level2)}: {value}
                </Tag>
              ))}
            </Space>
            <div>
              <Text style={{ fontSize: '10px', color: '#666' }}>
                {isHumanDimensions ? '👨‍💼 人工评分' : '🤖 AI评分'}
              </Text>
            </div>
          </div>
        );
      }
    },
    {
      title: '评估状态',
      dataIndex: 'human_total_score',
      key: 'evaluation_status',
      width: 100,
      align: 'center',
      render: (humanScore, record) => {
        const hasHumanScore = humanScore !== null && humanScore !== undefined;
        const hasHumanDimensions = record.human_dimensions && Object.keys(record.human_dimensions).length > 0;
        
        if (hasHumanScore || hasHumanDimensions) {
          return (
            <Tag color="purple" size="small">
              👨‍💼 人工评估
            </Tag>
          );
        } else {
          return (
            <Tag color="blue" size="small">
              🤖 AI评估
            </Tag>
          );
        }
      },
      filters: [
        { text: '人工评估', value: 'human' },
        { text: 'AI评估', value: 'ai' }
      ],
      onFilter: (value, record) => {
        const hasHuman = (record.human_total_score !== null && record.human_total_score !== undefined) ||
                        (record.human_dimensions && Object.keys(record.human_dimensions).length > 0);
        return value === 'human' ? hasHuman : !hasHuman;
      }
    },
    {
      title: '评估时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      sorter: true,
      render: (text) => {
        const date = new Date(text);
        return (
          <Space direction="vertical" size={2}>
            <Text>{date.toLocaleDateString()}</Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {date.toLocaleTimeString()}
            </Text>
          </Space>
        );
      }
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description="确定要删除这条评估记录吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  // 处理表格变化
  const handleTableChange = (paginationConfig, filters, sorter) => {
    fetchHistoryData(paginationConfig.current, paginationConfig.pageSize);
  };

  // 渲染统计卡片
  const renderStatistics = () => {
    if (statisticsLoading) {
      return <Spin />;
    }

    if (!statisticsData) {
      return null;
    }

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总评估数"
              value={statisticsData.total_evaluations}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="分类数量"
              value={statisticsData.classification_stats ? statisticsData.classification_stats.length : 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="平均分数"
              value={statisticsData.classification_stats ? 
                (statisticsData.classification_stats.reduce((sum, item) => sum + item.avg_score, 0) / 
                 statisticsData.classification_stats.length).toFixed(1) : 0
              }
              suffix="/ 10"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="最近7天"
              value={statisticsData.recent_trend ? statisticsData.recent_trend.length : 0}
              suffix="天有评估"
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染详情模态框
  const renderDetailModal = () => (
    <Modal
      title={isEditing ? "编辑评估结果" : "评估详情"}
      open={detailModalVisible}
      onCancel={() => {
        setDetailModalVisible(false);
        handleCancelEdit();
      }}
      width={1000}
      footer={
        isEditing ? [
          <Button key="cancel" onClick={handleCancelEdit}>
            取消
          </Button>,
          <Button key="save" type="primary" onClick={() => editForm.submit()}>
            保存
          </Button>
        ] : [
          <Button key="edit" type="primary" onClick={handleStartEdit}>
            编辑评估
          </Button>,
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]
      }
    >
      {selectedRecord && (
        <div>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card size="small" title="基本信息">
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>评估ID: </Text>
                    <Text>{selectedRecord.id}</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>总分: </Text>
                    <Text style={{ 
                      color: getScoreColor(selectedRecord.total_score),
                      fontWeight: 'bold',
                      fontSize: '16px'
                    }}>
                      {selectedRecord.total_score}/10
                    </Text>
                    <Tag color={getScoreLevel(selectedRecord.total_score).color} style={{ marginLeft: 8 }}>
                      {getScoreLevel(selectedRecord.total_score).text}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>分类: </Text>
                    <Tag color="blue">
                      {selectedRecord.classification_level1} → {selectedRecord.classification_level2}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>评估时间: </Text>
                    <Text>{new Date(selectedRecord.created_at).toLocaleString()}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>

            <Col span={24}>
              <Card size="small" title="问答内容">
                <Space direction="vertical" style={{ width: '100%' }} size={16}>
                  <div>
                    <Text strong style={{ color: '#1890ff' }}>用户问题:</Text>
                    <Paragraph style={{ 
                      marginTop: 8,
                      padding: '12px',
                      background: '#f0f9ff',
                      borderRadius: '6px',
                      border: '1px solid #e6f7ff'
                    }}>
                      {selectedRecord.user_input}
                    </Paragraph>
                  </div>
                  
                  <div>
                    <Text strong style={{ color: '#52c41a' }}>模型回答:</Text>
                    <Paragraph style={{ 
                      marginTop: 8,
                      padding: '12px',
                      background: '#f6ffed',
                      borderRadius: '6px',
                      border: '1px solid #d9f7be'
                    }}>
                      {selectedRecord.model_answer}
                    </Paragraph>
                  </div>
                  
                  {selectedRecord.reference_answer && (
                    <div>
                      <Text strong style={{ color: '#faad14' }}>参考答案:</Text>
                      <Paragraph style={{ 
                        marginTop: 8,
                        padding: '12px',
                        background: '#fffbe6',
                        borderRadius: '6px',
                        border: '1px solid #ffe58f'
                      }}>
                        {selectedRecord.reference_answer}
                      </Paragraph>
                    </div>
                  )}
                </Space>
              </Card>
            </Col>

            {/* 图片历史展示 */}
            <Col span={24}>
              <Card size="small" title="上传图片">
                {renderImageHistory(selectedRecord.uploaded_images)}
              </Card>
            </Col>

            {selectedRecord.dimensions && Object.keys(selectedRecord.dimensions).length > 0 && (
              <Col span={24}>
                <Card size="small" title="维度评分详情">
                  <Row gutter={[16, 16]}>
                    {Object.entries(selectedRecord.dimensions).map(([key, value]) => (
                      <Col xs={24} sm={12} md={6} key={key}>
                        <Card
                          size="small"
                          style={{
                            background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)',
                            border: '1px solid #e8f4fd',
                            borderRadius: '8px'
                          }}
                        >
                          <div style={{ textAlign: 'center' }}>
                            <Text strong style={{ color: '#1890ff' }}>
                              {getDimensionDisplayName(key, selectedRecord.classification_level2)}
                            </Text>
                            <div style={{ marginTop: 8 }}>
                              <Text style={{ 
                                fontSize: '18px', 
                                fontWeight: 'bold',
                                color: getScoreColor(value * 2.5) // 假设最大分数为4，转换为10分制
                              }}>
                                {value}
                              </Text>
                            </div>
                          </div>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            )}

            <Col span={24}>
              <Card size="small" title="评分理由">
                <Paragraph style={{ 
                  whiteSpace: 'pre-line',
                  lineHeight: 1.6,
                  padding: '12px',
                  background: '#fafafa',
                  borderRadius: '6px'
                }}>
                  {selectedRecord.reasoning}
                </Paragraph>
              </Card>
            </Col>

            {/* Badcase信息 */}
            <Col span={24}>
              <Card 
                size="small" 
                title={
                  <Space>
                    {selectedRecord.is_badcase ? (
                      <>
                        <span style={{ fontSize: '16px' }}>🚨</span>
                        Badcase标记信息
                      </>
                    ) : (
                      <>
                        <span style={{ fontSize: '16px' }}>✅</span>
                        质量评估正常
                      </>
                    )}
                  </Space>
                }
                style={{
                  background: selectedRecord.is_badcase 
                    ? 'linear-gradient(135deg, #fff2f0 0%, #ffffff 100%)' 
                    : 'linear-gradient(135deg, #f6ffed 0%, #ffffff 100%)',
                  border: selectedRecord.is_badcase 
                    ? '1px solid #ffccc7' 
                    : '1px solid #d9f7be'
                }}
              >
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Text strong>总体状态: </Text>
                    {selectedRecord.is_badcase ? (
                      <Tag color="red" style={{ fontSize: '12px' }}>
                        🚨 Badcase
                      </Tag>
                    ) : (
                      <Tag color="green" style={{ fontSize: '12px' }}>
                        ✅ 正常
                      </Tag>
                    )}
                  </Col>
                  <Col span={8}>
                    <Text strong>AI判断: </Text>
                    {selectedRecord.ai_is_badcase ? (
                      <Tag color="orange" style={{ fontSize: '12px' }}>
                        Badcase
                      </Tag>
                    ) : (
                      <Tag color="green" style={{ fontSize: '12px' }}>
                        正常
                      </Tag>
                    )}
                  </Col>
                  <Col span={8}>
                    <Text strong>人工标记: </Text>
                    {selectedRecord.human_is_badcase ? (
                      <Tag color="purple" style={{ fontSize: '12px' }}>
                        Badcase
                      </Tag>
                    ) : (
                      <Tag color="green" style={{ fontSize: '12px' }}>
                        正常
                      </Tag>
                    )}
                  </Col>
                  
                  {/* Badcase原因说明 */}
                  {selectedRecord.badcase_reason && (
                    <Col span={24}>
                      <Text strong style={{ color: '#ff4d4f' }}>Badcase原因:</Text>
                      <Paragraph style={{ 
                        marginTop: 8,
                        padding: '12px',
                        background: '#fff2f0',
                        borderRadius: '6px',
                        border: '1px solid #ffccc7',
                        whiteSpace: 'pre-line',
                        lineHeight: 1.6
                      }}>
                        {selectedRecord.badcase_reason}
                      </Paragraph>
                    </Col>
                  )}
                </Row>
              </Card>
            </Col>

            {/* 人工评估信息 */}
            {(selectedRecord.human_total_score !== null && selectedRecord.human_total_score !== undefined || isEditing) && (
              <Col span={24}>
                <Card 
                  size="small" 
                  title={
                    <Space>
                      <span style={{ fontSize: '16px' }}>👨‍💼</span>
                      人工评估结果
                    </Space>
                  }
                  style={{
                    background: 'linear-gradient(135deg, #f0f2ff 0%, #ffffff 100%)',
                    border: '1px solid #d6e4ff'
                  }}
                                >
                  {isEditing ? (
                    <Form
                      form={editForm}
                      layout="vertical"
                      onFinish={handleSaveEdit}
                      initialValues={editData}
                    >
                      <Row gutter={[16, 16]}>
                        {/* 维度评分编辑 */}
                        <Col span={24}>
                          <Text strong style={{ color: '#1890ff', marginBottom: 16, display: 'block' }}>
                            维度评分:
                          </Text>
                          <Row gutter={[12, 12]}>
                            {Object.keys(selectedRecord.dimensions || {}).map((dimensionKey) => (
                              <Col xs={12} sm={8} md={6} key={dimensionKey}>
                                <Form.Item
                                  name={['human_dimensions', dimensionKey]}
                                  label={getDimensionDisplayName(dimensionKey, selectedRecord.classification_level2)}
                                  rules={[
                                    { required: true, message: '请输入评分' },
                                    { type: 'number', min: 0, max: 5, message: '评分范围0-5' }
                                  ]}
                                >
                                  <InputNumber
                                    min={0}
                                    max={5}
                                    step={0.1}
                                    precision={1}
                                    style={{ width: '100%' }}
                                    placeholder="0-5分"
                                  />
                                </Form.Item>
                              </Col>
                            ))}
                          </Row>
                        </Col>

                        {/* Badcase标记编辑 */}
                        <Col span={24}>
                          <Divider />
                          <Row gutter={[16, 16]}>
                            <Col span={12}>
                              <Form.Item
                                name="human_is_badcase"
                                label="Badcase标记"
                                valuePropName="checked"
                              >
                                <Switch
                                  checkedChildren="是Badcase"
                                  unCheckedChildren="正常"
                                />
                              </Form.Item>
                            </Col>
                            <Col span={12}>
                              <Form.Item
                                name="badcase_reason"
                                label="Badcase原因"
                                rules={[
                                  {
                                    validator: (_, value) => {
                                      const isBadcase = editForm.getFieldValue('human_is_badcase');
                                      if (isBadcase && !value) {
                                        return Promise.reject('标记为Badcase时必须填写原因');
                                      }
                                      return Promise.resolve();
                                    }
                                  }
                                ]}
                              >
                                <Input.TextArea
                                  placeholder="请详细说明Badcase的具体原因..."
                                  rows={3}
                                  disabled={!editForm.getFieldValue('human_is_badcase')}
                                />
                              </Form.Item>
                            </Col>
                          </Row>
                        </Col>
                      </Row>
                    </Form>
                  ) : (
                    <Row gutter={[16, 16]}>
                      <Col span={12}>
                        <Text strong>人工评估总分: </Text>
                        <Text style={{ 
                          color: getScoreColor(selectedRecord.human_total_score),
                          fontWeight: 'bold',
                          fontSize: '18px'
                        }}>
                          {selectedRecord.human_total_score}/10
                        </Text>
                        <Tag color={getScoreLevel(selectedRecord.human_total_score).color} style={{ marginLeft: 8 }}>
                          {getScoreLevel(selectedRecord.human_total_score).text}
                        </Tag>
                      </Col>
                    <Col span={12}>
                      <Text strong>评估者: </Text>
                      <Text>{selectedRecord.evaluator_name || '评估专家'}</Text>
                    </Col>
                    <Col span={12}>
                      <Text strong>人工评估时间: </Text>
                      <Text>
                        {selectedRecord.human_evaluation_time ? 
                          new Date(selectedRecord.human_evaluation_time).toLocaleString() : 
                          '未记录'
                        }
                      </Text>
                    </Col>
                    <Col span={12}>
                      <Text strong>评分差异: </Text>
                      <Text style={{ 
                        color: Math.abs(selectedRecord.human_total_score - selectedRecord.total_score) > 1 ? '#ff4d4f' : '#52c41a',
                        fontWeight: 'bold'
                      }}>
                        {selectedRecord.human_total_score > selectedRecord.total_score ? '+' : ''}
                        {(selectedRecord.human_total_score - selectedRecord.total_score).toFixed(1)}
                      </Text>
                    </Col>
                    
                    {/* 人工维度评分 */}
                    {selectedRecord.human_dimensions && Object.keys(selectedRecord.human_dimensions).length > 0 && (
                      <Col span={24}>
                        <Text strong style={{ color: '#1890ff' }}>人工维度评分:</Text>
                        <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
                          {Object.entries(selectedRecord.human_dimensions).map(([key, value]) => {
                            const aiScore = selectedRecord.dimensions ? selectedRecord.dimensions[key] : null;
                            const diff = aiScore !== null ? (value - aiScore).toFixed(1) : null;
                            
                            return (
                              <Col xs={12} sm={8} md={6} key={key}>
                                <div style={{
                                  padding: '8px',
                                  background: '#f8f9fa',
                                  borderRadius: '4px',
                                  border: '1px solid #e9ecef'
                                }}>
                                  <Text strong style={{ fontSize: '12px' }}>
                                    {getDimensionDisplayName(key, selectedRecord.classification_level2)}
                                  </Text>
                                  <div>
                                    <Text style={{ color: getScoreColor(value * 2.5) }}>
                                      👨‍💼 {value}
                                    </Text>
                                    {aiScore !== null && (
                                      <>
                                        <Text type="secondary"> vs </Text>
                                        <Text style={{ color: getScoreColor(aiScore * 2.5) }}>
                                          🤖 {aiScore}
                                        </Text>
                                        {diff !== null && (
                                          <Text style={{ 
                                            color: Math.abs(diff) > 0.5 ? '#ff4d4f' : '#52c41a',
                                            fontSize: '11px',
                                            marginLeft: 4
                                          }}>
                                            ({diff > 0 ? '+' : ''}{diff})
                                          </Text>
                                        )}
                                      </>
                                    )}
                                  </div>
                                </div>
                              </Col>
                            );
                          })}
                        </Row>
                      </Col>
                    )}
                    
                    {/* 人工评估意见 */}
                    {selectedRecord.human_reasoning && (
                      <Col span={24}>
                        <Text strong style={{ color: '#1890ff' }}>人工评估意见:</Text>
                        <Paragraph style={{ 
                          marginTop: 8,
                          padding: '12px',
                          background: '#f0f2ff',
                          borderRadius: '6px',
                          border: '1px solid #d6e4ff',
                          whiteSpace: 'pre-line',
                          lineHeight: 1.6
                        }}>
                          {selectedRecord.human_reasoning}
                        </Paragraph>
                      </Col>
                    )}
                    </Row>
                  )}
                </Card>
              </Col>
            )}
          </Row>
        </div>
      )}
    </Modal>
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <FileTextOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          评估历史管理
        </Title>
        <Text type="secondary">
          查看和管理所有历史评估记录，支持按分类、时间等条件筛选
        </Text>
      </div>

      {/* 统计信息 */}
      {renderStatistics()}

      {/* 筛选控件 */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Space>
              <FilterOutlined />
              <Text strong>筛选条件:</Text>
            </Space>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="选择分类"
              style={{ width: '100%' }}
              allowClear
              value={filters.classification_level2}
              onChange={(value) => setFilters(prev => ({ ...prev, classification_level2: value }))}
            >
              {categoryOptions.map(option => (
                <Option key={option} value={option}>
                  {option}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              value={filters.dateRange}
              onChange={(dates) => setFilters(prev => ({ ...prev, dateRange: dates }))}
              placeholder={['开始日期', '结束日期']}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={() => {
                setFilters({
                  classification_level2: null,
                  dateRange: null,
                  searchText: ''
                });
                fetchHistoryData();
                fetchStatistics();
              }}
            >
              刷新
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={historyData}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            pageSizeOptions: ['10', '20', '50', '100']
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无评估记录"
              />
            )
          }}
        />
      </Card>

      {/* 详情模态框 */}
      {renderDetailModal()}
    </div>
  );
};

export default EvaluationHistory; 