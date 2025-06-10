import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Table,
  Tag,
  Button,
  Select,
  Space,
  Typography,
  Empty,
  Tooltip,
  Modal,
  Statistic,
  Alert,
  message,
  Pagination
} from 'antd';
import {
  WarningOutlined,
  EyeOutlined,
  ReloadOutlined,
  FilterOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// 配置axios baseURL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 增加到3分钟超时，适应大模型长时间处理
  headers: {
    'Content-Type': 'application/json',
  },
});

const BadcaseManagement = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [badcaseData, setBadcaseData] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [filters, setFilters] = useState({
    badcase_type: 'all',
    classification_level2: null
  });
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // 动态分类选项
  const [categoryOptions, setCategoryOptions] = useState([]);
  
  // 用于存储当前的AbortController和防抖timeout
  const abortControllerRef = useRef(null);
  const debounceTimeoutRef = useRef(null);

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      // 取消所有进行中的请求
      abortControllerRef.current?.abort();
      // 清理防抖timeout
      clearTimeout(debounceTimeoutRef.current);
    };
  }, []);

  // 处理URL参数 - 使用防抖机制解决竞态条件
  useEffect(() => {
    const categoryFromUrl = searchParams.get('category');
    const badcaseTypeFromUrl = searchParams.get('badcase_type');
    
    // 清理之前的防抖timeout
    clearTimeout(debounceTimeoutRef.current);
    
    // 使用setTimeout进行防抖，确保所有参数更新完成后再执行
    debounceTimeoutRef.current = setTimeout(() => {
      setFilters(prev => {
        const newFilters = { ...prev };
        let hasChanges = false;
        
        // 处理分类参数
        if (categoryFromUrl && categoryFromUrl !== prev.classification_level2) {
          newFilters.classification_level2 = categoryFromUrl;
          hasChanges = true;
        }
        
        // 处理badcase类型参数
        if (badcaseTypeFromUrl && badcaseTypeFromUrl !== prev.badcase_type) {
          newFilters.badcase_type = badcaseTypeFromUrl;
          hasChanges = true;
        }
        
        return hasChanges ? newFilters : prev;
      });
    }, 50); // 50ms防抖延迟，确保URL参数解析完成
    
    // 清理函数已移至组件卸载清理中
  }, [searchParams]);

  // 获取badcase记录
  const fetchBadcaseRecords = useCallback(async (page = 1, pageSize = 20) => {
    try {
      setLoading(true);
      
      const params = {
        page,
        per_page: pageSize,
        badcase_type: filters.badcase_type === 'all' ? null : filters.badcase_type,
        classification_level2: filters.classification_level2
      };

      // 创建新的AbortController
      const newAbortController = new AbortController();
      
      // 取消旧请求
      abortControllerRef.current?.abort();
      
      // 存储新的AbortController
      abortControllerRef.current = newAbortController;
      
      const response = await api.get('/badcase-records', { 
        params,
        signal: newAbortController.signal 
      });
      
      if (response.data.success) {
        setBadcaseData(response.data.data.items);
        setPagination({
          current: response.data.data.pagination.page,
          pageSize: response.data.data.pagination.per_page,
          total: response.data.data.pagination.total
        });
      } else {
        message.error('获取Badcase记录失败');
      }
    } catch (error) {
      // 更精确地处理被取消的请求错误
      if (error.code === 'ERR_CANCELED' || error.name === 'AbortError' || error.message?.includes('canceled')) {
        // 请求被取消，不显示错误消息
        console.log('API请求被取消 - 这是正常的');
        return;
      }
      
      // 只有真正的错误才显示错误消息
      console.error('获取Badcase记录失败:', error);
      message.error('获取Badcase记录失败');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // 获取统计数据
  const fetchStatistics = useCallback(async () => {
    try {
      const response = await api.get('/badcase-statistics');
      
      if (response.data.success) {
        setStatistics(response.data.data);
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
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

  // 初始化数据（仅获取统计和分类数据，不获取记录）
  useEffect(() => {
    fetchStatistics();
    fetchCategories();
  }, [fetchStatistics, fetchCategories]);

  // 当筛选条件改变时重新获取数据
  useEffect(() => {
    fetchBadcaseRecords(1, pagination.pageSize);
  }, [filters, fetchBadcaseRecords, pagination.pageSize]);

  // 查看详情
  const handleViewDetail = (record) => {
    setSelectedRecord(record);
    setDetailModalVisible(true);
  };

  // 获取分数颜色
  const getScoreColor = (score) => {
    if (score >= 8) return '#52c41a';
    if (score >= 6) return '#1890ff';
    if (score >= 4) return '#faad14';
    return '#ff4d4f';
  };

  // 获取分数等级
  const getScoreLevel = (score) => {
    if (score >= 8) return { text: '优秀', color: 'success' };
    if (score >= 6) return { text: '良好', color: 'processing' };
    if (score >= 4) return { text: '一般', color: 'warning' };
    return { text: '差', color: 'error' };
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
      )
    },
    {
      title: '总分',
      dataIndex: 'total_score',
      key: 'total_score',
      width: 100,
      sorter: true,
      render: (score) => {
        const level = getScoreLevel(score);
        return (
          <Space direction="vertical" size={2}>
            <Text style={{ 
              color: getScoreColor(score),
              fontWeight: 'bold',
              fontSize: '16px'
            }}>
              {score}/10
            </Text>
            <Tag color={level.color} size="small">
              {level.text}
            </Tag>
          </Space>
        );
      }
    },
    {
      title: 'Badcase类型',
      key: 'badcase_type',
      width: 120,
      align: 'center',
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          {record.ai_is_badcase && (
            <Tag color="orange" size="small">
              🤖 AI判断
            </Tag>
          )}
          {record.human_is_badcase && (
            <Tag color="purple" size="small">
              👤 人工标记
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: 'Badcase原因',
      dataIndex: 'badcase_reason',
      key: 'badcase_reason',
      width: 200,
      ellipsis: {
        showTitle: false,
      },
      render: (text) => {
        if (!text) {
          return <Text type="secondary">无说明</Text>;
        }
        return (
          <Tooltip title={text} placement="topLeft">
            <Text style={{ width: 180, display: 'block' }}>
              {text.length > 30 ? `${text.substring(0, 30)}...` : text}
            </Text>
          </Tooltip>
        );
      }
    },
    {
      title: '创建时间',
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
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Tooltip title="查看详情">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          />
        </Tooltip>
      )
    }
  ];

  // 渲染统计信息
  const renderStatistics = () => {
    if (!statistics) return null;

    const { overall } = statistics;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="总Badcase数"
              value={overall.total_badcases}
              prefix={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="AI判断Badcase"
              value={overall.ai_badcases}
              suffix={`(${overall.ai_badcase_percentage}%)`}
              prefix="🤖"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="人工标记Badcase"
              value={overall.human_badcases}
              suffix={`(${overall.human_badcase_percentage}%)`}
              prefix="👤"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Badcase比例"
              value={overall.total_badcase_percentage}
              suffix="%"
              prefix={<WarningOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: overall.total_badcase_percentage > 15 ? '#ff4d4f' : overall.total_badcase_percentage > 5 ? '#faad14' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染详情模态框
  const renderDetailModal = () => (
    <Modal
      title="Badcase详情"
      open={detailModalVisible}
      onCancel={() => setDetailModalVisible(false)}
      width={900}
      footer={[
        <Button key="close" onClick={() => setDetailModalVisible(false)}>
          关闭
        </Button>
      ]}
    >
      {selectedRecord && (
        <div>
          <Row gutter={[16, 16]}>
            {/* Badcase信息 */}
            <Col span={24}>
              <Card 
                size="small" 
                title={
                  <Space>
                    <span style={{ fontSize: '16px' }}>🚨</span>
                    Badcase详细信息
                  </Space>
                }
                style={{
                  background: 'linear-gradient(135deg, #fff2f0 0%, #ffffff 100%)',
                  border: '1px solid #ffccc7'
                }}
              >
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Text strong>AI判断: </Text>
                    {selectedRecord.ai_is_badcase ? (
                      <Tag color="orange">Badcase</Tag>
                    ) : (
                      <Tag color="green">正常</Tag>
                    )}
                  </Col>
                  <Col span={8}>
                    <Text strong>人工标记: </Text>
                    {selectedRecord.human_is_badcase ? (
                      <Tag color="purple">Badcase</Tag>
                    ) : (
                      <Tag color="green">正常</Tag>
                    )}
                  </Col>
                  <Col span={8}>
                    <Text strong>总分: </Text>
                    <Text style={{ 
                      color: getScoreColor(selectedRecord.total_score),
                      fontWeight: 'bold'
                    }}>
                      {selectedRecord.total_score}/10
                    </Text>
                  </Col>
                  
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

            {/* 基本信息 */}
            <Col span={24}>
              <Card size="small" title="基本信息">
                <Row gutter={[16, 8]}>
                  <Col span={12}>
                    <Text strong>评估ID: </Text>
                    <Text>{selectedRecord.id}</Text>
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
                  <Col span={12}>
                    <Text strong>评估者: </Text>
                    <Text>{selectedRecord.human_evaluation_by || '系统自动'}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>

            {/* 问答内容 */}
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

            {/* 评分理由 */}
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
          </Row>
        </div>
      )}
    </Modal>
  );

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <WarningOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
          Badcase管理
        </Title>
        <Text type="secondary">
          查看和管理所有被标记为Badcase的评估记录
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
              placeholder="Badcase类型"
              style={{ width: '100%' }}
              value={filters.badcase_type}
              onChange={(value) => setFilters(prev => ({ ...prev, badcase_type: value }))}
            >
              <Option value="all">全部类型</Option>
              <Option value="ai">AI判断</Option>
              <Option value="human">人工标记</Option>
            </Select>
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
          <Col xs={24} sm={12} md={6}>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={() => {
                setFilters({
                  badcase_type: 'all',
                  classification_level2: null
                });
                fetchBadcaseRecords();
                fetchStatistics();
              }}
            >
              刷新
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 提示信息 */}
      {badcaseData.length > 0 && (
        <Alert
          message="Badcase记录说明"
          description="这些记录被标记为Badcase，表示AI回答质量存在问题。请仔细分析这些案例，找出改进的方向。"
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 数据表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={badcaseData}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ x: 1200 }}
          locale={{
            emptyText: (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无Badcase记录"
              />
            )
          }}
        />
        
        {/* 分页 */}
        {pagination.total > 0 && (
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Pagination
              current={pagination.current}
              pageSize={pagination.pageSize}
              total={pagination.total}
              showSizeChanger
              showQuickJumper
              showTotal={(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`}
              pageSizeOptions={['10', '20', '50', '100']}
              onChange={(page, pageSize) => {
                fetchBadcaseRecords(page, pageSize);
              }}
              onShowSizeChange={(current, size) => {
                fetchBadcaseRecords(1, size);
              }}
            />
          </div>
        )}
      </Card>

      {/* 详情模态框 */}
      {renderDetailModal()}
    </div>
  );
};

export default BadcaseManagement; 