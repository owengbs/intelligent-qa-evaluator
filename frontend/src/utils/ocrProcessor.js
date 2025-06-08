import Tesseract from 'tesseract.js';

/**
 * OCR图片文字识别处理工具
 * 使用Tesseract.js进行光学字符识别
 */

/**
 * 识别图片中的文字
 * @param {File|Blob|string} image - 图片文件、Blob对象或Base64字符串
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeText = async (image, options = {}) => {
  let worker = null;
  
  try {
    const {
      languages = 'chi_sim+eng', // 支持简体中文和英文
      oem = 1, // OCR Engine Mode
      psm = 3, // Page Segmentation Mode
      onProgress = null
    } = options;

    console.log('🔍 开始OCR识别...');
    console.log('📝 语言设置:', languages);
    console.log('📊 图片类型:', typeof image, image instanceof File ? image.type : 'unknown');

    // 更新进度回调
    const updateProgress = (status, progress = 0) => {
      console.log(`📈 OCR状态: ${status}, 进度: ${progress}%`);
      if (onProgress) {
        onProgress(Math.round(progress));
      }
    };

    updateProgress('初始化OCR引擎', 5);

    // 创建Tesseract Worker，使用更稳定的配置
    worker = await Tesseract.createWorker({
      corePath: 'https://unpkg.com/tesseract.js-core@4.0.4/tesseract-core.wasm.js',
      workerPath: 'https://unpkg.com/tesseract.js@4.1.4/dist/worker.min.js',
      logger: (m) => {
        console.log('🤖 Tesseract日志:', m);
        
        if (m.status === 'loading tesseract core') {
          updateProgress('加载OCR核心模块', m.progress * 20);
        } else if (m.status === 'initializing tesseract') {
          updateProgress('初始化Tesseract', 20 + m.progress * 10);
        } else if (m.status === 'loading language traineddata') {
          updateProgress('加载语言模型', 30 + m.progress * 30);
        } else if (m.status === 'initializing api') {
          updateProgress('初始化API', 60 + m.progress * 10);
        } else if (m.status === 'recognizing text') {
          updateProgress('识别文字内容', 70 + m.progress * 30);
        }
      }
    });

    console.log('✅ Worker创建成功');
    updateProgress('加载语言包', 25);

    // 加载语言包，添加超时处理
    const loadLanguagePromise = worker.loadLanguage(languages);
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('语言包加载超时')), 60000); // 60秒超时
    });
    
    await Promise.race([loadLanguagePromise, timeoutPromise]);
    console.log('✅ 语言包加载成功');
    updateProgress('初始化语言模型', 50);
    
    // 初始化语言
    await worker.initialize(languages);
    console.log('✅ 语言初始化成功');
    updateProgress('配置参数', 65);
    
    // 设置参数
    await worker.setParameters({
      tessedit_ocr_engine_mode: oem,
      tessedit_pageseg_mode: psm,
    });

    console.log('✅ 参数配置完成，开始识别');
    updateProgress('开始文字识别', 70);

    // 执行OCR识别
    const { data: { text } } = await worker.recognize(image);
    
    console.log('✅ OCR识别完成');
    updateProgress('处理识别结果', 95);

    // 清理和格式化识别结果
    const cleanedText = cleanText(text);
    console.log('📄 识别结果:', cleanedText);
    
    updateProgress('完成', 100);
    return cleanedText;
    
  } catch (error) {
    console.error('❌ OCR识别失败:', error);
    
    // 提供更具体的错误信息
    let errorMessage = 'OCR识别失败';
    if (error.message.includes('timeout') || error.message.includes('超时')) {
      errorMessage = '网络超时，请检查网络连接或稍后重试';
    } else if (error.message.includes('Failed to fetch') || error.message.includes('网络')) {
      errorMessage = '网络连接失败，无法下载OCR语言包';
    } else if (error.message.includes('DataCloneError')) {
      errorMessage = '数据传输错误，请重新上传图片';
    } else {
      errorMessage = `OCR识别失败: ${error.message}`;
    }
    
    throw new Error(errorMessage);
  } finally {
    // 确保Worker被正确清理
    if (worker) {
      try {
        await worker.terminate();
        console.log('✅ Worker已清理');
      } catch (cleanupError) {
        console.warn('⚠️ Worker清理失败:', cleanupError);
      }
    }
  }
};

/**
 * 清理和格式化识别出的文字
 * @param {string} text - 原始识别文字
 * @returns {string} 清理后的文字
 */
const cleanText = (text) => {
  if (!text) return '';
  
  return text
    // 移除多余的空白字符
    .replace(/\s+/g, ' ')
    // 移除行首行尾空白
    .replace(/^\s+|\s+$/gm, '')
    // 移除空行
    .replace(/\n\s*\n/g, '\n')
    // 修复常见的OCR错误（可根据需要扩展）
    .replace(/[""]/g, '"')
    .replace(/['']/g, "'")
    // 移除首尾空白
    .trim();
};

/**
 * 从剪贴板粘贴事件中提取图片
 * @param {ClipboardEvent} event - 粘贴事件
 * @returns {File|null} 图片文件或null
 */
export const extractImageFromPaste = (event) => {
  const items = event.clipboardData?.items;
  if (!items) return null;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.type.indexOf('image') !== -1) {
      return item.getAsFile();
    }
  }
  return null;
};

/**
 * 验证文件是否为支持的图片格式
 * @param {File} file - 文件对象
 * @returns {boolean} 是否为支持的图片格式
 */
export const isValidImageFile = (file) => {
  if (!file) return false;
  
  const supportedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp'];
  return supportedTypes.includes(file.type.toLowerCase());
};

/**
 * 检查文件大小是否在限制范围内
 * @param {File} file - 文件对象
 * @param {number} maxSizeMB - 最大文件大小（MB）
 * @returns {boolean} 文件大小是否合法
 */
export const isValidFileSize = (file, maxSizeMB = 5) => {
  if (!file) return false;
  
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};

/**
 * 创建图片预览URL
 * @param {File} file - 图片文件
 * @returns {string} 预览URL
 */
export const createImagePreviewUrl = (file) => {
  return URL.createObjectURL(file);
};

/**
 * 释放图片预览URL
 * @param {string} url - 预览URL
 */
export const revokeImagePreviewUrl = (url) => {
  if (url) {
    URL.revokeObjectURL(url);
  }
};

/**
 * 简化版OCR识别（降级方案）
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextSimple = async (image, options = {}) => {
  let worker = null;
  
  try {
    const { onProgress = null } = options;
    
    console.log('🔍 使用简化版OCR识别...');
    
    // 更新进度
    const updateProgress = (progress) => {
      if (onProgress) onProgress(progress);
    };

    updateProgress(10);
    
    // 使用默认配置创建Worker
    worker = await Tesseract.createWorker({
      logger: (m) => {
        console.log('Tesseract:', m.status, m.progress);
        if (m.progress) {
          updateProgress(Math.round(m.progress * 100));
        }
      }
    });

    updateProgress(20);
    
    // 只使用英文语言包（更快）
    await worker.loadLanguage('eng');
    updateProgress(50);
    
    await worker.initialize('eng');
    updateProgress(70);

    // 执行识别
    const { data: { text } } = await worker.recognize(image);
    updateProgress(100);
    
    return cleanText(text);
    
  } catch (error) {
    console.error('简化版OCR也失败:', error);
    throw new Error('OCR识别服务暂时不可用，请稍后重试');
  } finally {
    if (worker) {
      try {
        await worker.terminate();
      } catch (e) {
        console.warn('Worker清理失败:', e);
      }
    }
  }
};

/**
 * 获取OCR识别进度的用户友好提示
 * @param {number} progress - 进度百分比
 * @returns {string} 进度提示文字
 */
export const getOCRProgressText = (progress) => {
  if (progress < 10) return '正在初始化OCR引擎...';
  if (progress < 25) return '正在加载OCR核心模块...';
  if (progress < 50) return '正在加载语言模型...';
  if (progress < 65) return '正在初始化API...';
  if (progress < 80) return '正在识别文字内容...';
  if (progress < 95) return '正在优化识别结果...';
  return '即将完成识别...';
};

const ocrUtils = {
  recognizeText,
  recognizeTextSimple,
  extractImageFromPaste,
  isValidImageFile,
  isValidFileSize,
  createImagePreviewUrl,
  revokeImagePreviewUrl,
  getOCRProgressText
};

export default ocrUtils; 