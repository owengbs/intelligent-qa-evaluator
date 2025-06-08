import Tesseract from 'tesseract.js';

/**
 * 超简单OCR处理器 - 避免所有复杂配置和序列化问题
 */

/**
 * 最简单的OCR识别（支持中英文）
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextUltraSimple = async (image, options = {}) => {
  const { onProgress = null } = options;
  
  try {
    console.log('🔍 使用超简单OCR模式（中英文）...');
    
    if (onProgress) onProgress(10);
    
    // 支持中英文识别，使用简化配置
    const { data: { text } } = await Tesseract.recognize(image, 'chi_sim+eng', {
      tessedit_pageseg_mode: Tesseract.PSM.AUTO,
      tessedit_ocr_engine_mode: Tesseract.OEM.LSTM_ONLY,
      preserve_interword_spaces: '1',
    });
    
    if (onProgress) onProgress(100);
    
    // 改进的文本清理
    const cleanedText = cleanText(text);
    
    console.log('📄 识别结果:', cleanedText);
    return cleanedText;
    
  } catch (error) {
    console.error('❌ 超简单OCR失败，尝试仅英文模式:', error);
    
    // 如果中文模式失败，降级到英文
    try {
      const { data: { text } } = await Tesseract.recognize(image, 'eng');
      const cleanedText = cleanText(text);
      console.log('📄 英文模式识别结果:', cleanedText);
      return cleanedText;
    } catch (fallbackError) {
      throw new Error(`OCR识别失败: ${fallbackError.message}`);
    }
  }
};

/**
 * 高精度中英文OCR识别
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextWithProgress = async (image, options = {}) => {
  const { onProgress = null, timeout = 120000 } = options; // 增加到2分钟超时
  
  try {
    console.log('🔍 使用高精度中英文OCR识别...');
    
    if (onProgress) onProgress(5);
    
    // 创建超时Promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('OCR处理超时')), timeout);
    });
    
    // 简单的进度更新
    const progressUpdater = (step, progress) => {
      console.log(`📈 OCR步骤: ${step}, 进度: ${progress}%`);
      if (onProgress) onProgress(progress);
    };
    
    progressUpdater('开始处理', 10);
    
    // 优先尝试中英文混合识别，使用高精度配置
    let ocrPromise;
    try {
      progressUpdater('加载中英文语言包', 20);
      
      ocrPromise = Tesseract.recognize(image, 'chi_sim+eng', {
        // 只使用支持的基础配置
        tessedit_pageseg_mode: Tesseract.PSM.AUTO,
        tessedit_ocr_engine_mode: Tesseract.OEM.LSTM_ONLY,
        preserve_interword_spaces: '1',
      });
      
      progressUpdater('执行中英文识别', 60);
      
    } catch (setupError) {
      console.warn('⚠️ 中英文模式初始化失败，使用英文模式:', setupError);
      progressUpdater('使用英文模式', 40);
      
      ocrPromise = Tesseract.recognize(image, 'eng', {
        tessedit_pageseg_mode: Tesseract.PSM.AUTO,
        tessedit_ocr_engine_mode: Tesseract.OEM.LSTM_ONLY,
      });
    }
    
    const { data: { text, confidence } } = await Promise.race([ocrPromise, timeoutPromise]);
    
    progressUpdater('处理识别结果', 90);
    
    // 改进的文本清理和格式化
    const cleanedText = cleanAndFormatText(text);
    
    progressUpdater('完成', 100);
    
    console.log('✅ OCR识别成功:', {
      text: cleanedText,
      confidence: confidence,
      length: cleanedText.length
    });
    
    return cleanedText;
    
  } catch (error) {
    console.error('❌ 高精度OCR失败，尝试英文模式:', error);
    
    // 降级处理
    try {
      if (onProgress) onProgress(50);
      
      const { data: { text } } = await Tesseract.recognize(image, 'eng', {
        tessedit_pageseg_mode: Tesseract.PSM.AUTO
      });
      
      const cleanedText = cleanAndFormatText(text);
      
      if (onProgress) onProgress(100);
      
      console.log('✅ 英文模式识别成功:', cleanedText);
      return cleanedText;
      
    } catch (fallbackError) {
      console.error('❌ 所有OCR模式都失败:', fallbackError);
      
      if (error.message.includes('timeout') || error.message.includes('超时')) {
        throw new Error('OCR处理超时，请尝试压缩图片后重新上传');
      } else if (error.message.includes('Failed to fetch')) {
        throw new Error('网络连接问题，无法下载语言包。建议：1) 检查网络连接 2) 尝试手机热点 3) 点击"预加载"按钮');
      } else {
        throw new Error(`OCR识别失败: ${error.message}。建议先点击"预加载"按钮下载语言包`);
      }
    }
  }
};

/**
 * 预加载OCR资源
 * @returns {Promise<boolean>} 是否成功
 */
export const preloadOCRResources = async () => {
  try {
    console.log('📦 开始预加载OCR资源...');
    
    // 创建一个最小的测试图片
    const canvas = document.createElement('canvas');
    canvas.width = 50;
    canvas.height = 20;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, 50, 20);
    ctx.fillStyle = 'black';
    ctx.font = '12px Arial';
    ctx.fillText('test', 5, 15);
    
    // 转换为Blob
    const blob = await new Promise(resolve => {
      canvas.toBlob(resolve);
    });
    
    // 执行一次快速识别来触发资源下载
    await Tesseract.recognize(blob, 'eng');
    
    console.log('✅ OCR资源预加载成功');
    return true;
    
  } catch (error) {
    console.error('❌ OCR资源预加载失败:', error);
    return false;
  }
};

/**
 * 检查OCR资源可用性
 * @returns {Promise<Object>} 检查结果
 */
export const checkOCRAvailability = async () => {
  const result = {
    available: false,
    message: '',
    details: {}
  };
  
  try {
    // 检查基础环境
    result.details.webWorker = typeof Worker !== 'undefined';
    result.details.webAssembly = typeof WebAssembly === 'object';
    result.details.tesseractLibrary = typeof Tesseract !== 'undefined';
    
    if (!result.details.webWorker) {
      result.message = '浏览器不支持WebWorker';
      return result;
    }
    
    if (!result.details.webAssembly) {
      result.message = '浏览器不支持WebAssembly';
      return result;
    }
    
    if (!result.details.tesseractLibrary) {
      result.message = 'Tesseract库未加载';
      return result;
    }
    
    // 尝试快速预加载测试
    const preloadSuccess = await preloadOCRResources();
    result.details.preloadSuccess = preloadSuccess;
    
    if (preloadSuccess) {
      result.available = true;
      result.message = 'OCR功能可用';
    } else {
      result.message = '网络连接问题，OCR资源无法加载';
    }
    
  } catch (error) {
    result.message = `OCR检查失败: ${error.message}`;
    result.details.error = error;
  }
  
  return result;
};

/**
 * 清理识别的文本
 */
const cleanText = (text) => {
  if (!text) return '';
  
  return text
    .replace(/\s+/g, ' ') // 多个空格替换为单个空格
    .replace(/^\s+|\s+$/gm, '') // 去除行首行尾空格
    .replace(/\n\s*\n/g, '\n') // 多个换行替换为单个换行
    .trim(); // 去除首尾空格
};

/**
 * 改进的文本清理和格式化（适用于中英文混合内容）
 */
const cleanAndFormatText = (text) => {
  if (!text) return '';
  
  return text
    // 移除OCR常见的错误字符
    .replace(/[|\[\]]/g, '') // 移除常见的误识别字符
    .replace(/[""]/g, '"') // 统一引号
    .replace(/['']/g, "'") // 统一单引号
    
    // 处理中英文混合的空格问题
    .replace(/([a-zA-Z0-9])\s+([a-zA-Z0-9])/g, '$1 $2') // 英文单词间保持单个空格
    .replace(/([中文字符范围])\s+([中文字符范围])/g, '$1$2') // 中文字符间去除空格
    .replace(/([\u4e00-\u9fff])\s+([a-zA-Z0-9])/g, '$1 $2') // 中文和英文间保持空格
    .replace(/([a-zA-Z0-9])\s+([\u4e00-\u9fff])/g, '$1 $2') // 英文和中文间保持空格
    
    // 处理标点符号
    .replace(/\s*([,.!?;:，。！？；：])\s*/g, '$1 ') // 标点符号后加空格
    .replace(/\s+([.!?，。！？])/g, '$1') // 移除标点符号前的空格
    
    // 处理换行和段落
    .replace(/\n\s*\n\s*\n/g, '\n\n') // 多个换行合并为两个
    .replace(/^\s+|\s+$/gm, '') // 去除每行首尾空格
    .replace(/\s+/g, ' ') // 合并多余空格
    
    // 最终清理
    .trim()
    .replace(/\n\s*\n/g, '\n') // 确保段落分隔
    .replace(/\s+$/, ''); // 去除末尾空格
};

export default {
  recognizeTextUltraSimple,
  recognizeTextWithProgress,
  preloadOCRResources,
  checkOCRAvailability
}; 