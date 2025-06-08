import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Badge,
  InputNumber,
  Upload,
  Image,
  Tooltip
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
  SendOutlined,
  PictureOutlined,
  DeleteOutlined,
  ScanOutlined
} from '@ant-design/icons';
import { submitEvaluation, clearResult, clearError, clearHistory } from '../store/evaluationSlice';
import dayjs from 'dayjs';
import axios from 'axios';
import { 
  recognizeText, 
  recognizeTextSimple,
  extractImageFromPaste, 
  isValidImageFile, 
  isValidFileSize, 
  createImagePreviewUrl, 
  revokeImagePreviewUrl,
  getOCRProgressText
} from '../utils/ocrProcessor';

// 导入本地化OCR处理器
import { 
  smartOCRRecognize,
  testNetworkConnectivity
} from '../utils/ocrProcessorLocal';

// 导入超简单OCR处理器（修复序列化问题）
import { 
  recognizeTextWithProgress,
  preloadOCRResources,
  checkOCRAvailability
} from '../utils/ocrProcessorSimple';

// 导入修复版OCR处理器
import { 
  recognizeTextFixed,
  preloadOCRResourcesFixed,
  testOCRFunction
} from '../utils/ocrProcessorFixed';

// 开发模式下导入诊断工具
if (process.env.NODE_ENV === 'development') {
  import('../utils/ocrDiagnostic').then(() => {
    console.log('🔧 OCR诊断工具已加载，可在控制台使用 window.ocrDiagnostic');
  });
}

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

// 配置axios baseURL - 使用环境变量中的API地址
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const api = axios.create({
  baseURL: API_BASE_URL,
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
  
  // 人工评估相关状态
  const [humanEvaluationVisible, setHumanEvaluationVisible] = useState(false);
  const [humanEvaluationLoading, setHumanEvaluationLoading] = useState(false);
  const [humanForm] = Form.useForm();
  const [currentHistoryId, setCurrentHistoryId] = useState(null);
  
  // 图片识别相关状态
  const [ocrLoading, setOcrLoading] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [ocrProgress, setOcrProgress] = useState(0);
  // eslint-disable-next-line no-unused-vars
  const [currentImageFile, setCurrentImageFile] = useState(null);
  
  // 强制刷新状态
  const [forceRenderKey, setForceRenderKey] = useState(0);
  const [modelResponseValue, setModelResponseValue] = useState('');
  
  // 图片历史记录状态
  const [uploadedImages, setUploadedImages] = useState([]);
  
  // Redux状态
  const { isLoading, result, error, history } = useSelector((state) => state.evaluation);

  // 添加防重复提交状态跟踪
  const [humanEvaluationSubmitting, setHumanEvaluationSubmitting] = useState(false);
  const [lastSubmissionTime, setLastSubmissionTime] = useState(0);

  // 图片识别处理函数
  const handleImageUpload = async (file) => {
    try {
      // 验证文件类型和大小
      if (!isValidImageFile(file)) {
        message.error('请上传PNG、JPG或JPEG格式的图片');
        return false;
      }

      if (!isValidFileSize(file, 5)) {
        message.error('图片大小不能超过5MB');
        return false;
      }

      // 清理之前的预览URL
      if (imagePreview) {
        revokeImagePreviewUrl(imagePreview);
      }

      // 上传图片到服务器
      console.log('📤 开始上传图片到服务器...');
      const uploadedImageInfo = await uploadImageToServer(file);
      
      if (!uploadedImageInfo) {
        message.error('图片上传失败，请重试');
        return false;
      }

      // 设置预览URL（使用服务器URL）
      setImagePreview(uploadedImageInfo.url);
      setCurrentImageFile(file);

      // 保存图片信息到历史记录
      const imageInfo = {
        id: uploadedImageInfo.id,
        name: uploadedImageInfo.name,
        size: uploadedImageInfo.size,
        type: uploadedImageInfo.type,
        previewUrl: uploadedImageInfo.url, // 使用服务器URL
        uploadTime: uploadedImageInfo.upload_time,
        ocrText: '', // 将在OCR识别后更新
        filename: uploadedImageInfo.filename
      };
      
      setUploadedImages(prev => [...prev, imageInfo]);
      message.success('图片上传成功！');

      // 开始OCR识别
      await performOCR(file, imageInfo.id);
      
      return false; // 阻止Upload组件的默认上传行为
    } catch (error) {
      console.error('图片处理失败:', error);
      message.error('图片处理失败');
      return false;
    }
  };

  // 上传图片到服务器
  const uploadImageToServer = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/upload/image`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      
      if (result.success) {
        console.log('✅ 图片上传成功:', result.data);
        return result.data;
      } else {
        console.error('❌ 图片上传失败:', result.message);
        message.error(result.message);
        return null;
      }
    } catch (error) {
      console.error('❌ 图片上传请求失败:', error);
      message.error('网络请求失败，请检查网络连接');
      return null;
    }
  };

  // 执行OCR识别
  const performOCR = async (file, imageId = null) => {
    try {
      setOcrLoading(true);
      setOcrProgress(0);

      console.log('🚀 开始超简单OCR识别流程...');

      // 使用超简单OCR识别（避免序列化问题）
      console.log('🔍 开始OCR识别，文件信息:', {
        name: file.name,
        size: file.size,
        type: file.type
      });

      const recognizedText = await recognizeTextFixed(file, {
        onProgress: (progress) => {
          console.log(`📈 OCR进度更新: ${progress}%`);
          setOcrProgress(progress);
        },
        timeout: 120000 // 2分钟超时
      });

      console.log('📄 OCR识别原始结果:', {
        text: recognizedText,
        length: recognizedText ? recognizedText.length : 0,
        hasContent: !!(recognizedText && recognizedText.trim())
      });

      if (recognizedText && recognizedText.trim()) {
        // 更新图片历史记录中的OCR文本
        if (imageId) {
          setUploadedImages(prev => prev.map(img => 
            img.id === imageId 
              ? { ...img, ocrText: recognizedText }
              : img
          ));
        }
        
        // 获取当前模型回答的值
        const currentModelResponse = form.getFieldValue('modelResponse') || '';
        console.log('📝 当前表单内容:', currentModelResponse);
        
        // 如果当前有内容，在末尾添加识别的文字，否则直接设置
        const newText = currentModelResponse 
          ? `${currentModelResponse}\n\n${recognizedText}` 
          : recognizedText;
        
        console.log('📝 准备填入的新内容:', newText);
        
        // 使用专门的填入函数
        const fillSuccess = await fillModelResponseText(newText);
        
        if (!fillSuccess) {
          console.error('❌ 自动填入失败');
          message.warning({
            content: `自动填入失败，请手动复制以下内容：${newText}`,
            duration: 10,
            style: { marginTop: '100px' }
          });
          
          // 复制到剪贴板作为备选方案
          try {
            await navigator.clipboard.writeText(newText);
            message.info('✅ 文本已复制到剪贴板，请手动粘贴到模型回答框');
          } catch (clipboardError) {
            console.warn('剪贴板复制失败:', clipboardError);
          }
        }

        message.success(`✅ OCR识别成功！已添加 ${recognizedText.length} 个字符到模型回答中`);
        console.log('📄 最终识别结果:', recognizedText);
        
      } else {
        console.warn('⚠️ OCR识别结果为空或仅包含空白字符');
        message.warning('未识别到任何文字，请尝试使用更清晰的图片或检查图片中是否包含文字内容');
      }
      
    } catch (error) {
      console.error('❌ OCR识别失败:', error);
      
      // 根据错误类型提供不同的建议
      let errorMsg = error.message;
      if (error.message.includes('网络')) {
        errorMsg += '\n💡 建议：检查网络连接，或尝试使用手机热点';
      } else if (error.message.includes('超时')) {
        errorMsg += '\n💡 建议：图片可能过大，请尝试压缩图片后重新上传';
      }
      
      message.error(`OCR识别失败: ${errorMsg}`);
    } finally {
      setOcrLoading(false);
      setOcrProgress(0);
    }
  };

  // 处理粘贴图片事件
  const handleTextAreaPaste = async (event) => {
    const imageFile = extractImageFromPaste(event);
    if (imageFile) {
      event.preventDefault(); // 阻止默认粘贴行为
      await handlePastedImageUpload(imageFile);
    }
  };

  // 处理粘贴的图片上传
  const handlePastedImageUpload = async (file) => {
    try {
      console.log('📋 处理粘贴的图片:', file);
      
      // 使用base64方式上传粘贴的图片
      const base64Data = await fileToBase64(file);
      const uploadedImageInfo = await uploadBase64ImageToServer(base64Data, file.name);
      
      if (!uploadedImageInfo) {
        message.error('粘贴图片上传失败，请重试');
        return;
      }

      // 保存图片信息到历史记录
      const imageInfo = {
        id: uploadedImageInfo.id,
        name: uploadedImageInfo.name,
        size: uploadedImageInfo.size,
        type: uploadedImageInfo.type,
        previewUrl: uploadedImageInfo.url,
        uploadTime: uploadedImageInfo.upload_time,
        ocrText: '',
        filename: uploadedImageInfo.filename
      };
      
      setUploadedImages(prev => [...prev, imageInfo]);
      message.success('粘贴图片上传成功！');

      // 开始OCR识别
      await performOCR(file, imageInfo.id);
      
    } catch (error) {
      console.error('粘贴图片处理失败:', error);
      message.error('粘贴图片处理失败');
    }
  };

  // 文件转base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  // 上传base64图片到服务器
  const uploadBase64ImageToServer = async (base64Data, filename) => {
    try {
      const response = await fetch(`${API_BASE_URL}/upload/image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imageData: base64Data,
          filename: filename || 'pasted_image.png'
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        console.log('✅ Base64图片上传成功:', result.data);
        return result.data;
      } else {
        console.error('❌ Base64图片上传失败:', result.message);
        message.error(result.message);
        return null;
      }
    } catch (error) {
      console.error('❌ Base64图片上传请求失败:', error);
      message.error('网络请求失败，请检查网络连接');
      return null;
    }
  };

  // 清空图片
  const clearImage = () => {
    if (imagePreview) {
      revokeImagePreviewUrl(imagePreview);
    }
    setImagePreview(null);
    setCurrentImageFile(null);
    setOcrLoading(false);
    setOcrProgress(0);
  };

    // 专门的表单填入函数 - 使用React状态强制刷新
  const fillModelResponseText = (text) => {
    console.log('🎯 开始填入文本到模型回答框:', text);
    
    return new Promise((resolve) => {
      try {
        // 直接更新React状态 - 现在是受控组件
        console.log('📋 更新React状态和表单');
        
        // 1. 更新状态
        setModelResponseValue(text);
        
        // 2. 更新表单
        form.setFieldsValue({ modelResponse: text });
        
        // 3. 强制重新渲染
        setForceRenderKey(prev => prev + 1);
        
        console.log('✅ 状态更新完成');
        
        // 验证更新是否成功
        setTimeout(() => {
          const formValue = form.getFieldValue('modelResponse');
          const stateValue = text; // modelResponseValue should be updated
          
          console.log('🔍 验证结果:', {
            formValue,
            stateValue,
            expected: text,
            formMatch: formValue === text,
            stateMatch: stateValue === text
          });
          
          // 由于是受控组件，状态更新应该立即反映在UI上
          resolve(true);
        }, 100);
        
      } catch (error) {
        console.error('❌ 填入过程出错:', error);
        resolve(false);
      }
    });
  };

  // 组件卸载时清理资源
  useEffect(() => {
    return () => {
      if (imagePreview) {
        revokeImagePreviewUrl(imagePreview);
      }
    };
  }, [imagePreview]);

  // 动态生成评分prompt - 根据评估标准自动生成维度评分要求
  const generateScoringPrompt = (evaluationCriteria) => {
    // 解析评估标准，提取维度信息
    const lines = evaluationCriteria.split('\n').filter(line => line.trim());
    const dimensions = [];
    
    lines.forEach(line => {
      const parts = line.split('\t');
      if (parts.length >= 3) {
        const dimensionName = parts[0].trim();
        const description = parts[1].trim();
        const scoringRule = parts[2].trim();
        
        // 提取最大分数
        let maxScore = 5; // 默认值
        const scoreMatch = scoringRule.match(/(\d+)-(\d+)分|(\d+)分/);
        if (scoreMatch) {
          maxScore = parseInt(scoreMatch[2] || scoreMatch[3] || scoreMatch[1]);
        }
        
        dimensions.push({
          name: dimensionName,
          description: description,
          scoringRule: scoringRule,
          maxScore: maxScore
        });
      }
    });

    if (dimensions.length === 0) {
      console.warn('未解析到维度信息，使用默认维度');
      // 如果解析失败，使用默认维度
      return `请根据以下详细的评估标准对回答质量进行严格评分：

评估标准：
{evaluation_criteria}

请严格按照以下格式返回评估结果:
总分: [分数]/10

各维度评分:
数据准确性: [分数] 分 - [评分理由]
数据时效性: [分数] 分 - [评分理由]
内容完整性: [分数] 分 - [评分理由]
用户视角: [分数] 分 - [评分理由]

评分理由: [详细的多行评分分析]`;
    }

    // 生成维度评分要求，明确格式
    const dimensionRequirements = dimensions.map(dim => 
      `${dim.name}: [0-${dim.maxScore}分] - [评分理由]`
    ).join('\n');

    return `请根据以下详细的评估标准对回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 严格按照上述评估标准进行评分，不得放宽标准
2. 特别注意问题提出时间 {question_time}，时效性判断要求严格
3. 任何信息错误都应严重扣分，时间敏感内容要求更高
4. 回答质量评判从严，避免给出过高分数
5. 只有真正优秀的回答才能获得高分
6. 必须为每个评估维度提供具体分数，不得模糊评分

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

维度详细说明：
${dimensions.map(dim => `• ${dim.name}（最高${dim.maxScore}分）：${dim.description}`).join('\n')}

评估要求：
1. 必须为以下每个维度都给出具体分数
2. 分数必须在对应维度的最大分数范围内
3. 按照标准格式输出，方便系统解析

请严格按照以下格式返回评估结果（重要：格式必须完全一致）:

各维度评分:
${dimensionRequirements}

总分: [各维度分数之和]/10

评分理由: [详细的多行评分分析，必须说明扣分理由，按照评估标准逐项说明每个维度的评分理由和存在的问题，特别注明时间因素的考虑]`;
  };

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
      
      // 动态生成适配当前评估标准的scoring_prompt
      const dynamicScoringPrompt = generateScoringPrompt(values.evaluationCriteria);
      
      // 映射前端字段名到后端API期望的字段名
      const formattedValues = {
        user_input: values.userQuery,  // userQuery -> user_input
        model_answer: values.modelResponse,  // modelResponse -> model_answer
        reference_answer: values.referenceAnswer || '',  // referenceAnswer -> reference_answer
        question_time: values.questionTime ? values.questionTime.format('YYYY-MM-DD HH:mm:ss') : dayjs().format('YYYY-MM-DD HH:mm:ss'),
        evaluation_criteria: values.evaluationCriteria,  // evaluationCriteria -> evaluation_criteria
        scoring_prompt: dynamicScoringPrompt,  // 使用动态生成的scoring_prompt
        uploaded_images: uploadedImages  // 添加图片历史记录
      };
      
      console.log('表单验证通过，提交评估:', formattedValues);
      console.log('动态生成的评估prompt:', dynamicScoringPrompt);
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
    setClassification(null);
    clearImage(); // 清理图片状态
    setUploadedImages([]); // 清理图片历史记录
  };

  // 人工评估维度组件
  const HumanEvaluationDimensions = ({ classification, result }) => {
    const [dimensions, setDimensions] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    
    React.useEffect(() => {
      const fetchDimensions = async () => {
        if (!classification || !classification.level2) {
          setLoading(false);
          return;
        }
        
        try {
          // 使用评估模板API获取新维度体系
          const templateResponse = await api.get(`/evaluation-template/${classification.level2}`);
          if (templateResponse.data.success && templateResponse.data.data) {
            const templateData = templateResponse.data.data;
            setDimensions(templateData.dimensions || []);
          } else {
            setDimensions([]);
          }
        } catch (error) {
          console.error('获取维度标准失败:', error);
          message.error('获取维度标准失败');
          setDimensions([]);
        } finally {
          setLoading(false);
        }
      };
      
      fetchDimensions();
    }, [classification]);
    
    if (loading) {
      return <Spin tip="加载维度信息..." />;
    }
    
    if (dimensions.length === 0) {
      return (
        <Alert
          type="warning"
          message="暂无维度配置"
          description={`当前分类「${classification?.level2 || '未知'}」尚未配置评估维度，请先在标准配置页面进行配置。`}
        />
      );
    }
    
    return (
      <>
        <Divider orientation="left">各维度分数调整</Divider>
        <Row gutter={[16, 16]}>
          {dimensions.map((dimension) => {
            // 获取AI评分（如果有的话）
            const aiScore = result.dimensions && result.dimensions[dimension.name] 
              ? result.dimensions[dimension.name] 
              : 0;
            
            // 使用新维度体系的最大分数
            const maxScore = dimension.max_score || 2;
            
            return (
              <Col span={8} key={dimension.name}>
                <Form.Item
                  label={
                    <Tooltip title={`${dimension.reference_standard}\n\n评分原则：${dimension.scoring_principle}`}>
                      {dimension.name} (AI评分: {aiScore}/{maxScore})
                    </Tooltip>
                  }
                  name={`dimension_${dimension.name}`}
                  rules={[
                    { required: true, message: `请输入${dimension.name}分数` },
                    { type: 'number', min: 0, max: maxScore, message: `分数应在0-${maxScore}之间` }
                  ]}
                >
                  <InputNumber 
                    step={0.1} 
                    min={0} 
                    max={maxScore} 
                    placeholder={`0-${maxScore}分`}
                    style={{ width: '100%' }}
                  />
                </Form.Item>
              </Col>
            );
          })}
        </Row>
      </>
    );
  };

  // 人工评估相关函数
  const handleHumanEvaluation = async () => {
    if (!result || !result.history_id) {
      message.error('无法获取评估记录ID，请重新评估');
      return;
    }
    
    if (!classification || !classification.level2) {
      message.error('无法获取分类信息，请重新分类');
      return;
    }
    
    setCurrentHistoryId(result.history_id);
    
    try {
      // 获取当前分类的评估模板（新维度体系）
      const templateResponse = await api.get(`/evaluation-template/${classification.level2}`);
      
      if (!templateResponse.data.success || !templateResponse.data.data) {
        message.error('该分类暂无配置的评估维度');
        return;
      }
      
      const templateData = templateResponse.data.data;
      const dimensions = templateData.dimensions || [];
      
      // 初始化人工评估表单
      const initialValues = {
        human_total_score: result.score,
        human_reasoning: '',
        evaluator_name: '评估专家'
      };
      
      // 为每个维度初始化分数
      dimensions.forEach((dimension) => {
        // 优先使用AI评估结果，如果没有则使用0
        const aiScore = result.dimensions && result.dimensions[dimension.name] 
          ? result.dimensions[dimension.name] 
          : 0;
        initialValues[`dimension_${dimension.name}`] = aiScore;
      });
      
      humanForm.setFieldsValue(initialValues);
      setHumanEvaluationVisible(true);
      
    } catch (error) {
      console.error('获取评估模板失败:', error);
      message.error('获取评估标准失败，请重试');
    }
  };

  const handleHumanEvaluationSubmit = async () => {
    // 防重复提交检查
    const now = Date.now();
    if (humanEvaluationSubmitting) {
      message.warning('正在提交中，请勿重复点击');
      return;
    }
    
    if (now - lastSubmissionTime < 3000) { // 3秒内不允许重复提交
      message.warning('提交过于频繁，请稍后再试');
      return;
    }
    
    try {
      setHumanEvaluationSubmitting(true);
      setLastSubmissionTime(now);
      setHumanEvaluationLoading(true);
      
      const values = await humanForm.validateFields();
      
      // 构建人工评估数据
      const humanData = {
        human_total_score: values.human_total_score,
        human_reasoning: values.human_reasoning,
        evaluator_name: values.evaluator_name || '评估专家'
      };
      
      // 收集各维度分数
      const humanDimensions = {};
      Object.keys(values).forEach(key => {
        if (key.startsWith('dimension_')) {
          const dimensionKey = key.replace('dimension_', '');
          humanDimensions[dimensionKey] = values[key];
        }
      });
      
      if (Object.keys(humanDimensions).length > 0) {
        humanData.human_dimensions = humanDimensions;
      }
      
      // 调用API更新人工评估 - 只调用一次，使用PUT方法
      console.log('提交人工评估数据:', humanData);
      const response = await api.put(`/evaluation-history/${currentHistoryId}/human-evaluation`, humanData);
      
      if (response.data.success) {
        message.success('人工评估保存成功');
        setHumanEvaluationVisible(false);
        
        // 人工评估成功后，数据已保存到数据库
        // 用户可以重新评估查看更新后的结果
        
      } else {
        message.error(response.data.message || '人工评估保存失败');
      }
      
    } catch (error) {
      console.error('人工评估提交失败:', error);
      message.error('人工评估提交失败，请重试');
    } finally {
      setHumanEvaluationLoading(false);
      setHumanEvaluationSubmitting(false);
    }
  };

  const renderHumanEvaluationModal = () => {
    if (!result) return null;
    
    return (
      <Modal
        title={
          <Space>
            <span style={{ fontSize: '20px' }}>👨‍💼</span>
            人工评估修正
          </Space>
        }
        open={humanEvaluationVisible}
        onCancel={() => setHumanEvaluationVisible(false)}
        onOk={handleHumanEvaluationSubmit}
        okText="保存评估"
        cancelText="取消"
        width={800}
        confirmLoading={humanEvaluationLoading}
        okButtonProps={{
          disabled: humanEvaluationSubmitting, // 添加禁用状态防止重复点击
          loading: humanEvaluationLoading
        }}
      >
        <div style={{ marginBottom: 16 }}>
          <Alert
            message="人工评估说明"
            description="您可以基于AI评估结果进行调整和修正，补充您的专业评估意见。修改后的评估结果将保存为最终评估结果。"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </div>
        
        <Form
          form={humanForm}
          layout="vertical"
          initialValues={{
            human_total_score: result.score,
            evaluator_name: '评估专家'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="评估者姓名"
                name="evaluator_name"
                rules={[{ required: true, message: '请输入评估者姓名' }]}
              >
                <Input placeholder="请输入您的姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="人工总分"
                name="human_total_score"
                rules={[
                  { required: true, message: '请输入总分' },
                  { type: 'number', min: 0, max: 10, message: '总分应在0-10之间' }
                ]}
              >
                <InputNumber 
                  step={0.1} 
                  min={0} 
                  max={10} 
                  placeholder="0-10分"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          
          {/* 各维度分数调整 - 基于新的维度体系 */}
          <HumanEvaluationDimensions 
            classification={classification}
            result={result}
          />
          
          <Form.Item
            label="人工评估意见"
            name="human_reasoning"
            rules={[{ required: true, message: '请输入您的评估意见' }]}
          >
            <TextArea
              rows={6}
              placeholder="请详细说明您的评估理由，包括与AI评估的差异原因、专业判断依据等..."
            />
          </Form.Item>
        </Form>
      </Modal>
    );
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
          📸 上传图片 ({images.length}张)
        </Text>
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '8px',
          maxHeight: '200px',
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
                width={80}
                height={80}
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
                      <Text style={{ fontSize: '10px', color: 'white' }}>查看</Text>
                    </div>
                  )
                }}
              />
              {image.ocrText && (
                <Tooltip 
                  title={
                    <div>
                      <Text strong style={{ color: '#fff' }}>OCR识别结果:</Text>
                      <br />
                      <Text style={{ color: '#fff' }}>
                        {image.ocrText.length > 100 
                          ? `${image.ocrText.substring(0, 100)}...` 
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
                    width: '16px',
                    height: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '10px',
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
            <span>总大小 {(images.reduce((sum, img) => sum + img.size, 0) / 1024 / 1024).toFixed(2)} MB</span>
          </Space>
        </div>
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
      width={1000}
      style={{ top: 20 }}
    >
      <List
        dataSource={history}
        renderItem={(item, index) => (
          <List.Item
            style={{ 
              padding: '16px',
              border: '1px solid #f0f0f0',
              borderRadius: '8px',
              marginBottom: '12px',
              background: '#fafafa'
            }}
            actions={[
              <Button 
                size="small" 
                icon={<EyeOutlined />}
                type="primary"
                ghost
                onClick={() => {
                  form.setFieldsValue({
                    userQuery: item.raw_response?.split('用户输入:')[1]?.split('模型回答:')[0]?.trim() || '',
                    modelResponse: item.raw_response?.split('模型回答:')[1]?.split('参考答案:')[0]?.trim() || '',
                    referenceAnswer: item.raw_response?.split('参考答案:')[1]?.trim() || ''
                  });
                  
                  // 恢复图片历史记录
                  if (item.uploaded_images && item.uploaded_images.length > 0) {
                    setUploadedImages(item.uploaded_images);
                    message.info(`已恢复 ${item.uploaded_images.length} 张历史图片`);
                  } else {
                    setUploadedImages([]);
                  }
                  
                  setHistoryModalVisible(false);
                }}
              >
                载入此记录
              </Button>
            ]}
          >
            <List.Item.Meta
              title={
                <Space align="start">
                  <div>
                    <Space>
                      <Text strong>评估记录 #{index + 1}</Text>
                      <Tag color={getScoreLevel(item.score).color}>
                        {item.score}/10 - {getScoreLevel(item.score).text}
                      </Tag>
                    </Space>
                    <div style={{ marginTop: '4px' }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {item.timestamp}
                      </Text>
                    </div>
                  </div>
                </Space>
              }
              description={
                <div style={{ marginTop: '8px' }}>
                  {/* 评估理由摘要 */}
                  <div style={{ marginBottom: '8px' }}>
                    <Text>
                      {item.reasoning?.substring(0, 150)}
                      {item.reasoning && item.reasoning.length > 150 ? '...' : ''}
                    </Text>
                  </div>
                  
                  {/* 图片历史展示 */}
                  {renderImageHistory(item.uploaded_images)}
                  
                  {/* 维度分数简要展示 */}
                  {item.dimensions && Object.keys(item.dimensions).length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        📊 维度得分: 
                      </Text>
                      <Space size="small" style={{ marginLeft: '8px' }}>
                        {Object.entries(item.dimensions).map(([key, value]) => {
                          // 使用动态维度名称获取函数
                          const displayName = getDimensionDisplayName(key, item.evaluation_criteria || '');
                          return (
                            <Tag size="small" key={key} color="blue">
                              {displayName}: {value}
                            </Tag>
                          );
                        })}
                      </Space>
                    </div>
                  )}
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
        extra={
          <Space>
            <Button
              type="primary"
              ghost
              size="small"
              icon={<span style={{ fontSize: '14px' }}>👨‍💼</span>}
              onClick={handleHumanEvaluation}
            >
              人工评估
            </Button>
            <Text type="secondary">{new Date(result.timestamp).toLocaleString()}</Text>
          </Space>
        }
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
              <Title level={5} style={{ marginBottom: 16, color: '#1890ff' }}>
                📊 各维度评分详情
              </Title>
              <Row gutter={[16, 16]}>
                {Object.entries(result.dimensions).map(([key, value]) => {
                  // 扩展的维度名称映射，支持更多维度
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
                  
                  // 扩展的维度图标映射
                  const dimensionIcons = {
                    accuracy: '🎯',
                    completeness: '📋',
                    fluency: '💬',
                    safety: '🛡️',
                    relevance: '🔗',
                    clarity: '💡',
                    timeliness: '⏰',
                    usability: '⚡',
                    compliance: '✅'
                  };
                  
                  // 从表单获取评估标准文本，动态解析最大分数
                  const criteriaText = form.getFieldValue('evaluationCriteria') || '';
                  const maxScore = getDimensionMaxScore(key, criteriaText);
                  const percentage = Math.round((value / maxScore) * 100);
                  
                  // 显示名称：优先使用映射，否则使用原始key（首字母大写）
                  const displayName = dimensionNames[key] || key.charAt(0).toUpperCase() + key.slice(1);
                  const icon = dimensionIcons[key] || '📈';
                  
                  return (
                    <Col xs={24} sm={12} lg={6} key={key}>
                      <Card
                        size="small"
                        style={{
                          background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)',
                          border: '1px solid #e8f4fd',
                          borderRadius: '12px',
                          height: '120px',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'center'
                        }}
                        bodyStyle={{ padding: '16px' }}
                      >
                        <div style={{ textAlign: 'center' }}>
                          <div style={{ 
                            fontSize: '24px', 
                            marginBottom: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px'
                          }}>
                            <span>{icon}</span>
                            <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                              {displayName}
                            </Text>
                          </div>
                          
                          <div style={{ marginBottom: '8px' }}>
                            <Text style={{ 
                              fontSize: '20px', 
                              fontWeight: 'bold',
                              color: getScoreColor((value / maxScore) * 10)
                            }}>
                              {value}
                            </Text>
                            <Text type="secondary" style={{ fontSize: '14px' }}>
                              /{maxScore}
                            </Text>
                          </div>
                          
                          <Progress
                            percent={percentage}
                            size="small"
                            strokeColor={{
                              '0%': percentage >= 80 ? '#52c41a' : percentage >= 60 ? '#1890ff' : percentage >= 40 ? '#faad14' : '#ff4d4f',
                              '100%': percentage >= 80 ? '#73d13d' : percentage >= 60 ? '#40a9ff' : percentage >= 40 ? '#ffc53d' : '#ff7875',
                            }}
                            showInfo={false}
                            strokeWidth={6}
                            style={{ marginBottom: '4px' }}
                          />
                          
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {percentage}%
                          </Text>
                        </div>
                      </Card>
                    </Col>
                  );
                })}
              </Row>
              
              {/* 添加维度评分总览 */}
              <div style={{ 
                marginTop: 16, 
                padding: '12px 16px',
                background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)',
                borderRadius: '8px',
                border: '1px solid #91d5ff'
              }}>
                <Row align="middle" gutter={16}>
                  <Col>
                    <Text strong style={{ color: '#1890ff' }}>
                      📈 综合表现:
                    </Text>
                  </Col>
                  <Col flex="auto">
                    {Object.entries(result.dimensions).map(([key, value], index) => {
                      // 使用相同的维度名称映射
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
                      
                      const criteriaText = form.getFieldValue('evaluationCriteria') || '';
                      const maxScore = getDimensionMaxScore(key, criteriaText);
                      const percentage = (value / maxScore) * 100;
                      const displayName = dimensionNames[key] || key.charAt(0).toUpperCase() + key.slice(1);
                      
                      return (
                        <Tag
                          key={key}
                          color={percentage >= 80 ? 'success' : percentage >= 60 ? 'processing' : percentage >= 40 ? 'warning' : 'error'}
                          style={{ margin: '2px 4px 2px 0', fontSize: '12px' }}
                        >
                          {displayName}: {value}/{maxScore}
                        </Tag>
                      );
                    })}
                  </Col>
                </Row>
              </div>
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
      const response = await api.post('/classify', {
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
      const response = await api.get(`/evaluation-template/${level2Category}`);
      
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
    
    // 创建更友好的格式化文本，同时保持tab分隔的兼容性
    const formattedLines = template.dimensions.map(dimension => {
      // 基本信息行
      const basicInfo = `${dimension.name}\t${dimension.reference_standard}\t${dimension.scoring_principle}`;
      
      // 添加友好的显示格式
      const friendlyFormat = `
📊 维度名称：${dimension.name} (最高${dimension.max_score}分)
📋 参考标准：${dimension.reference_standard}
⚖️  评分原则：${dimension.scoring_principle}

具体评分等级：`;
      
      // 添加具体的评分等级
      let criteriaDetails = '';
      if (dimension.evaluation_criteria && Array.isArray(dimension.evaluation_criteria)) {
        criteriaDetails = dimension.evaluation_criteria
          .sort((a, b) => b.score - a.score) // 按分数降序排列
          .map(criteria => `  • ${criteria.level} (${criteria.score}分)：${criteria.description}`)
          .join('\n');
      }
      
      return basicInfo + '\n' + friendlyFormat + '\n' + criteriaDetails;
    });
    
    // 创建完整的友好格式
    const friendlyHeader = `🎯 评估标准配置 (总分：${template.total_max_score}分)
📝 分类：${template.level2_category}
⏰ 更新时间：${new Date().toLocaleString()}

═══════════════════════════════════════════`;
    
    const basicTabFormat = template.dimensions
      .map(dimension => `${dimension.name}\t${dimension.reference_standard}\t${dimension.scoring_principle}`)
      .join('\n');
    
    const friendlyFullFormat = friendlyHeader + '\n\n' + formattedLines.join('\n\n─────────────────────────────────────────\n\n');
    
    // 将完整的template数据存储到form中，供人工评估时使用
    setTimeout(() => {
      form.setFieldsValue({
        evaluationTemplate: JSON.stringify(template),
        evaluationCriteriaFriendly: friendlyFullFormat
      });
    }, 0);
    
    // 返回tab分隔格式供AI评估使用
    return basicTabFormat;
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
  // 注意：这里故意不包含handleAutoClassify依赖，因为它会导致循环依赖
  // handleAutoClassify在每次render时都会重新创建，会导致debounce失效
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoClassifyEnabled]);

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

  // 解析评估标准获取各维度最大分数
  const parseEvaluationCriteria = (criteriaText) => {
    if (!criteriaText) return {};
    
    // 首先尝试解析JSON格式（新的标准配置格式）
    try {
      const parsed = JSON.parse(criteriaText);
      if (parsed.dimensions && Array.isArray(parsed.dimensions)) {
        const criteriaMap = {};
        parsed.dimensions.forEach(dimension => {
          if (dimension.name && dimension.max_score) {
            criteriaMap[dimension.name] = dimension.max_score;
          }
        });
        return criteriaMap;
      }
    } catch (e) {
      // 如果不是JSON格式，继续用原来的tab分割方式解析
    }
    
    // 原有的tab分割格式解析
    const lines = criteriaText.split('\n').filter(line => line.trim());
    const criteriaMap = {};
    
    lines.forEach(line => {
      const parts = line.split('\t');
      if (parts.length >= 3) {
        const dimensionName = parts[0].trim();
        const scoringRule = parts[2].trim();
        
        // 提取最大分数，查找类似 "0-4分" 的模式
        const scoreMatch = scoringRule.match(/(\d+)-(\d+)分|(\d+)分/);
        if (scoreMatch) {
          const maxScore = parseInt(scoreMatch[2] || scoreMatch[3] || scoreMatch[1]);
          criteriaMap[dimensionName] = maxScore;
        }
      }
    });
    
    return criteriaMap;
  };

  // 获取维度显示名称
  const getDimensionDisplayName = (dimensionKey, criteriaText) => {
    // 首先尝试从评估标准中解析维度名称
    const lines = criteriaText.split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      const parts = line.split('\t');
      if (parts.length >= 1) {
        const dimensionName = parts[0].trim();
        // 检查是否匹配当前维度key（支持多种匹配方式）
        if (dimensionName.toLowerCase() === dimensionKey.toLowerCase() ||
            dimensionKey.toLowerCase().includes(dimensionName.toLowerCase()) ||
            dimensionName.toLowerCase().includes(dimensionKey.toLowerCase())) {
          return dimensionName;
        }
      }
    }
    
    // 回退到旧的硬编码映射
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
    
    return dimensionNames[dimensionKey] || dimensionKey.charAt(0).toUpperCase() + dimensionKey.slice(1);
  };

  // 获取维度对应的最大分数
  const getDimensionMaxScore = (dimensionKey, criteriaText) => {
    const criteriaMap = parseEvaluationCriteria(criteriaText || '');
    
    // 扩展的默认映射，支持更多维度
    const defaultMapping = {
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
    
    const chineseName = defaultMapping[dimensionKey];
    
    // 先尝试用中文名称查找
    if (chineseName && criteriaMap[chineseName]) {
      return criteriaMap[chineseName];
    }
    
    // 再尝试用英文名称查找（首字母大写）
    const capitalizedKey = dimensionKey.charAt(0).toUpperCase() + dimensionKey.slice(1);
    if (criteriaMap[capitalizedKey]) {
      return criteriaMap[capitalizedKey];
    }
    
    // 尝试用英文名称查找（原始格式）
    if (criteriaMap[dimensionKey]) {
      return criteriaMap[dimensionKey];
    }
    
    // 尝试遍历所有标准，找到可能匹配的维度
    for (const [stdName, maxScore] of Object.entries(criteriaMap)) {
      // 模糊匹配：检查是否包含类似的关键词
      const lowerStdName = stdName.toLowerCase();
      const lowerDimensionKey = dimensionKey.toLowerCase();
      
      if (lowerStdName.includes(lowerDimensionKey) || lowerDimensionKey.includes(lowerStdName)) {
        return maxScore;
      }
    }
    
    // 扩展的默认值，支持更多维度类型
    const defaultScores = {
      accuracy: 4,
      completeness: 3,
      fluency: 2,
      safety: 1,
      relevance: 3,
      clarity: 2,
      timeliness: 3,
      usability: 3,
      compliance: 2
    };
    
    // 如果还是找不到，使用默认值或者10分
    return defaultScores[dimensionKey] || 5; // 改为5分作为未知维度的默认值
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
                        <Tag size="small" color="green" icon={<ScanOutlined />}>支持图片识别</Tag>
                      </Space>
                    }
                    rules={[{ required: true, message: '请输入模型回答' }]}
                  >
                    <div>
                      {/* 图片上传区域 */}
                      <div style={{ marginBottom: 12 }}>
                        <Space>
                          <Upload
                            accept=".png,.jpg,.jpeg,.gif,.bmp"
                            beforeUpload={handleImageUpload}
                            showUploadList={false}
                            disabled={ocrLoading}
                          >
                            <Button
                              icon={<PictureOutlined />}
                              style={{
                                borderRadius: '6px',
                                border: '1px dashed #d9d9d9',
                                background: '#fafafa'
                              }}
                              disabled={ocrLoading}
                            >
                              点击或拖拽上传图片
                            </Button>
                          </Upload>
                          
                          <Button
                            size="small"
                            type="link"
                            onClick={async () => {
                              message.loading('检测网络状态...', 1);
                              try {
                                const results = await testNetworkConnectivity();
                                const accessibleCount = results.filter(r => r.status === 'accessible').length;
                                const totalCount = results.length;
                                
                                if (accessibleCount === totalCount) {
                                  message.success('✅ 网络连接良好，OCR功能正常');
                                } else if (accessibleCount > 0) {
                                  message.warning(`⚠️ 部分网络资源可访问 (${accessibleCount}/${totalCount})，可能影响OCR性能`);
                                } else {
                                  message.error('❌ 网络连接异常，OCR功能可能不可用');
                                }
                                
                                console.log('🌐 网络检测结果:', results);
                              } catch (error) {
                                message.error('网络检测失败');
                                console.error('网络检测错误:', error);
                              }
                            }}
                            disabled={ocrLoading}
                          >
                            🌐 检测网络
                          </Button>
                          
                          <Button
                            size="small"
                            type="link"
                            onClick={async () => {
                              const loadingMessage = message.loading('预加载OCR资源...', 0);
                              try {
                                const success = await preloadOCRResourcesFixed();
                                loadingMessage();
                                
                                if (success) {
                                  message.success('✅ OCR资源预加载成功！现在可以快速识别图片了');
                                } else {
                                  message.error('❌ OCR资源预加载失败，可能是网络问题');
                                }
                              } catch (error) {
                                loadingMessage();
                                message.error(`预加载失败: ${error.message}`);
                                console.error('预加载错误:', error);
                              }
                            }}
                            disabled={ocrLoading}
                          >
                            📦 预加载
                          </Button>
                          
                          <Button
                            size="small"
                            type="link"
                            onClick={async () => {
                              const loadingMessage = message.loading('测试OCR功能...', 0);
                              try {
                                const result = await testOCRFunction();
                                loadingMessage();
                                
                                if (result.success) {
                                  message.success(`✅ OCR测试成功！识别时间: ${result.details.duration}ms`);
                                  console.log('OCR测试详情:', result.details);
                                } else {
                                  message.error(`❌ OCR测试失败: ${result.message}`);
                                }
                              } catch (error) {
                                loadingMessage();
                                message.error(`测试失败: ${error.message}`);
                                console.error('测试错误:', error);
                              }
                            }}
                            disabled={ocrLoading}
                          >
                            🧪 测试
                          </Button>
                          
                          <Button
                            size="small"
                            type="link"
                            onClick={async () => {
                              const testText = '这是一个测试文本，用于验证表单填入功能是否正常工作。';
                              console.log('🔧 开始测试填入功能...');
                              
                              const success = await fillModelResponseText(testText);
                              
                              if (success) {
                                message.success('✅ 填入测试成功！');
                              } else {
                                message.error('❌ 填入测试失败！');
                              }
                            }}
                            disabled={ocrLoading}
                          >
                            🔧 测试填入
                          </Button>
                        </Space>
                        
                        <div style={{ marginTop: 4, color: '#666', fontSize: '12px' }}>
                          支持PNG/JPG格式，大小不超过5MB • 如果OCR卡住，请先检测网络状态
                        </div>
                      </div>

                      {/* 图片预览区域 */}
                      {imagePreview && (
                        <div style={{ 
                          marginBottom: 12, 
                          padding: '12px',
                          border: '1px solid #d9d9d9',
                          borderRadius: '6px',
                          background: '#fafafa'
                        }}>
                          <div style={{ marginBottom: 8 }}>
                            <Space>
                              <Tag color="blue">图片预览</Tag>
                              <Button 
                                size="small" 
                                type="text" 
                                danger
                                icon={<DeleteOutlined />}
                                onClick={clearImage}
                                disabled={ocrLoading}
                              >
                                清空
                              </Button>
                            </Space>
                          </div>
                          <Image
                            src={imagePreview}
                            alt="OCR识别图片"
                            style={{ 
                              maxWidth: '100%', 
                              maxHeight: '200px',
                              borderRadius: '4px'
                            }}
                            fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHANwDrkl1AuO+pmgAAADhlWElmTU0AKgAAAAgAAYdpAAQAAAABAAAAGgAAAAAAAqACAAQAAAABAAAAwqADAAQAAAABAAAAwwAAAAD9b/HnAAAHlklEQVR4Ae3dP3Ik1RnG8W+2V1JhQQzYEDHBOGGLkNHGBOOUEUKMLhD1YQhJW1YMcAV2gZLwBdgGBM4Y7QqKiQ3YCUNzFUtzuVJhw="
                          />
                        </div>
                      )}

                      {/* OCR识别进度 */}
                      {ocrLoading && (
                        <div style={{ 
                          marginBottom: 12,
                          padding: '12px',
                          background: '#e6f7ff',
                          border: '1px solid #91d5ff',
                          borderRadius: '6px'
                        }}>
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <Space>
                              <Spin size="small" />
                              <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                                {getOCRProgressText(ocrProgress)}
                              </span>
                              <Button 
                                size="small" 
                                type="text" 
                                danger
                                onClick={() => {
                                  setOcrLoading(false);
                                  setOcrProgress(0);
                                  message.info('已取消OCR识别');
                                }}
                              >
                                取消
                              </Button>
                            </Space>
                            <Progress 
                              percent={ocrProgress} 
                              size="small"
                              strokeColor={{
                                '0%': '#108ee9',
                                '100%': '#87d068',
                              }}
                            />
                            {ocrProgress < 10 && (
                              <div style={{ fontSize: '12px', color: '#666' }}>
                                💡 首次使用需要下载语言包，请稍等片刻...
                              </div>
                            )}
                          </Space>
                        </div>
                      )}

                      {/* 文本输入框 - 添加强制刷新支持 */}
                      <TextArea 
                        key={`modelResponse-${forceRenderKey}`}
                        rows={5} 
                        placeholder="请输入待评估的模型回答内容，或粘贴图片进行OCR识别..." 
                        value={modelResponseValue || form.getFieldValue('modelResponse') || ''}
                        onChange={(e) => {
                          const newValue = e.target.value;
                          setModelResponseValue(newValue);
                          form.setFieldsValue({ modelResponse: newValue });
                        }}
                        onPaste={handleTextAreaPaste}
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
                      
                      {/* 当前会话图片历史展示 */}
                      {uploadedImages.length > 0 && (
                        <div style={{ marginTop: '12px' }}>
                          <div style={{ 
                            padding: '12px',
                            border: '1px solid #e6f7ff',
                            borderRadius: '6px',
                            background: 'linear-gradient(135deg, #f6f9fc 0%, #ffffff 100%)'
                          }}>
                            <Text strong style={{ color: '#1890ff', marginBottom: '8px', display: 'block' }}>
                              📷 本次评估已上传图片 ({uploadedImages.length}张)
                            </Text>
                            {renderImageHistory(uploadedImages)}
                            <div style={{ marginTop: '8px', textAlign: 'right' }}>
                              <Button 
                                size="small" 
                                type="text" 
                                danger
                                onClick={() => {
                                  // 清理所有已上传的图片
                                  uploadedImages.forEach(img => {
                                    if (img.previewUrl) {
                                      URL.revokeObjectURL(img.previewUrl);
                                    }
                                  });
                                  setUploadedImages([]);
                                  message.info('已清空所有上传图片');
                                }}
                              >
                                清空所有图片
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
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

      {/* 人工评估模态框 */}
      {renderHumanEvaluationModal()}
    </div>
  );
};

export default EvaluationForm; 