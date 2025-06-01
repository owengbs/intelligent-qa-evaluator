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
  Spin
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

// 配置axios
const api = axios.create({
  timeout: 30000,
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

  // 分类选项
  const categoryOptions = [
    '选股', '宏观经济分析', '大盘行业分析', '个股分析', '个股决策', '信息查询', '无效问题'
  ];

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

      const response = await api.get('/api/evaluation-history', { params });
      
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
      const response = await api.get('/api/evaluation-statistics');
      
      if (response.data.success) {
        setStatisticsData(response.data.data);
      }
    } catch (error) {
      console.error('获取统计数据失败:', error);
    } finally {
      setStatisticsLoading(false);
    }
  }, []);

  // 初始化数据
  useEffect(() => {
    fetchHistoryData();
    fetchStatistics();
  }, [fetchHistoryData, fetchStatistics]);

  // 当筛选条件改变时重新获取数据
  useEffect(() => {
    fetchHistoryData(1, pagination.pageSize);
  }, [filters, fetchHistoryData, pagination.pageSize]);

  // 删除评估记录
  const handleDelete = async (historyId) => {
    try {
      const response = await api.delete(`/api/evaluation-history/${historyId}`);
      
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

  // 维度显示名称映射
  const dimensionNames = {
    accuracy: '准确性',
    completeness: '完整性',
    fluency: '流畅性',
    safety: '安全性',
    relevance: '相关性',
    clarity: '清晰度',
    timeliness: '时效性',
    usability: '可用性',
    compliance: '合规性'
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
      title: '维度评分',
      dataIndex: 'dimensions',
      key: 'dimensions',
      width: 200,
      render: (dimensions) => {
        if (!dimensions || Object.keys(dimensions).length === 0) {
          return <Text type="secondary">无维度数据</Text>;
        }
        
        return (
          <Space wrap size={4}>
            {Object.entries(dimensions).slice(0, 3).map(([key, value]) => (
              <Tag key={key} size="small">
                {dimensionNames[key] || key}: {value}
              </Tag>
            ))}
            {Object.keys(dimensions).length > 3 && (
              <Tag size="small">+{Object.keys(dimensions).length - 3}</Tag>
            )}
          </Space>
        );
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
      title="评估详情"
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
                              {dimensionNames[key] || key}
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