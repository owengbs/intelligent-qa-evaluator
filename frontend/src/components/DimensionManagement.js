import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Card,
  Tag,
  Space,
  Collapse,
  Typography,
  Popconfirm,
  Switch,
  Row,
  Col,
  Badge,
  Tooltip,
  InputNumber
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;
const { Title, Paragraph, Text } = Typography;

// 添加API基础URL配置和详细日志
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
console.log('🔧 DimensionManagement - API_BASE_URL:', API_BASE_URL);
console.log('🔧 DimensionManagement - process.env.REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
console.log('🔧 DimensionManagement - NODE_ENV:', process.env.NODE_ENV);

const DimensionManagement = () => {
  const [dimensions, setDimensions] = useState([]);
  const [groupedDimensions, setGroupedDimensions] = useState({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingDimension, setEditingDimension] = useState(null);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewingDimension, setViewingDimension] = useState(null);
  const [form] = Form.useForm();

  // 层次选项
  const layerOptions = [
    { value: '第一层指标', label: '第一层指标' },
    { value: '第二层指标', label: '第二层指标' },
    { value: '第三层指标', label: '第三层指标' },
    { value: '其他服务场景', label: '其他服务场景' }
  ];

  // 类别选项
  const categoryOptions = [
    { value: '金融场景', label: '金融场景' },
    { value: '其他服务场景', label: '其他服务场景' },
    { value: '用户体验', label: '用户体验' }
  ];

  // 获取维度列表
  const fetchDimensions = async () => {
    setLoading(true);
    try {
      const dimensionsUrl = `${API_BASE_URL}/dimensions`;
      console.log('🔧 Fetching dimensions from:', dimensionsUrl);
      
      const response = await fetch(dimensionsUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log('🔧 Dimensions response status:', response.status);
      console.log('🔧 Dimensions response headers:', response.headers);
      
      const responseText = await response.text();
      console.log('🔧 Raw response text (first 200 chars):', responseText.substring(0, 200));
      
      let result;
      try {
        result = JSON.parse(responseText);
        console.log('🔧 Parsed JSON result:', result);
      } catch (parseError) {
        console.error('🔧 JSON parse error:', parseError);
        console.error('🔧 Response text:', responseText);
        throw new Error(`JSON解析失败: ${parseError.message}. 响应内容: ${responseText.substring(0, 100)}`);
      }
      
      if (result.success) {
        setDimensions(result.data);
        
        // 获取分组数据
        const groupedUrl = `${API_BASE_URL}/dimensions/grouped`;
        console.log('🔧 Fetching grouped dimensions from:', groupedUrl);
        
        const groupedResponse = await fetch(groupedUrl);
        const groupedResult = await groupedResponse.json();
        if (groupedResult.success) {
          setGroupedDimensions(groupedResult.data);
        }
      } else {
        message.error('获取维度列表失败: ' + result.message);
      }
    } catch (error) {
      console.error('获取维度列表失败:', error);
      message.error('获取维度列表失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDimensions();
  }, []);

  // 处理新增/编辑
  const handleSubmit = async (values) => {
    try {
      // 处理评测标准数据
      const evaluation_criteria = values.evaluation_criteria_items || [];
      
      const submitData = {
        ...values,
        evaluation_criteria: evaluation_criteria.map((item, index) => ({
          level: item.level || `标准${index + 1}`,
          score: item.score || 0,
          description: item.description || ''
        }))
      };

      const url = editingDimension 
        ? `${API_BASE_URL}/dimensions/${editingDimension.id}`
        : `${API_BASE_URL}/dimensions`;
      
      const method = editingDimension ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData),
      });

      const result = await response.json();
      
      if (result.success) {
        message.success(editingDimension ? '维度更新成功' : '维度创建成功');
        setModalVisible(false);
        setEditingDimension(null);
        form.resetFields();
        fetchDimensions();
      } else {
        message.error(result.message || '操作失败');
      }
    } catch (error) {
      console.error('提交失败:', error);
      message.error('操作失败: ' + error.message);
    }
  };

  // 处理删除
  const handleDelete = async (dimensionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/dimensions/${dimensionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();
      
      if (result.success) {
        message.success('维度删除成功');
        fetchDimensions();
      } else {
        message.error(result.message || '删除失败');
      }
    } catch (error) {
      console.error('删除失败:', error);
      message.error('删除失败: ' + error.message);
    }
  };

  // 打开编辑模态框
  const handleEdit = (dimension) => {
    setEditingDimension(dimension);
    
    // 准备评测标准数据
    const evaluation_criteria_items = dimension.evaluation_criteria || [];
    
    form.setFieldsValue({
      ...dimension,
      evaluation_criteria_items: evaluation_criteria_items
    });
    
    setModalVisible(true);
  };

  // 查看维度详情
  const handleView = (dimension) => {
    setViewingDimension(dimension);
    setViewModalVisible(true);
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
              <Badge count={item.score} style={{ backgroundColor: '#52c41a' }} />
              <Text>{item.description}</Text>
            </Space>
          </div>
        ))}
      </Space>
    );
  };

  // 表格列定义
  const columns = [
    {
      title: '维度名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: '层次',
      dataIndex: 'layer',
      key: 'layer',
      width: 120,
      render: (layer) => {
        const colors = {
          '第一层指标': 'red',
          '第二层指标': 'orange', 
          '第三层指标': 'green',
          '其他服务场景': 'blue'
        };
        return <Tag color={colors[layer] || 'default'}>{layer}</Tag>;
      }
    },
    {
      title: '类别',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (category) => <Tag>{category}</Tag>
    },
    {
      title: '定义',
      dataIndex: 'definition',
      key: 'definition',
      render: (text) => (
        <Tooltip title={text}>
          <div style={{ 
            maxWidth: '300px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}>
            {text || '暂无定义'}
          </div>
        </Tooltip>
      )
    },
    {
      title: '评测标准',
      dataIndex: 'evaluation_criteria',
      key: 'evaluation_criteria',
      width: 200,
      render: (criteria) => (
        <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
          {renderEvaluationCriteria(criteria)}
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (is_active) => (
        <Tag color={is_active ? 'green' : 'red'}>
          {is_active ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '排序',
      dataIndex: 'sort_order',
      key: 'sort_order',
      width: 80,
      render: (order) => <Text>{order || 0}</Text>
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button 
              type="link" 
              icon={<EyeOutlined />} 
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="link" 
              icon={<EditOutlined />} 
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除这个维度吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={3}>评估维度管理</Title>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={fetchDimensions}
              loading={loading}
            >
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingDimension(null);
                form.resetFields();
                setModalVisible(true);
              }}
            >
              新增维度
            </Button>
          </Space>
        </div>

        {/* 按层次分组展示 */}
        <Collapse style={{ marginBottom: '24px' }}>
          {Object.entries(groupedDimensions).map(([layer, layerDimensions]) => (
            <Panel 
              header={
                <Space>
                  <Text strong>{layer}</Text>
                  <Badge count={layerDimensions.length} style={{ backgroundColor: '#1890ff' }} />
                </Space>
              } 
              key={layer}
            >
              <Row gutter={[16, 16]}>
                {layerDimensions.map((dimension) => (
                  <Col span={8} key={dimension.id}>
                    <Card 
                      size="small"
                      title={dimension.name}
                      extra={
                        <Space>
                          <Button 
                            type="link" 
                            size="small"
                            icon={<EyeOutlined />}
                            onClick={() => handleView(dimension)}
                          />
                          <Button 
                            type="link" 
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => handleEdit(dimension)}
                          />
                        </Space>
                      }
                    >
                      <Paragraph ellipsis={{ rows: 2 }}>
                        {dimension.definition || '暂无定义'}
                      </Paragraph>
                      <div>
                        <Tag>{dimension.category}</Tag>
                        <Tag color={dimension.is_active ? 'green' : 'red'}>
                          {dimension.is_active ? '启用' : '禁用'}
                        </Tag>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Panel>
          ))}
        </Collapse>

        {/* 详细表格 */}
        <Table
          columns={columns}
          dataSource={dimensions}
          rowKey="id"
          loading={loading}
          pagination={{
            total: dimensions.length,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑模态框 */}
      <Modal
        title={editingDimension ? '编辑维度' : '新增维度'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingDimension(null);
          form.resetFields();
        }}
        width={800}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="维度名称"
                rules={[{ required: true, message: '请输入维度名称' }]}
              >
                <Input placeholder="请输入维度名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="layer"
                label="层次"
                rules={[{ required: true, message: '请选择层次' }]}
              >
                <Select placeholder="请选择层次">
                  {layerOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="category"
                label="类别"
              >
                <Select placeholder="请选择类别">
                  {categoryOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="sort_order"
                label="排序"
              >
                <InputNumber 
                  placeholder="排序权重" 
                  min={0}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="is_active"
                label="状态"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="definition"
            label="维度定义"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入维度定义"
            />
          </Form.Item>

          <Form.Item
            name="examples"
            label="示例说明"
          >
            <TextArea 
              rows={3} 
              placeholder="请输入示例说明"
            />
          </Form.Item>

          {/* 评测标准 */}
          <Form.Item label="评测标准">
            <Form.List name="evaluation_criteria_items">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Card key={key} size="small" style={{ marginBottom: 8 }}>
                      <Row gutter={16}>
                        <Col span={6}>
                          <Form.Item
                            {...restField}
                            name={[name, 'level']}
                            rules={[{ required: true, message: '请输入等级' }]}
                          >
                            <Input placeholder="等级 (如: 强/适中/弱)" />
                          </Form.Item>
                        </Col>
                        <Col span={6}>
                          <Form.Item
                            {...restField}
                            name={[name, 'score']}
                            rules={[{ required: true, message: '请输入分数' }]}
                          >
                            <InputNumber 
                              placeholder="分数" 
                              min={0} 
                              max={10}
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                        <Col span={10}>
                          <Form.Item
                            {...restField}
                            name={[name, 'description']}
                            rules={[{ required: true, message: '请输入描述' }]}
                          >
                            <Input placeholder="评测标准描述" />
                          </Form.Item>
                        </Col>
                        <Col span={2}>
                          <Button 
                            type="link" 
                            danger
                            onClick={() => remove(name)}
                          >
                            删除
                          </Button>
                        </Col>
                      </Row>
                    </Card>
                  ))}
                  <Form.Item>
                    <Button 
                      type="dashed" 
                      onClick={() => add()} 
                      block
                      icon={<PlusOutlined />}
                    >
                      添加评测标准
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingDimension ? '更新' : '创建'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看详情模态框 */}
      <Modal
        title="维度详情"
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {viewingDimension && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Text strong>维度名称: </Text>
                <Text>{viewingDimension.name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>层次: </Text>
                <Tag color="blue">{viewingDimension.layer}</Tag>
              </Col>
              <Col span={12}>
                <Text strong>类别: </Text>
                <Tag>{viewingDimension.category}</Tag>
              </Col>
              <Col span={12}>
                <Text strong>状态: </Text>
                <Tag color={viewingDimension.is_active ? 'green' : 'red'}>
                  {viewingDimension.is_active ? '启用' : '禁用'}
                </Tag>
              </Col>
            </Row>

            <div style={{ marginTop: 16 }}>
              <Text strong>维度定义:</Text>
              <Paragraph style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                {viewingDimension.definition || '暂无定义'}
              </Paragraph>
            </div>

            <div style={{ marginTop: 16 }}>
              <Text strong>评测标准:</Text>
              <div style={{ marginTop: 8 }}>
                {renderEvaluationCriteria(viewingDimension.evaluation_criteria)}
              </div>
            </div>

            <div style={{ marginTop: 16 }}>
              <Text strong>示例说明:</Text>
              <Paragraph style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 4 }}>
                {viewingDimension.examples || '暂无示例'}
              </Paragraph>
            </div>

            {viewingDimension.created_at && (
              <div style={{ marginTop: 16, color: '#666' }}>
                <Text type="secondary">
                  创建时间: {new Date(viewingDimension.created_at).toLocaleString()}
                </Text>
                {viewingDimension.updated_at && (
                  <Text type="secondary" style={{ marginLeft: 24 }}>
                    更新时间: {new Date(viewingDimension.updated_at).toLocaleString()}
                  </Text>
                )}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default DimensionManagement; 