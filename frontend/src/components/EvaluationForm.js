import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Button, 
  Card, 
  Form, 
  Input, 
  Spin, 
  Alert, 
  Row, 
  Col, 
  Divider,
  Typography,
  Space,
  Statistic,
  Tag,
  Modal,
  List,
  Progress,
  message,
  DatePicker,
  Badge
} from 'antd';
import { 
  ClearOutlined, 
  CheckCircleOutlined,
  EyeOutlined,
  CalendarOutlined,
  BulbOutlined,
  TagOutlined,
  RobotOutlined,
  ThunderboltOutlined,
  SendOutlined
} from '@ant-design/icons';
import { submitEvaluation, clearResult, clearError, clearHistory } from '../store/evaluationSlice';
import dayjs from 'dayjs';
import axios from 'axios';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

// 配置axios baseURL - 由于有proxy配置，可以使用相对路径
const api = axios.create({
  timeout: 120000, // 增加超时时间到120秒，适应大模型长时间思考的情况
  headers: {
    'Content-Type': 'application/json',
  },
});

const EvaluationForm = () => {
  const [form] = Form.useForm();
  const dispatch = useDispatch();
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [loadingDots, setLoadingDots] = useState('');
  const [variableHelpVisible, setVariableHelpVisible] = useState(false);
  const [classification, setClassification] = useState(null);
  const [classificationLoading, setClassificationLoading] = useState(false);
  const [showClassificationModal, setShowClassificationModal] = useState(false);
  const [autoClassifyEnabled, setAutoClassifyEnabled] = useState(true);
  
  // Redux状态
  const { isLoading, result, error, history } = useSelector((state) => state.evaluation);

  // 使用useMemo优化默认评分规则模板
  const defaultScoringPrompt = useMemo(() => `请根据以下详细的评估标准对回答质量进行评分：

评估标准：
{evaluation_criteria}

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

评估要求：
1. 严格按照上述评估标准进行评分
2. 特别注意问题提出时间 {question_time}，判断答案在当时是否准确
3. 某些信息可能随时间变化，需要基于当时的情况进行评判
4. 对于时间敏感的内容（如历史事件、政策法规、技术发展等）要格外注意

请严格按照以下格式返回评估结果:
总分: [分数]/10
评分理由: [详细的多行评分分析，按照评估标准逐项说明，特别注明时间因素的考虑]`, []);

  // 加载动画效果
  useEffect(() => {
    let interval;
    if (isLoading) {
      interval = setInterval(() => {
        setLoadingDots(prev => {
          if (prev.length >= 3) return '';
          return prev + '.';
        });
      }, 500);
    } else {
      setLoadingDots('');
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isLoading]);

  // 初始化表单默认值
  useEffect(() => {
    const defaultEvaluationCriteria = `准确性\t答案与事实完全一致，数据准确无误\t0-4分：完全正确=4分；轻微误差=2分；重大错误=0分
完整性\t回答覆盖问题所有关键信息点\t0-3分：完全覆盖=3分；部分覆盖=1分；未覆盖=0分
流畅性\t语言自然流畅，表达清晰易懂\t0-2分：表达清晰=2分；基本流畅=1分；表达混乱=0分
安全性\t避免有害、误导性或不当内容\t0-1分：安全无害=1分；存在问题=0分`;

    // 设置表单初始值
    form.setFieldsValue({
      evaluationCriteria: defaultEvaluationCriteria,
      questionTime: dayjs()
    });
  }, [form]);

  // 提交评估
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 映射前端字段名到后端API期望的字段名
      const formattedValues = {
        user_input: values.userQuery,  // userQuery -> user_input
        model_answer: values.modelResponse,  // modelResponse -> model_answer
        reference_answer: values.referenceAnswer || '',  // referenceAnswer -> reference_answer
        question_time: values.questionTime ? values.questionTime.format('YYYY-MM-DD HH:mm:ss') : dayjs().format('YYYY-MM-DD HH:mm:ss'),
        evaluation_criteria: values.evaluationCriteria,  // evaluationCriteria -> evaluation_criteria
        scoring_prompt: defaultScoringPrompt  // 使用默认的scoring_prompt
      };
      
      console.log('表单验证通过，提交评估:', formattedValues);
      dispatch(submitEvaluation(formattedValues));
    } catch (validationError) {
      console.error('表单验证失败:', validationError);
    }
  };

  // 清空表单
  const handleClear = () => {
    const defaultEvaluationCriteria = `准确性\t答案与事实完全一致，数据准确无误\t0-4分：完全正确=4分；轻微误差=2分；重大错误=0分
完整性\t回答覆盖问题所有关键信息点\t0-3分：完全覆盖=3分；部分覆盖=1分；未覆盖=0分
流畅性\t语言自然流畅，表达清晰易懂\t0-2分：表达清晰=2分；基本流畅=1分；表达混乱=0分
安全性\t避免有害、误导性或不当内容\t0-1分：安全无害=1分；存在问题=0分`;

    form.resetFields();
    form.setFieldsValue({
      evaluationCriteria: defaultEvaluationCriteria,
      questionTime: dayjs()
    });
    
    dispatch(clearResult());
    dispatch(clearError());
    setClassification(null);
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

  // 渲染加载提示
  const renderLoadingTip = () => {
    return (
      <div style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: 16 }}>
          <Text strong>正在调用大模型进行评估{loadingDots}</Text>
        </div>
        <div style={{ marginBottom: 8 }}>
          <Text type="secondary">⏱️ 预计需要 30-120 秒</Text>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            💡 大模型正在深度分析内容质量，请耐心等待
          </Text>
        </div>
        <Progress 
          percent={100} 
          status="active" 
          showInfo={false}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
        />
      </div>
    );
  };

  // 渲染历史记录
  const renderHistoryModal = () => (
    <Modal
      title="评估历史记录"
      open={historyModalVisible}
      onCancel={() => setHistoryModalVisible(false)}
      footer={[
        <Button key="clear" danger onClick={() => dispatch(clearHistory())}>
          清空历史
        </Button>,
        <Button key="close" onClick={() => setHistoryModalVisible(false)}>
          关闭
        </Button>
      ]}
      width={800}
    >
      <List
        dataSource={history}
        renderItem={(item, index) => (
          <List.Item
            actions={[
              <Button 
                size="small" 
                icon={<EyeOutlined />}
                onClick={() => {
                  form.setFieldsValue({
                    userQuery: item.raw_response?.split('用户输入:')[1]?.split('模型回答:')[0]?.trim() || '',
                    modelResponse: item.raw_response?.split('模型回答:')[1]?.split('参考答案:')[0]?.trim() || '',
                    referenceAnswer: item.raw_response?.split('参考答案:')[1]?.trim() || ''
                  });
                  setHistoryModalVisible(false);
                }}
              >
                查看
              </Button>
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Text>评估 #{index + 1}</Text>
                  <Tag color={getScoreLevel(item.score).color}>
                    {item.score}/10 - {getScoreLevel(item.score).text}
                  </Tag>
                </Space>
              }
              description={
                <div>
                  <Text type="secondary">{item.timestamp}</Text>
                  <br />
                  <Text>{item.reasoning?.substring(0, 100)}...</Text>
                </div>
              }
            />
          </List.Item>
        )}
      />
    </Modal>
  );

  // 渲染评估结果
  const renderResult = () => {
    if (error) {
      return (
        <Alert 
          message="评估失败" 
          description={error}
          type="error" 
          showIcon
          closable
          onClose={() => dispatch(clearError())}
        />
      );
    }

    if (!result) return null;

    const scoreLevel = getScoreLevel(result.score);

    return (
      <Card 
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            评估结果
          </Space>
        }
        extra={<Text type="secondary">{new Date(result.timestamp).toLocaleString()}</Text>}
        style={{ marginTop: 24 }}
      >
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Row gutter={16} align="middle">
              <Col>
                <Statistic
                  title="总分"
                  value={result.score}
                  suffix="/ 10"
                  precision={1}
                  valueStyle={{ 
                    color: getScoreColor(result.score),
                    fontSize: '2rem'
                  }}
                />
              </Col>
              <Col>
                <Tag color={scoreLevel.color} style={{ fontSize: '14px', padding: '4px 12px' }}>
                  {scoreLevel.text}
                </Tag>
              </Col>
            </Row>
          </Col>
          
          {result.dimensions && Object.keys(result.dimensions).length > 0 && (
            <Col span={24}>
              <Title level={5}>各维度评分:</Title>
              <Row gutter={16}>
                {Object.entries(result.dimensions).map(([key, value]) => {
                  const dimensionNames = {
                    accuracy: '准确性',
                    completeness: '完整性',
                    fluency: '流畅性',
                    safety: '安全性'
                  };
                  return (
                    <Col span={6} key={key}>
                      <Statistic
                        title={dimensionNames[key] || key}
                        value={value}
                        precision={1}
                        valueStyle={{ fontSize: '16px' }}
                      />
                    </Col>
                  );
                })}
              </Row>
            </Col>
          )}
          
          <Col span={24}>
            <Title level={5}>评分理由:</Title>
            <div style={{ 
              background: '#fafafa', 
              padding: 16, 
              borderRadius: 6,
              whiteSpace: 'pre-line',
              lineHeight: 1.6
            }}>
              {result.reasoning}
            </div>
          </Col>
          
          <Col span={24}>
            <Row justify="space-between">
              <Col>
                <Text type="secondary">
                  评估耗时: {result.evaluation_time_seconds}秒
                </Text>
              </Col>
              <Col>
                <Text type="secondary">
                  使用模型: {result.model_used}
                </Text>
              </Col>
              {result.question_time && (
                <Col>
                  <Text type="secondary">
                    问题时间: {result.question_time}
                  </Text>
                </Col>
              )}
            </Row>
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染变量帮助模态框
  const renderVariableHelpModal = () => (
    <Modal
      title="评估系统帮助"
      open={variableHelpVisible}
      onCancel={() => setVariableHelpVisible(false)}
      footer={[
        <Button key="close" type="primary" onClick={() => setVariableHelpVisible(false)}>
          知道了
        </Button>
      ]}
      width={700}
    >
      <div style={{ lineHeight: 1.6 }}>
        <Title level={5}>📝 评估流程说明</Title>
        <div style={{ marginBottom: 24 }}>
          <p>本系统采用智能化评估流程：</p>
          <ol>
            <li><strong>填写基础信息</strong>：输入用户问题、模型回答、参考答案等</li>
            <li><strong>智能分类</strong>：系统自动分析问题类型并推荐评估标准</li>
            <li><strong>设置评估标准</strong>：根据分类结果自动匹配或手动设置评估维度</li>
            <li><strong>开始评估</strong>：大模型基于标准进行深度分析和评分</li>
            <li><strong>查看结果</strong>：获得详细的评分结果和改进建议</li>
          </ol>
        </div>

        <Title level={5}>💡 使用技巧</Title>
        <div style={{ 
          background: '#f0f0f0', 
          padding: 16, 
          borderRadius: 6, 
          marginBottom: 16
        }}>
          <ul style={{ marginLeft: 16, marginBottom: 0 }}>
            <li>开启"智能分类"可以自动识别问题类型并推荐评估标准</li>
            <li>问题时间很重要，影响模型对时效性信息的评判</li>
            <li>评估标准支持制表符分隔格式，便于批量设置</li>
            <li>大模型评估可能需要30-120秒，请耐心等待</li>
          </ul>
        </div>

        <Alert
          message="💡 评估标准格式说明"
          description={
            <div>
              <p>评估标准使用制表符分隔的格式，每行一个维度：</p>
              <code>
                维度名称[TAB]评估要求[TAB]评分标准<br/>
                示例：准确性[TAB]答案与事实一致[TAB]0-4分：完全正确=4分
              </code>
            </div>
          }
          type="info"
          showIcon
          style={{ marginTop: 16 }}
        />
      </div>
    </Modal>
  );

  // 新增：自动分类功能
  const handleAutoClassify = async (userInput) => {
    if (!userInput || !autoClassifyEnabled) return;
    
    try {
      setClassificationLoading(true);
      const response = await api.post('/api/classify', {
        userQuery: userInput
      });
      
      setClassification(response.data);
      message.success(`问题已自动分类: ${response.data.level1} → ${response.data.level2} → ${response.data.level3}`);
      
      // 根据分类结果自动获取和更新评估标准
      await updateEvaluationCriteriaByClassification(response.data.level2);
      
    } catch (error) {
      console.error('自动分类失败:', error);
      
      // 判断是否为超时错误
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        message.error({
          content: '分类请求超时，大模型思考时间较长，请稍后重试或手动进行分类',
          duration: 5,
        });
      } else if (error.response?.status === 504) {
        message.error({
          content: '服务器处理超时，大模型响应时间过长，请稍后重试',
          duration: 5,
        });
      } else if (error.response?.status >= 500) {
        message.error({
          content: '服务器内部错误，请检查网络连接或稍后重试',
          duration: 4,
        });
      } else {
        message.warning({
          content: '自动分类失败，将使用默认评估模式',
          duration: 3,
        });
      }
      
      setClassification(null);
    } finally {
      setClassificationLoading(false);
    }
  };

  // 新增：根据分类获取评估标准
  const updateEvaluationCriteriaByClassification = async (level2Category) => {
    if (!level2Category) return;
    
    try {
      console.log('正在获取分类评估标准:', level2Category);
      
      // 调用API获取对应分类的评估标准
      const response = await api.get(`/api/evaluation-template/${level2Category}`);
      
      if (response.data.success && response.data.data) {
        const template = response.data.data;
        
        // 格式化评估标准为表格格式
        const formattedCriteria = formatEvaluationCriteria(template);
        
        // 更新表单中的评估标准
        form.setFieldsValue({
          evaluationCriteria: formattedCriteria
        });
        
        message.success(`已自动更新为"${level2Category}"的评估标准 (总分: ${template.total_max_score}分)`);
        console.log('评估标准更新成功:', formattedCriteria);
        
      } else {
        console.warn('未找到对应分类的评估标准');
        message.warning(`未找到"${level2Category}"的评估标准，将使用默认标准`);
      }
      
    } catch (error) {
      console.error('获取评估标准失败:', error);
      message.warning('获取评估标准失败，将使用默认标准');
    }
  };

  // 新增：格式化评估标准为制表符分隔格式
  const formatEvaluationCriteria = (template) => {
    if (!template || !template.dimensions) return '';
    
    return template.dimensions
      .map(dimension => `${dimension.name}\t${dimension.reference_standard}\t${dimension.scoring_principle}`)
      .join('\n');
  };

  // 监听用户输入变化，触发自动分类
  const debounceTimerRef = useRef(null);
  
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const handleUserInputChange = useCallback((value) => {
    // 清除之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    if (value && value.length > 5 && autoClassifyEnabled) {
      // 设置新的定时器
      debounceTimerRef.current = setTimeout(() => {
        handleAutoClassify(value);
      }, 1000);
    }
  }, [autoClassifyEnabled]); // 移除handleAutoClassify依赖，直接调用

  // 清理定时器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // 手动分类
  const handleManualClassify = async () => {
    const userQuery = form.getFieldValue('userQuery');
    if (!userQuery) {
      message.warning('请先输入用户问题');
      return;
    }
    
    await handleAutoClassify(userQuery);
  };

  // 获取分类标签颜色
  const getClassificationColor = (level) => {
    const colors = {
      '选股': 'blue',
      '分析': 'green',
      '决策': 'orange', 
      '信息查询': 'purple'
    };
    return colors[level] || 'default';
  };

  // 渲染分类信息
  const renderClassificationInfo = () => {
    if (!classification) return null;

    return (
      <Card 
        size="small" 
        style={{ 
          marginBottom: 16,
          background: 'linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%)',
          border: '1px solid #1890ff'
        }}
        title={
          <Space>
            <TagOutlined style={{ color: '#1890ff' }} />
            <Text strong style={{ color: '#1890ff' }}>智能分类结果</Text>
            <Badge 
              count={`置信度: ${Math.round((classification.confidence || 0) * 100)}%`} 
              style={{ backgroundColor: classification.confidence > 0.8 ? '#52c41a' : '#faad14' }}
            />
          </Space>
        }
        extra={
          <Space>
            <Button 
              size="small" 
              type="primary"
              ghost
              onClick={() => updateEvaluationCriteriaByClassification(classification.level2)}
              title="重新获取评估标准"
            >
              刷新标准
            </Button>
            <Button 
              size="small" 
              type="link"
              onClick={() => setShowClassificationModal(true)}
            >
              查看详情
            </Button>
            <Button 
              size="small" 
              type="link"
              danger
              onClick={() => setClassification(null)}
            >
              清除分类
            </Button>
          </Space>
        }
      >
        <Row gutter={[8, 8]}>
          <Col>
            <Tag color={getClassificationColor(classification.level1)} style={{ margin: 0 }}>
              {classification.level1}
            </Tag>
          </Col>
          <Col>
            <Text type="secondary">→</Text>
          </Col>
          <Col>
            <Tag color="default">
              {classification.level2}
            </Tag>
          </Col>
          <Col>
            <Text type="secondary">→</Text>
          </Col>
          <Col>
            <Tag color="default">
              {classification.level3}
            </Tag>
          </Col>
        </Row>
        <Paragraph style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
          <Text type="secondary">
            {classification.level3_definition}
          </Text>
        </Paragraph>
        <Paragraph style={{ margin: '4px 0 0 0', fontSize: '12px' }}>
          <Text type="secondary">
            💡 评估标准已自动更新为"{classification.level2}"分类的专用标准
          </Text>
        </Paragraph>
      </Card>
    );
  };

  return (
    <div style={{ 
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        {/* 主要内容区域 */}
        <Card
          style={{
            borderRadius: '16px',
            boxShadow: '0 20px 40px rgba(0, 0, 0, 0.1)',
            border: 'none',
            overflow: 'hidden'
          }}
          bodyStyle={{ padding: 0 }}
        >
          {/* 头部区域 */}
          <div style={{
            background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
            padding: '24px 32px',
            color: 'white'
          }}>
            <Space align="center">
              <RobotOutlined style={{ fontSize: '32px' }} />
              <div>
                <Title level={3} style={{ margin: 0, color: 'white' }}>
                  评估信息输入
                </Title>
                <Text style={{ color: 'rgba(255,255,255,0.8)', fontSize: '14px' }}>
                  请填写完整的评估信息，系统将自动进行智能分析和评分
                </Text>
              </div>
            </Space>
            {autoClassifyEnabled && (
              <Tag 
                icon={<ThunderboltOutlined />} 
                color="gold"
                style={{ 
                  position: 'absolute', 
                  top: '24px', 
                  right: '32px',
                  border: 'none',
                  borderRadius: '12px'
                }}
              >
                智能分类已启用
              </Tag>
            )}
          </div>

          {/* 表单内容区域 */}
          <div style={{ padding: '32px' }}>
            <Form form={form} layout="vertical" size="large">
              {/* 基础信息输入 */}
              <Row gutter={[24, 24]}>
                <Col xs={24} lg={12}>
                  <Form.Item 
                    name="userQuery" 
                    label={
                      <Space>
                        <span style={{ fontWeight: 600, color: '#1890ff' }}>用户输入</span>
                        <Tag size="small" color="blue">必填</Tag>
                      </Space>
                    }
                    rules={[{ required: true, message: '请输入用户问题' }]}
                  >
                    <TextArea 
                      rows={5} 
                      placeholder="请输入用户的原始问题，系统将自动进行分类识别..." 
                      onChange={(e) => handleUserInputChange(e.target.value)}
                      style={{
                        borderRadius: '8px',
                        border: '2px solid #f0f0f0',
                        transition: 'all 0.3s ease'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#1890ff';
                        e.target.style.boxShadow = '0 0 0 2px rgba(24, 144, 255, 0.2)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#f0f0f0';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} lg={12}>
                  <Form.Item 
                    name="modelResponse" 
                    label={
                      <Space>
                        <span style={{ fontWeight: 600, color: '#1890ff' }}>模型回答</span>
                        <Tag size="small" color="blue">必填</Tag>
                      </Space>
                    }
                    rules={[{ required: true, message: '请输入模型回答' }]}
                  >
                    <TextArea 
                      rows={5} 
                      placeholder="请输入待评估的模型回答内容..." 
                      style={{
                        borderRadius: '8px',
                        border: '2px solid #f0f0f0',
                        transition: 'all 0.3s ease'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#1890ff';
                        e.target.style.boxShadow = '0 0 0 2px rgba(24, 144, 255, 0.2)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#f0f0f0';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              {/* 分类信息显示 */}
              {(classification || classificationLoading) && (
                <div style={{ marginBottom: 24 }}>
                  {classificationLoading ? (
                    <Card 
                      size="small" 
                      style={{ 
                        background: 'linear-gradient(135deg, #fff9e6 0%, #f0f9ff 100%)',
                        border: '2px solid #faad14',
                        borderRadius: '12px',
                        boxShadow: '0 4px 12px rgba(250, 173, 20, 0.15)'
                      }}
                    >
                      <div style={{ padding: '12px 0' }}>
                        <Space direction="vertical" size={12} style={{ width: '100%' }}>
                          <Space size={16}>
                            <Spin size="small" />
                            <Text strong style={{ color: '#fa8c16', fontSize: '16px' }}>
                              正在进行智能分类...
                            </Text>
                          </Space>
                          <Text type="secondary" style={{ fontSize: '14px' }}>
                            🤖 大模型正在深度分析问题类型，预计需要 30-120 秒
                          </Text>
                          <Progress 
                            percent={100} 
                            status="active" 
                            showInfo={false}
                            strokeColor={{
                              '0%': '#faad14',
                              '100%': '#1890ff',
                            }}
                            strokeWidth={8}
                            style={{ borderRadius: '4px' }}
                          />
                        </Space>
                      </div>
                    </Card>
                  ) : (
                    renderClassificationInfo()
                  )}
                </div>
              )}

              {/* 详细信息输入 */}
              <Row gutter={[24, 24]}>
                <Col xs={24} lg={12}>
                  <Form.Item 
                    name="questionTime" 
                    label={
                      <Space>
                        <CalendarOutlined style={{ color: '#1890ff' }} />
                        <span style={{ fontWeight: 600, color: '#1890ff' }}>问题提出时间</span>
                        <Tag size="small" color="blue">必填</Tag>
                      </Space>
                    }
                    rules={[{ required: true, message: '请选择问题提出时间' }]}
                  >
                    <DatePicker 
                      showTime={{ format: 'HH:mm:ss' }}
                      format="YYYY-MM-DD HH:mm:ss"
                      placeholder="选择问题提出时间"
                      style={{ 
                        width: '100%',
                        borderRadius: '8px',
                        border: '2px solid #f0f0f0',
                        height: '48px'
                      }}
                      defaultValue={dayjs()}
                      disabledDate={(current) => current && current > dayjs().endOf('day')}
                    />
                  </Form.Item>
                </Col>
                <Col xs={24} lg={12}>
                  <Form.Item 
                    name="referenceAnswer" 
                    label={
                      <Space>
                        <span style={{ fontWeight: 600, color: '#1890ff' }}>参考答案</span>
                        <Tag size="small" color="blue">必填</Tag>
                      </Space>
                    }
                    rules={[{ required: true, message: '请输入参考答案' }]}
                  >
                    <TextArea 
                      rows={4} 
                      placeholder="请输入标准的参考答案作为评估基准..." 
                      style={{
                        borderRadius: '8px',
                        border: '2px solid #f0f0f0',
                        transition: 'all 0.3s ease'
                      }}
                      onFocus={(e) => {
                        e.target.style.borderColor = '#1890ff';
                        e.target.style.boxShadow = '0 0 0 2px rgba(24, 144, 255, 0.2)';
                      }}
                      onBlur={(e) => {
                        e.target.style.borderColor = '#f0f0f0';
                        e.target.style.boxShadow = 'none';
                      }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              {/* 评估标准 */}
              <Form.Item
                name="evaluationCriteria"
                label={
                  <Space>
                    <BulbOutlined style={{ color: '#1890ff' }} />
                    <span style={{ fontWeight: 600, color: '#1890ff' }}>评估标准</span>
                    <Tag size="small" color="blue">必填</Tag>
                  </Space>
                }
                rules={[{ required: true, message: '请输入评估标准' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="请定义详细的评估维度和评分规则（支持制表符分隔格式）&#10;示例：准确性&#9;答案与事实完全一致&#9;0-4分：完全正确=4分；轻微误差=2分；重大错误=0分"
                  maxLength={2000}
                  showCount
                  style={{
                    borderRadius: '8px',
                    border: '2px solid #f0f0f0',
                    transition: 'all 0.3s ease',
                    fontFamily: 'Consolas, Monaco, monospace'
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = '#1890ff';
                    e.target.style.boxShadow = '0 0 0 2px rgba(24, 144, 255, 0.2)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#f0f0f0';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </Form.Item>

              {/* 操作按钮区域 */}
              <div style={{ 
                marginTop: 32,
                padding: '24px',
                background: 'linear-gradient(135deg, #f6f9fc 0%, #f0f4f8 100%)',
                borderRadius: '12px',
                border: '1px solid #e8f4f8'
              }}>
                <Row gutter={16} align="middle">
                  <Col xs={24} md={12}>
                    <Space size={16}>
                      <Button 
                        type="primary" 
                        icon={<ThunderboltOutlined />}
                        onClick={handleManualClassify}
                        loading={classificationLoading}
                        disabled={!form.getFieldValue('userQuery')}
                        style={{
                          borderRadius: '8px',
                          height: '40px',
                          fontWeight: 600,
                          background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                          border: 'none'
                        }}
                      >
                        智能分类
                      </Button>
                      <Button 
                        type={autoClassifyEnabled ? 'default' : 'dashed'}
                        size="small"
                        onClick={() => setAutoClassifyEnabled(!autoClassifyEnabled)}
                        style={{ borderRadius: '6px' }}
                      >
                        {autoClassifyEnabled ? '关闭自动分类' : '开启自动分类'}
                      </Button>
                    </Space>
                  </Col>
                  <Col xs={24} md={12}>
                    <div style={{ textAlign: 'right' }}>
                      <Space size={16}>
                        <Button 
                          icon={<ClearOutlined />}
                          onClick={handleClear}
                          style={{
                            borderRadius: '8px',
                            height: '40px'
                          }}
                        >
                          清空表单
                        </Button>
                        <Button 
                          type="primary" 
                          icon={<SendOutlined />}
                          onClick={handleSubmit}
                          loading={isLoading}
                          size="large"
                          style={{
                            borderRadius: '8px',
                            height: '48px',
                            fontWeight: 600,
                            fontSize: '16px',
                            background: 'linear-gradient(135deg, #52c41a 0%, #1890ff 100%)',
                            border: 'none',
                            boxShadow: '0 4px 12px rgba(82, 196, 26, 0.3)'
                          }}
                        >
                          开始评估
                        </Button>
                      </Space>
                    </div>
                  </Col>
                </Row>
              </div>
            </Form>
          </div>
        </Card>

        {/* 加载状态显示 */}
        {isLoading && (
          <Card 
            style={{
              marginTop: 24,
              borderRadius: '16px',
              border: 'none',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.1)'
            }}
          >
            <div style={{ textAlign: 'center', padding: '24px' }}>
              <Space direction="vertical" size={16}>
                <Spin size="large" />
                <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                  正在进行智能评估...
                </Title>
                {renderLoadingTip()}
              </Space>
            </div>
          </Card>
        )}

        {/* 评估结果展示区域 - 移到页面最下方 */}
        {(result || error) && (
          <div style={{ marginTop: 32 }}>
            <Card
              style={{
                borderRadius: '16px',
                border: 'none',
                boxShadow: '0 12px 32px rgba(0, 0, 0, 0.1)',
                overflow: 'hidden'
              }}
              bodyStyle={{ padding: 0 }}
            >
              <div style={{
                background: 'linear-gradient(135deg, #52c41a 0%, #1890ff 100%)',
                padding: '20px 32px',
                color: 'white'
              }}>
                <Space align="center">
                  <CheckCircleOutlined style={{ fontSize: '24px' }} />
                  <Title level={3} style={{ margin: 0, color: 'white' }}>
                    评估结果
                  </Title>
                </Space>
              </div>
              <div style={{ padding: '32px' }}>
                {renderResult()}
              </div>
            </Card>
          </div>
        )}
      </div>

      {/* 分类详情模态框 */}
      <Modal
        title="分类详情"
        open={showClassificationModal}
        onCancel={() => setShowClassificationModal(false)}
        footer={[
          <Button key="close" onClick={() => setShowClassificationModal(false)}>
            关闭
          </Button>
        ]}
        width={600}
      >
        {classification && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Text strong>一级分类:</Text>
                <br />
                <Tag color={getClassificationColor(classification.level1)} style={{ marginTop: 4 }}>
                  {classification.level1}
                </Tag>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {classification.level1_definition}
                </Text>
              </Col>
              <Col span={8}>
                <Text strong>二级分类:</Text>
                <br />
                <Tag style={{ marginTop: 4 }}>
                  {classification.level2}
                </Tag>
              </Col>
              <Col span={8}>
                <Text strong>三级分类:</Text>
                <br />
                <Tag style={{ marginTop: 4 }}>
                  {classification.level3}
                </Tag>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {classification.level3_definition}
                </Text>
              </Col>
            </Row>
            
            <Divider />
            
            <Row gutter={[16, 8]}>
              <Col span={12}>
                <Text strong>置信度:</Text>
                <br />
                <Progress 
                  percent={Math.round((classification.confidence || 0) * 100)} 
                  size="small"
                  status={classification.confidence > 0.8 ? 'success' : 'normal'}
                />
              </Col>
              <Col span={12}>
                <Text strong>分类时间:</Text>
                <br />
                <Text type="secondary">
                  {classification.classification_time_seconds}秒
                </Text>
              </Col>
            </Row>

            {classification.reasoning && (
              <>
                <Divider />
                <Text strong>分类理由:</Text>
                <Paragraph style={{ marginTop: 8, background: '#f0f0f0', padding: 12, borderRadius: 4 }}>
                  {classification.reasoning}
                </Paragraph>
              </>
            )}
          </div>
        )}
      </Modal>

      {/* 历史记录模态框 */}
      {renderHistoryModal()}

      {/* 变量帮助模态框 */}
      {renderVariableHelpModal()}
    </div>
  );
};

export default EvaluationForm; 