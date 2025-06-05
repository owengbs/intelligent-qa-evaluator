import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import axios from 'axios';

// 配置API基础URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const { TabPane } = Tabs;
const { TextArea } = Input;
const { Option } = Select;
const { Title, Text, Paragraph } = Typography;

const EvaluationStandardConfig = () => {
  const [loading, setLoading] = useState(false);
  const [groupedStandards, setGroupedStandards] = useState({});
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStandard, setEditingStandard] = useState(null);
  const [activeTab, setActiveTab] = useState('选股');
  const [form] = Form.useForm();

  // 二级分类选项
  const categoryOptions = [
    '选股',
    '宏观经济分析',
    '大盘行业分析',
    '个股分析',
    '个股决策',
    '信息查询',
    '无效问题'
  ];

  // 加载评估标准
  const loadEvaluationStandards = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/evaluation-standards/grouped');
      if (response.data.success) {
        setGroupedStandards(response.data.data);
        
        // 如果当前活动标签页没有数据，切换到第一个有数据的标签页
        if (!response.data.data[activeTab] && response.data.categories.length > 0) {
          setActiveTab(response.data.categories[0]);
        }
      }
    } catch (error) {
      console.error('加载评估标准失败:', error);
      message.error('加载评估标准失败');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadEvaluationStandards();
  }, [loadEvaluationStandards]);

  // 显示新增/编辑模态框
  const showModal = (standard = null) => {
    setEditingStandard(standard);
    setModalVisible(true);
    
    if (standard) {
      form.setFieldsValue(standard);
    } else {
      form.resetFields();
      form.setFieldsValue({
        level2_category: activeTab,
        max_score: 3
      });
    }
  };

  // 隐藏模态框
  const hideModal = () => {
    setModalVisible(false);
    setEditingStandard(null);
    form.resetFields();
  };

  // 保存评估标准
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingStandard) {
        // 更新现有标准
        await api.put(`/evaluation-standards/${editingStandard.id}`, values);
        message.success('评估标准更新成功');
      } else {
        // 创建新标准
        await api.post('/evaluation-standards', values);
        message.success('评估标准创建成功');
      }
      
      hideModal();
      loadEvaluationStandards();
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error('保存失败');
      }
    }
  };

  // 删除评估标准
  const handleDelete = async (id) => {
    try {
      await api.delete(`/evaluation-standards/${id}`);
      message.success('评估标准删除成功');
      loadEvaluationStandards();
    } catch (error) {
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error('删除失败');
      }
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '评估维度',
      dataIndex: 'dimension',
      key: 'dimension',
      width: 120,
      render: (text, record) => (
        <Space>
          <Tag color={record.is_default ? 'blue' : 'green'}>
            {text}
          </Tag>
          {record.is_default && (
            <Tooltip title="系统默认标准">
              <CheckCircleOutlined style={{ color: '#1890ff' }} />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '参考标准',
      dataIndex: 'reference_standard',
      key: 'reference_standard',
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
      title: '打分原则',
      dataIndex: 'scoring_principle',
      key: 'scoring_principle',
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
      title: '最高分',
      dataIndex: 'max_score',
      key: 'max_score',
      width: 80,
      align: 'center',
      render: (score) => (
        <Tag color="orange">{score}分</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => showModal(record)}
            />
          </Tooltip>
          {!record.is_default && (
            <Tooltip title="删除">
              <Popconfirm
                title="确定要删除这个评估标准吗？"
                onConfirm={() => handleDelete(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                />
              </Popconfirm>
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // 计算统计信息
  const getStatistics = (standards) => {
    if (!standards || standards.length === 0) {
      return { total: 0, totalScore: 0, defaultCount: 0, customCount: 0 };
    }
    
    const total = standards.length;
    const totalScore = standards.reduce((sum, item) => sum + item.max_score, 0);
    const defaultCount = standards.filter(item => item.is_default).length;
    const customCount = total - defaultCount;
    
    return { total, totalScore, defaultCount, customCount };
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Title level={3}>
            <InfoCircleOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
            评估标准配置
          </Title>
          <Paragraph>
            为每个二级分类配置专属的评估标准，包括评估维度、参考标准和打分原则。
            系统提供默认标准，您也可以添加自定义标准。
          </Paragraph>
        </div>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabBarExtraContent={
            <Space>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => showModal()}
              >
                新增标准
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadEvaluationStandards}
                loading={loading}
              >
                刷新
              </Button>
            </Space>
          }
        >
          {categoryOptions.map(category => {
            const standards = groupedStandards[category] || [];
            const stats = getStatistics(standards);
            
            return (
              <TabPane
                tab={
                  <Space>
                    {category}
                    <Tag>{standards.length}</Tag>
                  </Space>
                }
                key={category}
              >
                <div style={{ marginBottom: '16px' }}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="评估标准数量"
                        value={stats.total}
                        prefix={<CheckCircleOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="总分值"
                        value={stats.totalScore}
                        suffix="分"
                        prefix={<WarningOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="默认标准"
                        value={stats.defaultCount}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="自定义标准"
                        value={stats.customCount}
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </Col>
                  </Row>
                </div>

                {standards.length === 0 ? (
                  <Alert
                    message="暂无评估标准"
                    description={`${category}分类下还没有配置评估标准，请添加。`}
                    type="info"
                    showIcon
                    style={{ marginTop: '16px' }}
                  />
                ) : (
                  <Table
                    columns={columns}
                    dataSource={standards}
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

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingStandard ? '编辑评估标准' : '新增评估标准'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={hideModal}
        width={600}
        okText="保存"
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            max_score: 3
          }}
        >
          <Form.Item
            name="level2_category"
            label="二级分类"
            rules={[{ required: true, message: '请选择二级分类' }]}
          >
            <Select placeholder="选择二级分类">
              {categoryOptions.map(option => (
                <Option key={option} value={option}>
                  {option}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="dimension"
            label="评估维度"
            rules={[{ required: true, message: '请输入评估维度' }]}
          >
            <Input placeholder="如：准确性、完整性、相关性等" />
          </Form.Item>

          <Form.Item
            name="reference_standard"
            label="参考标准"
            rules={[{ required: true, message: '请输入参考标准' }]}
          >
            <TextArea
              rows={3}
              placeholder="描述该维度的具体评估标准和要求"
            />
          </Form.Item>

          <Form.Item
            name="scoring_principle"
            label="打分原则"
            rules={[{ required: true, message: '请输入打分原则' }]}
          >
            <TextArea
              rows={3}
              placeholder="详细说明评分规则，如：0-4分：完全符合=4分；部分符合=2分；完全不符=0分"
            />
          </Form.Item>

          <Form.Item
            name="max_score"
            label="最高分数"
            rules={[
              { required: true, message: '请输入最高分数' },
              { type: 'number', min: 1, max: 10, message: '分数范围应在1-10之间' }
            ]}
          >
            <InputNumber
              min={1}
              max={10}
              placeholder="最高分数"
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EvaluationStandardConfig; 