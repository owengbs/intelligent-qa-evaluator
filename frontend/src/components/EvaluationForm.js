import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
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
  Tooltip,
  message,
  DatePicker
} from 'antd';
import { 
  PlayCircleOutlined, 
  ClearOutlined, 
  HistoryOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  CheckOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { submitEvaluation, clearResult, clearError, clearHistory } from '../store/evaluationSlice';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { Title, Text } = Typography;

const EvaluationForm = () => {
  const [form] = Form.useForm();
  const dispatch = useDispatch();
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [loadingDots, setLoadingDots] = useState('');
  const [promptValidation, setPromptValidation] = useState({ isValid: true, missingVars: [] });
  const [variableHelpVisible, setVariableHelpVisible] = useState(false);
  const [forceUpdateKey, setForceUpdateKey] = useState(0);
  
  // 创建TextArea的ref
  const promptTextAreaRef = useRef(null);
  
  // Redux状态
  const { isLoading, result, error, history } = useSelector((state) => state.evaluation);
  
  // 使用useMemo优化必需变量列表，避免无限渲染
  const requiredVariables = useMemo(() => [
    { key: 'user_input', label: '用户输入', description: '用户的原始问题' },
    { key: 'model_answer', label: '模型回答', description: '待评估的模型回答' },
    { key: 'reference_answer', label: '参考答案', description: '标准参考答案' },
    { key: 'question_time', label: '问题时间', description: '问题提出时间' },
    { key: 'evaluation_criteria', label: '评估标准', description: '详细的评估标准和评分规则' }
  ], []);
  
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

  // 验证Prompt中的变量
  const validatePromptVariables = useCallback((promptText) => {
    if (!promptText) {
      setPromptValidation({ isValid: false, missingVars: requiredVariables.map(v => v.key) });
      return;
    }

    const missingVars = requiredVariables.filter(variable => {
      const pattern = new RegExp(`\\{${variable.key}\\}`, 'g');
      return !pattern.test(promptText);
    });

    setPromptValidation({
      isValid: missingVars.length === 0,
      missingVars: missingVars.map(v => v.key)
    });
  }, [requiredVariables]);

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
    return () => clearInterval(interval);
  }, [isLoading]);

  // 初始化表单默认值 - 修复循环依赖问题
  useEffect(() => {
    const defaultEvaluationCriteria = `准确性\t答案与事实完全一致，数据准确无误\t0-4分：完全正确=4分；轻微误差=2分；重大错误=0分
完整性\t回答覆盖问题所有关键信息点\t0-3分：完全覆盖=3分；部分覆盖=1分；未覆盖=0分
流畅性\t语言自然流畅，表达清晰易懂\t0-2分：表达清晰=2分；基本流畅=1分；表达混乱=0分
安全性\t避免有害、误导性或不当内容\t0-1分：安全无害=1分；存在问题=0分`;

    form.setFieldsValue({
      scoringPrompt: defaultScoringPrompt,
      evaluationCriteria: defaultEvaluationCriteria
    });
    // 直接在这里进行初始验证，而不是调用validatePromptVariables
    const missingVars = requiredVariables.filter(variable => {
      const pattern = new RegExp(`\\{${variable.key}\\}`, 'g');
      return !pattern.test(defaultScoringPrompt);
    });

    setPromptValidation({
      isValid: missingVars.length === 0,
      missingVars: missingVars.map(v => v.key)
    });
  }, [form, defaultScoringPrompt, requiredVariables]);

  // 插入变量到Prompt
  const insertVariable = (variableKey) => {
    console.log('🔥 点击插入变量:', variableKey); // 调试信息
    
    const currentPrompt = form.getFieldValue('scoringPrompt') || '';
    console.log('📝 当前prompt长度:', currentPrompt.length); // 调试信息
    console.log('📝 当前prompt前100字符:', currentPrompt.substring(0, 100)); // 调试信息
    
    // 获取textarea的多种方法
    let textArea = null;
    
    // 方法1: 通过ref获取 (Ant Design 5的新结构)
    if (promptTextAreaRef.current) {
      console.log('🔍 ref结构:', promptTextAreaRef.current); // 调试信息
      console.log('🔍 ref类型:', typeof promptTextAreaRef.current); // 调试信息
      console.log('🔍 ref所有属性:', Object.keys(promptTextAreaRef.current)); // 调试信息
      
      // 尝试多种可能的ref结构
      textArea = promptTextAreaRef.current.resizableTextArea?.textArea ||
                promptTextAreaRef.current.input ||
                promptTextAreaRef.current.nativeElement ||
                promptTextAreaRef.current;
      
      console.log('🔍 通过ref找到的textArea:', textArea); // 调试信息
      if (textArea) {
        console.log('🔍 textArea标签名:', textArea.tagName); // 调试信息
        console.log('🔍 textArea类型:', typeof textArea); // 调试信息
      }
    }
    
    // 方法2: 通过DOM查询获取
    if (!textArea || !textArea.tagName || textArea.tagName !== 'TEXTAREA') {
      console.log('🔍 开始DOM查询'); // 调试信息
      const selectors = [
        '[data-testid="prompt-textarea"]',
        'textarea[placeholder="评分规则模板..."]',
        'form textarea:last-of-type',
        '.ant-input',
        'textarea',
        '[name="scoringPrompt"]'
      ];
      
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        console.log(`🔍 选择器 "${selector}" 找到:`, element); // 调试信息
        if (element && element.tagName === 'TEXTAREA') {
          textArea = element;
          console.log('✅ 找到textarea通过选择器:', selector); // 调试信息
          break;
        }
      }
      
      // 如果还没找到，尝试查找所有textarea
      if (!textArea) {
        const allTextareas = document.querySelectorAll('textarea');
        console.log('🔍 页面上所有textarea数量:', allTextareas.length); // 调试信息
        allTextareas.forEach((ta, index) => {
          console.log(`🔍 textarea[${index}]:`, ta.placeholder, ta.name, ta.className); // 调试信息
        });
        
        // 尝试使用最后一个textarea
        if (allTextareas.length > 0) {
          textArea = allTextareas[allTextareas.length - 1];
          console.log('🔍 使用最后一个textarea'); // 调试信息
        }
      }
    }
    
    console.log('🎯 最终找到的textArea:', textArea); // 调试信息
    
    if (textArea && textArea.tagName === 'TEXTAREA') {
      try {
        // 获取光标位置
        const cursorPosition = textArea.selectionStart || 0;
        const textBefore = currentPrompt.substring(0, cursorPosition);
        const textAfter = currentPrompt.substring(cursorPosition);
        const insertText = `{${variableKey}}`;
        const newPrompt = textBefore + insertText + textAfter;
        
        console.log('📍 插入位置:', cursorPosition, '插入文本:', insertText); // 调试信息
        console.log('📄 新prompt长度:', newPrompt.length); // 调试信息
        
        // 方法1: 直接更新DOM元素的值
        textArea.value = newPrompt;
        console.log('✅ DOM值已直接更新'); // 调试信息
        
        // 方法2: 触发原生input事件，让React感知到变化
        const inputEvent = new Event('input', { bubbles: true });
        textArea.dispatchEvent(inputEvent);
        console.log('✅ 已触发input事件'); // 调试信息
        
        // 方法3: 同时更新表单值
        form.setFieldsValue({ scoringPrompt: newPrompt });
        console.log('✅ 表单值已更新'); // 调试信息
        
        // 方法4: 强制触发change事件
        const changeEvent = new Event('change', { bubbles: true });
        textArea.dispatchEvent(changeEvent);
        console.log('✅ 已触发change事件'); // 调试信息
        
        // 方法5: 强制重新渲染组件
        setForceUpdateKey(prev => prev + 1);
        console.log('✅ 已触发强制更新'); // 调试信息
        
        validatePromptVariables(newPrompt);
        
        // 重新设置光标位置和焦点
        setTimeout(() => {
          try {
            const newPosition = cursorPosition + insertText.length;
            textArea.focus();
            if (textArea.setSelectionRange) {
              textArea.setSelectionRange(newPosition, newPosition);
            }
            console.log('✅ 光标位置已更新'); // 调试信息
          } catch (error) {
            console.error('❌ 设置光标位置失败:', error);
          }
        }, 50);
        
        message.success(`✅ 已插入变量 {${variableKey}}`);
        return;
      } catch (error) {
        console.error('❌ 插入变量时出错:', error);
      }
    }
    
    // 如果所有方法都失败，直接在末尾添加
    console.log('🔄 回退到末尾插入模式'); // 调试信息
    const newPrompt = currentPrompt + (currentPrompt.endsWith('\n') ? '' : '\n') + `{${variableKey}}`;
    
    // 尝试直接更新DOM和表单
    if (textArea) {
      textArea.value = newPrompt;
      const inputEvent = new Event('input', { bubbles: true });
      textArea.dispatchEvent(inputEvent);
    }
    
    form.setFieldsValue({ scoringPrompt: newPrompt });
    validatePromptVariables(newPrompt);
    
    // 强制重新渲染组件
    setForceUpdateKey(prev => prev + 1);
    console.log('✅ 末尾插入 - 已触发强制更新'); // 调试信息
    
    message.success(`✅ 已在末尾插入变量 {${variableKey}}`);
  };

  // 渲染变量插入按钮组
  const renderVariableButtons = () => (
    <div style={{ marginBottom: 8 }}>
      <Text strong style={{ marginRight: 12 }}>快速插入变量：</Text>
      <Space wrap>
        {requiredVariables.map(variable => (
          <Tooltip 
            key={variable.key} 
            title={
              <div>
                <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{variable.description}</div>
                <div style={{ fontSize: '12px', opacity: 0.8 }}>
                  支持的变量名：
                  <br />
                  {getVariableAlternatives(variable.key).map(alt => (
                    <Tag key={alt} size="small" style={{ margin: '2px' }}>
                      {`{${alt}}`}
                    </Tag>
                  ))}
                </div>
                <div style={{ fontSize: '11px', marginTop: 4, color: '#1890ff' }}>
                  💡 点击插入到光标位置
                </div>
              </div>
            }
            overlayStyle={{ maxWidth: 300 }}
          >
            <Button
              size="small"
              icon={<PlusOutlined />}
              onClick={() => {
                console.log('按钮被点击:', variable.key);
                insertVariable(variable.key);
              }}
              style={{ 
                borderColor: promptValidation.missingVars.includes(variable.key) ? '#ff4d4f' : '#d9d9d9',
                color: promptValidation.missingVars.includes(variable.key) ? '#ff4d4f' : undefined,
                backgroundColor: promptValidation.missingVars.includes(variable.key) ? '#fff2f0' : undefined,
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'scale(1.05)';
                e.target.style.borderColor = '#1890ff';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'scale(1)';
                e.target.style.borderColor = promptValidation.missingVars.includes(variable.key) ? '#ff4d4f' : '#d9d9d9';
              }}
            >
              {`{${variable.key}}`}
            </Button>
          </Tooltip>
        ))}
        <Tooltip title="查看所有支持的变量名称">
          <Button 
            size="small" 
            type="link"
            onClick={() => setVariableHelpVisible(true)}
            style={{ padding: '4px 8px' }}
          >
            帮助 ?
          </Button>
        </Tooltip>
        <Tooltip title="测试变量插入功能">
          <Button 
            size="small" 
            type="dashed"
            onClick={() => {
              console.log('🧪 测试按钮被点击');
              const testText = ' [测试] ';
              const currentPrompt = form.getFieldValue('scoringPrompt') || '';
              const newPrompt = currentPrompt + testText;
              form.setFieldsValue({ scoringPrompt: newPrompt });
              setForceUpdateKey(prev => prev + 1);
              console.log('✅ 测试按钮 - 已触发强制更新');
              message.info('✅ 测试文本已插入');
            }}
            style={{ padding: '4px 8px', marginLeft: 8 }}
          >
            🧪 测试
          </Button>
        </Tooltip>
      </Space>
    </div>
  );

  // 获取变量的替代名称 - 使用useMemo优化
  const getVariableAlternatives = useMemo(() => {
    const alternatives = {
      'user_input': ['user_input', 'user_query', 'user_question', 'question', 'query'],
      'model_answer': ['model_answer', 'model_response', 'model_output', 'response', 'answer'],
      'reference_answer': ['reference_answer', 'reference', 'standard_answer', 'correct_answer', 'target_answer'],
      'question_time': ['question_time', 'ask_time', 'time', 'timestamp', 'date'],
      'evaluation_criteria': ['evaluation_criteria', 'criteria', 'standards', 'scoring_criteria', 'eval_standards']
    };
    return (variableKey) => alternatives[variableKey] || [variableKey];
  }, []);

  // 渲染变量验证状态
  const renderValidationStatus = () => {
    if (promptValidation.isValid) {
      return (
        <Alert
          message={
            <Space>
              <CheckOutlined style={{ color: '#52c41a' }} />
              <Text>所有必需变量已正确配置</Text>
            </Space>
          }
          type="success"
          showIcon={false}
          style={{ marginTop: 8 }}
        />
      );
    } else {
      return (
        <Alert
          message={
            <Space direction="vertical" size={4}>
              <Space>
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                <Text strong>缺少必需的变量</Text>
              </Space>
              <Text>
                请确保包含以下变量：
                {promptValidation.missingVars.map(varKey => (
                  <Tag key={varKey} color="error" style={{ margin: '0 4px' }}>
                    {`{${varKey}}`}
                  </Tag>
                ))}
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                💡 点击上方按钮可快速插入变量
              </Text>
            </Space>
          }
          type="warning"
          showIcon={false}
          style={{ marginTop: 8 }}
        />
      );
    }
  };

  // 提交评估
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      // 验证Prompt变量
      if (!promptValidation.isValid) {
        message.error('请先修复Prompt模板中缺少的变量');
        return;
      }
      
      // 格式化时间参数
      const formattedValues = {
        ...values,
        questionTime: values.questionTime ? values.questionTime.format('YYYY-MM-DD HH:mm:ss') : dayjs().format('YYYY-MM-DD HH:mm:ss')
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
      scoringPrompt: defaultScoringPrompt,
      evaluationCriteria: defaultEvaluationCriteria
    });
    // 直接设置验证状态，而不是调用validatePromptVariables
    const missingVars = requiredVariables.filter(variable => {
      const pattern = new RegExp(`\\{${variable.key}\\}`, 'g');
      return !pattern.test(defaultScoringPrompt);
    });

    setPromptValidation({
      isValid: missingVars.length === 0,
      missingVars: missingVars.map(v => v.key)
    });
    
    // 强制重新渲染组件
    setForceUpdateKey(prev => prev + 1);
    console.log('✅ 清空表单 - 已触发强制更新');
    
    dispatch(clearResult());
    dispatch(clearError());
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
      title="变量使用帮助"
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
        <Title level={5}>📝 必需变量说明</Title>
        <div style={{ marginBottom: 24 }}>
          {requiredVariables.map(variable => (
            <div key={variable.key} style={{ marginBottom: 16, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
              <div style={{ marginBottom: 8 }}>
                <Text strong>{variable.label}</Text> - <Text type="secondary">{variable.description}</Text>
              </div>
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>支持的变量名：</Text>
                <div style={{ marginTop: 4 }}>
                  {getVariableAlternatives(variable.key).map(alt => (
                    <Tag key={alt} style={{ margin: '2px' }}>
                      {`{${alt}}`}
                    </Tag>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        <Title level={5}>💡 使用示例</Title>
        <div style={{ 
          background: '#f0f0f0', 
          padding: 16, 
          borderRadius: 6, 
          marginBottom: 16,
          fontFamily: 'monospace',
          whiteSpace: 'pre-line',
          fontSize: '13px'
        }}>
{`请评估以下回答的质量：

问题时间: {question_time}
用户问题: {user_input}
模型回答: {model_answer}
参考答案: {reference_answer}

请按照以下标准评分：
1. 准确性 (0-4分) - 特别考虑时间因素
2. 完整性 (0-3分)
3. 流畅性 (0-2分)
4. 安全性 (0-1分)

总分: [分数]/10
评分理由: [详细说明，特别说明时间因素的考虑]`}
        </div>

        <Alert
          message="💡 容错提示"
          description={
            <div>
              <p>系统支持多种变量名写法，即使您使用了不同的变量名，系统也能自动识别：</p>
              <ul style={{ marginLeft: 16, marginBottom: 0 }}>
                <li><code>{`{user_query}`}</code> 会自动替换为用户输入</li>
                <li><code>{`{model_response}`}</code> 会自动替换为模型回答</li>
                <li><code>{`{reference}`}</code> 会自动替换为参考答案</li>
                <li><code>{`{time}`}</code> 会自动替换为问题时间</li>
              </ul>
            </div>
          }
          type="info"
          showIcon
        />
      </div>
    </Modal>
  );

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 24 }}>
      <Card 
        title={
          <Space>
            <Title level={3} style={{ margin: 0 }}>问答质量评估系统</Title>
          </Space>
        } 
        extra={
          <Space>
            {history.length > 0 && (
              <Button 
                icon={<HistoryOutlined />}
                onClick={() => setHistoryModalVisible(true)}
              >
                历史记录 ({history.length})
              </Button>
            )}
          </Space>
        }
        style={{ 
          background: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(10px)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
        }}
      >
        <Form 
          form={form} 
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Form.Item 
                name="userQuery" 
                label="用户输入"
                rules={[{ required: true, message: '请输入用户问题' }]}
              >
                <TextArea 
                  rows={4} 
                  placeholder="请输入用户的原始问题..."
                  showCount
                  maxLength={1000}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} lg={12}>
              <Form.Item 
                name="questionTime" 
                label={
                  <Space>
                    <CalendarOutlined />
                    <span>问题提出时间</span>
                  </Space>
                }
                rules={[{ required: true, message: '请选择问题提出时间' }]}
                extra="选择用户提出该问题的具体时间，有助于模型基于当时的情况进行准确评估"
              >
                <DatePicker 
                  showTime={{ format: 'HH:mm:ss' }}
                  format="YYYY-MM-DD HH:mm:ss"
                  placeholder="选择问题提出时间"
                  style={{ width: '100%' }}
                  defaultValue={dayjs()}
                  disabledDate={(current) => current && current > dayjs().endOf('day')}
                />
              </Form.Item>
            </Col>
            
            <Col span={24}>
              <Form.Item 
                name="evaluationCriteria" 
                label="评估标准"
                rules={[{ required: true, message: '请输入详细的评估标准' }]}
                extra="定义具体的评分维度、要求和评分标准，格式示例：准确性 - 具体要求 - 评分标准"
              >
                <TextArea 
                  rows={6} 
                  placeholder={`请输入详细的评估标准，例如：

准确性	指数涨跌幅、行业数据与交易所一致	0-4分：数据完全正确=4分；小幅误差（±0.5%）=2分；重大错误=0分
相关性	回答需关联问题范围（如"牛市"需结合经济周期、成交量等）	0-3分：紧密关联=3分；部分关联=1分；无关=0分
可用性	提供关键指标对比（如行业PE分位数、资金流入排名）	0-3分：提供≥3项指标=3分；1-2项=1分；无指标=0分
合规性	避免绝对结论（如"必定进入牛市"）	0-2分：措辞谨慎=2分；存在绝对化表述=0分`}
                  showCount
                  maxLength={2000}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} lg={12}>
              <Form.Item 
                name="referenceAnswer" 
                label="参考标准答案"
                rules={[{ required: true, message: '请输入参考答案' }]}
              >
                <TextArea 
                  rows={4} 
                  placeholder="请输入参考的标准答案..."
                  showCount
                  maxLength={2000}
                />
              </Form.Item>
            </Col>
            
            <Col xs={24} lg={12}>
              <Form.Item 
                name="modelResponse" 
                label="模型答案"
                rules={[{ required: true, message: '请输入待评估的模型回答' }]}
              >
                <TextArea 
                  rows={4} 
                  placeholder="请输入待评估的模型回答..."
                  showCount
                  maxLength={3000}
                />
              </Form.Item>
            </Col>
            
            <Col span={24}>
              <Form.Item 
                name="scoringPrompt" 
                label="打分规则 (Prompt模板)"
                extra="使用下方按钮插入必需的变量，确保评估正确执行"
              >
                <div>
                  {renderVariableButtons()}
                  <TextArea 
                    key={`prompt-textarea-${forceUpdateKey}`}
                    ref={promptTextAreaRef}
                    rows={8} 
                    placeholder="评分规则模板..."
                    showCount
                    value={form.getFieldValue('scoringPrompt')}
                    onChange={(e) => {
                      form.setFieldsValue({ scoringPrompt: e.target.value });
                      validatePromptVariables(e.target.value);
                    }}
                    style={{
                      borderColor: promptValidation.isValid ? undefined : '#ff4d4f'
                    }}
                    data-testid="prompt-textarea"
                  />
                  {renderValidationStatus()}
                </div>
              </Form.Item>
            </Col>
          </Row>
          
          <Divider />
          
          <Space size="large">
            <Button 
              type="primary" 
              size="large"
              icon={<PlayCircleOutlined />}
              loading={isLoading}
              onClick={handleSubmit}
              disabled={!promptValidation.isValid}
            >
              {isLoading ? '评估中...' : '开始评估'}
            </Button>
            
            <Button 
              icon={<ClearOutlined />}
              onClick={handleClear}
              disabled={isLoading}
              size="large"
            >
              清空表单
            </Button>
          </Space>
          
          {/* 评估时间提示 */}
          {!isLoading && (
            <div style={{ marginTop: 16 }}>
              <Alert
                message="💡 温馨提示"
                description="大模型评估通常需要 30-120 秒，请耐心等待。评估时间取决于内容复杂度。"
                type="info"
                showIcon
                style={{ marginBottom: 0 }}
              />
            </div>
          )}
        </Form>
      </Card>
      
      {/* 评估结果显示区域 */}
      <Spin spinning={isLoading} tip={renderLoadingTip()}>
        {renderResult()}
      </Spin>
      
      {/* 历史记录模态框 */}
      {renderHistoryModal()}
      
      {/* 变量帮助模态框 */}
      {renderVariableHelpModal()}
    </div>
  );
};

export default EvaluationForm; 