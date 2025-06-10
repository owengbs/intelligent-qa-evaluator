import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Alert,
  Spin,
  Typography,
  Progress,
  Tag,
  Space,
  Button
} from 'antd';
import {
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;

// 配置axios baseURL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180000, // 增加到3分钟超时，适应大模型长时间处理
  headers: {
    'Content-Type': 'application/json',
  },
});

const BadcaseStatistics = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const fetchBadcaseStatistics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.get('/badcase-statistics');
      
      if (response.data.success) {
        setData(response.data.data);
      } else {
        setError(response.data.message || '获取统计数据失败');
      }
    } catch (err) {
      console.error('获取Badcase统计失败:', err);
      setError('网络错误，请检查连接');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBadcaseStatistics();
  }, []);

  const getPercentageColor = (percentage) => {
    if (percentage <= 5) return '#52c41a'; // 绿色 - 很好
    if (percentage <= 15) return '#faad14'; // 黄色 - 一般
    return '#ff4d4f'; // 红色 - 需要关注
  };

  const getPercentageStatus = (percentage) => {
    if (percentage <= 5) return 'success';
    if (percentage <= 15) return 'active';
    return 'exception';
  };

  const categoryColumns = [
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 200,
    },
    {
      title: '总记录数',
      dataIndex: 'total_records',
      key: 'total_records',
      width: 120,
      align: 'center',
      render: (count) => (
        <Tag color="blue">{count}</Tag>
      )
    },
    {
      title: 'Badcase数量',
      dataIndex: 'badcase_count',
      key: 'badcase_count',
      width: 120,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'red' : 'green'}>{count}</Tag>
      )
    },
    {
      title: 'Badcase比例',
      dataIndex: 'badcase_percentage',
      key: 'badcase_percentage',
      width: 200,
      align: 'center',
      render: (percentage) => (
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Progress
            percent={percentage}
            size="small"
            status={getPercentageStatus(percentage)}
            strokeColor={getPercentageColor(percentage)}
            format={(percent) => `${percent}%`}
          />
        </Space>
      )
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>正在加载Badcase统计数据...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="加载失败"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={fetchBadcaseStatistics}>
            重试
          </Button>
        }
      />
    );
  }

  if (!data) {
    return (
      <Alert
        message="暂无数据"
        description="系统中还没有评估记录"
        type="info"
        showIcon
      />
    );
  }

  const { overall, by_category } = data;

  // 准备表格数据
  const tableData = Object.entries(by_category).map(([category, stats]) => ({
    key: category,
    category,
    ...stats
  }));

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
          Badcase统计分析
        </Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchBadcaseStatistics}
            loading={loading}
          >
            刷新数据
          </Button>
        </Space>
      </div>

      {/* 总体统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总评估记录"
              value={overall.total_records}
              prefix={<CheckCircleOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总Badcase数"
              value={overall.total_badcases}
              prefix={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="AI判断Badcase"
              value={overall.ai_badcases}
              suffix={`(${overall.ai_badcase_percentage}%)`}
              prefix={<WarningOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="人工标记Badcase"
              value={overall.human_badcases}
              suffix={`(${overall.human_badcase_percentage}%)`}
              prefix={<WarningOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 总体Badcase比例 */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={4}>总体Badcase比例</Title>
        <Row gutter={16} align="middle">
          <Col span={12}>
            <Progress
              type="circle"
              percent={overall.total_badcase_percentage}
              status={getPercentageStatus(overall.total_badcase_percentage)}
              strokeColor={getPercentageColor(overall.total_badcase_percentage)}
              format={(percent) => `${percent}%`}
              width={120}
            />
          </Col>
          <Col span={12}>
            <div>
              <Text strong style={{ fontSize: '16px' }}>
                系统质量评估
              </Text>
              <div style={{ marginTop: 8 }}>
                {overall.total_badcase_percentage <= 5 && (
                  <Tag color="success" style={{ fontSize: '14px' }}>
                    ✅ 质量优秀 (≤5%)
                  </Tag>
                )}
                {overall.total_badcase_percentage > 5 && overall.total_badcase_percentage <= 15 && (
                  <Tag color="warning" style={{ fontSize: '14px' }}>
                    ⚠️ 质量一般 (5-15%)
                  </Tag>
                )}
                {overall.total_badcase_percentage > 15 && (
                  <Tag color="error" style={{ fontSize: '14px' }}>
                    🚨 需要关注 (&gt;15%)
                  </Tag>
                )}
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

      {/* 分类统计表格 */}
      <Card>
        <Title level={4}>各分类Badcase统计</Title>
        <Table
          columns={categoryColumns}
          dataSource={tableData}
          pagination={false}
          size="middle"
          scroll={{ x: 600 }}
        />
      </Card>

      {/* 说明信息 */}
      <Alert
        style={{ marginTop: 16 }}
        message="统计说明"
        description={
          <div>
            <p>• <strong>AI判断Badcase</strong>: 系统根据评分阈值自动判断的低质量回答（分数低于50%）</p>
            <p>• <strong>人工标记Badcase</strong>: 评估专家手动标记的问题回答</p>
                         <p>• <strong>质量标准</strong>: ≤5%优秀，5-15%一般，&gt;15%需要关注</p>
          </div>
        }
        type="info"
        showIcon
      />
    </div>
  );
};

export default BadcaseStatistics; 