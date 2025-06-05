import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  Popconfirm,
  message,
  Alert,
  Tooltip,
  Tag,
  Divider,
  Typography,
  Row,
  Col,
  Statistic,
  Badge
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  SettingOutlined,
  ExportOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

// 配置axios baseURL - 使用环境变量中的API地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const ClassificationConfig = () => {
  const [standards, setStandards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStandard, setEditingStandard] = useState(null);
  const [form] = Form.useForm();
  const [statistics, setStatistics] = useState({});

  // 加载分类标准
  const loadClassificationStandards = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/classification-standards');
      setStandards(response.data.standards || []);
      
      // 计算统计信息
      const stats = calculateStatistics(response.data.standards || []);
      setStatistics(stats);
      
      message.success('分类标准加载成功');
    } catch (error) {
      console.error('加载分类标准失败:', error);
      message.error('加载分类标准失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 计算统计信息
  const calculateStatistics = (standardsList) => {
    const level1Set = new Set();
    const level2Set = new Set();
    const level3Set = new Set();
    
    standardsList.forEach(standard => {
      level1Set.add(standard.level1);
      level2Set.add(standard.level2);
      level3Set.add(standard.level3);
    });
    
    return {
      total: standardsList.length,
      level1Count: level1Set.size,
      level2Count: level2Set.size,
      level3Count: level3Set.size
    };
  };

  useEffect(() => {
    loadClassificationStandards();
  }, [loadClassificationStandards]);

  // 处理新增/编辑
  const handleEdit = (record = null) => {
    setEditingStandard(record);
    if (record) {
      form.setFieldsValue(record);
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

  // 处理保存
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      let newStandards;
      if (editingStandard) {
        // 编辑现有标准
        newStandards = standards.map(item => 
          item === editingStandard ? { ...item, ...values } : item
        );
      } else {
        // 新增标准
        newStandards = [...standards, values];
      }
      
      // 更新到后端
      const response = await api.post('/classification-standards', {
        standards: newStandards
      });
      
      if (response.data.success) {
        setStandards(newStandards);
        setStatistics(calculateStatistics(newStandards));
        setModalVisible(false);
        message.success(editingStandard ? '编辑成功' : '新增成功');
      } else {
        message.error(response.data.error || '保存失败');
      }
    } catch (error) {
      console.error('保存失败:', error);
      message.error('保存失败');
    }
  };

  // 处理删除
  const handleDelete = async (record) => {
    try {
      const newStandards = standards.filter(item => item !== record);
      
      const response = await api.post('/classification-standards', {
        standards: newStandards
      });
      
      if (response.data.success) {
        setStandards(newStandards);
        setStatistics(calculateStatistics(newStandards));
        message.success('删除成功');
      } else {
        message.error(response.data.error || '删除失败');
      }
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败');
    }
  };

  // 重置为默认
  const handleReset = async () => {
    try {
      const response = await api.post('/classification-standards/reset');
      
      if (response.data.success) {
        await loadClassificationStandards();
        message.success('重置成功');
      } else {
        message.error(response.data.error || '重置失败');
      }
    } catch (error) {
      console.error('重置失败:', error);
      message.error('重置失败');
    }
  };

  // 导出配置
  const handleExport = () => {
    const dataStr = JSON.stringify(standards, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `classification-standards-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    message.success('配置导出成功');
  };

  // 获取分类层级的颜色
  const getLevelColor = (level) => {
    const colors = {
      '选股': 'blue',
      '分析': 'green', 
      '决策': 'orange',
      '信息查询': 'purple'
    };
    return colors[level] || 'default';
  };

  // 表格列定义
  const columns = [
    {
      title: '一级分类',
      dataIndex: 'level1',
      key: 'level1',
      width: 120,
      render: (text) => (
        <Tag color={getLevelColor(text)} style={{ margin: 0 }}>
          {text}
        </Tag>
      ),
      filters: [...new Set(standards.map(item => item.level1))].map(level => ({
        text: level,
        value: level
      })),
      onFilter: (value, record) => record.level1 === value,
    },
    {
      title: '二级分类',
      dataIndex: 'level2',
      key: 'level2',
      width: 140,
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: '三级分类',
      dataIndex: 'level3',
      key: 'level3',
      width: 160,
      render: (text) => <Text>{text}</Text>
    },
    {
      title: '分类定义',
      dataIndex: 'level3_definition',
      key: 'level3_definition',
      width: 250,
      render: (text) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 230, display: 'block' }}>
            {text}
          </Text>
        </Tooltip>
      )
    },
    {
      title: '问题示例',
      dataIndex: 'examples',
      key: 'examples',
      width: 200,
      render: (text) => (
        <Tooltip title={text}>
          <Text type="secondary" ellipsis style={{ maxWidth: 180, display: 'block' }}>
            {text}
          </Text>
        </Tooltip>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="确定删除这个分类标准吗？"
            onConfirm={() => handleDelete(record)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <SettingOutlined />
            <Title level={3} style={{ margin: 0 }}>
              分类标准配置
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<PlusOutlined />} type="primary" onClick={() => handleEdit()}>
              新增分类
            </Button>
            <Button icon={<ExportOutlined />} onClick={handleExport}>
              导出配置
            </Button>
            <Popconfirm
              title="确定重置为默认分类标准吗？这将清除所有自定义配置。"
              onConfirm={handleReset}
              okText="确定"
              cancelText="取消"
            >
              <Button icon={<ReloadOutlined />} danger>
                重置默认
              </Button>
            </Popconfirm>
          </Space>
        }
        style={{
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}
      >
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic
              title="总分类数"
              value={statistics.total}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="一级分类"
              value={statistics.level1Count}
              prefix={<Badge color="blue" />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="二级分类"
              value={statistics.level2Count}
              prefix={<Badge color="green" />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="三级分类"
              value={statistics.level3Count}
              prefix={<Badge color="orange" />}
            />
          </Col>
        </Row>

        <Divider />

        {/* 说明信息 */}
        <Alert
          message="分类标准说明"
          description={
            <div>
              <Paragraph>
                分类标准用于自动识别用户问题类型，系统会根据分类结果选择对应的评估prompt模板。
              </Paragraph>
              <ul style={{ marginBottom: 0 }}>
                <li><Text strong>一级分类</Text>: 问题的主要类型（如：选股、分析、决策、信息查询）</li>
                <li><Text strong>二级分类</Text>: 细分的问题范围</li>
                <li><Text strong>三级分类</Text>: 具体的问题类别</li>
                <li><Text strong>分类定义</Text>: 该分类的具体含义和范围</li>
                <li><Text strong>问题示例</Text>: 典型的问题示例，用于LLM分类参考</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 分类标准表格 */}
        <Table
          columns={columns}
          dataSource={standards}
          loading={loading}
          rowKey={(record) => `${record.level1}-${record.level2}-${record.level3}`}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
          }}
          scroll={{ x: 1200 }}
          size="middle"
        />
      </Card>

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingStandard ? '编辑分类标准' : '新增分类标准'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={800}
        okText="保存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            level1: '',
            level1_definition: '',
            level2: '',
            level3: '',
            level3_definition: '',
            examples: ''
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="level1"
                label="一级分类"
                rules={[{ required: true, message: '请输入一级分类' }]}
              >
                <Input placeholder="如：选股、分析、决策、信息查询" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="level2"
                label="二级分类"
                rules={[{ required: true, message: '请输入二级分类' }]}
              >
                <Input placeholder="如：个股分析、宏观经济分析" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="level3"
                label="三级分类"
                rules={[{ required: true, message: '请输入三级分类' }]}
              >
                <Input placeholder="如：基本面分析、技术面分析" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="level1_definition"
                label="一级分类定义"
                rules={[{ required: true, message: '请输入一级分类定义' }]}
              >
                <Input placeholder="一级分类的含义和范围" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="level3_definition"
            label="三级分类定义"
            rules={[{ required: true, message: '请输入三级分类定义' }]}
          >
            <TextArea
              rows={3}
              placeholder="详细描述该分类的具体含义、适用范围和特征"
            />
          </Form.Item>

          <Form.Item
            name="examples"
            label="问题示例"
            rules={[{ required: true, message: '请输入问题示例' }]}
          >
            <TextArea
              rows={3}
              placeholder="提供该分类的典型问题示例，多个示例用分号分隔"
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ClassificationConfig; 