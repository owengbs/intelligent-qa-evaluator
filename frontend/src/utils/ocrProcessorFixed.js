import Tesseract from 'tesseract.js';

/**
 * 修复版OCR处理器 - 解决参数警告和文本填入问题
 */

/**
 * 简单可靠的OCR识别（修复版本）
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextFixed = async (image, options = {}) => {
  const { onProgress = null, timeout = 120000 } = options;
  
  try {
    console.log('🔍 使用修复版OCR识别...');
    
    if (onProgress) onProgress(5);
    
    // 创建超时Promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('OCR处理超时')), timeout);
    });
    
    // 进度更新函数
    const updateProgress = (step, progress) => {
      console.log(`📈 OCR步骤: ${step}, 进度: ${progress}%`);
      if (onProgress) onProgress(progress);
    };
    
    updateProgress('开始处理', 10);
    
    // 首先尝试中英文识别，使用最简单的配置
    let ocrResult = null;
    
    try {
      updateProgress('加载中英文语言包', 20);
      
      // 使用最简单的配置，避免参数警告
      const ocrPromise = Tesseract.recognize(image, 'chi_sim+eng', {
        // 只使用最基础的、确保兼容的参数
        tessedit_pageseg_mode: Tesseract.PSM.AUTO
      });
      
      updateProgress('执行中英文识别', 60);
      ocrResult = await Promise.race([ocrPromise, timeoutPromise]);
      
      console.log('✅ 中英文识别成功');
      
    } catch (chineseError) {
      console.warn('⚠️ 中英文识别失败，尝试英文模式:', chineseError.message);
      
      try {
        updateProgress('使用英文模式', 40);
        
        const englishPromise = Tesseract.recognize(image, 'eng', {
          tessedit_pageseg_mode: Tesseract.PSM.AUTO
        });
        
        updateProgress('执行英文识别', 70);
        ocrResult = await Promise.race([englishPromise, timeoutPromise]);
        
        console.log('✅ 英文识别成功');
        
      } catch (englishError) {
        console.error('❌ 英文识别也失败:', englishError.message);
        throw new Error(`所有OCR模式都失败: ${englishError.message}`);
      }
    }
    
    updateProgress('处理识别结果', 90);
    
    if (!ocrResult || !ocrResult.data) {
      throw new Error('OCR返回结果为空');
    }
    
    const { text, confidence } = ocrResult.data;
    
    // 清理和格式化文本
    const cleanedText = cleanAndFormatText(text);
    
    updateProgress('完成', 100);
    
    console.log('✅ OCR识别完成:', {
      originalText: text,
      cleanedText: cleanedText,
      confidence: confidence,
      length: cleanedText.length
    });
    
    return cleanedText;
    
  } catch (error) {
    console.error('❌ OCR识别失败:', error);
    
    let errorMessage = 'OCR识别失败';
    if (error.message.includes('timeout') || error.message.includes('超时')) {
      errorMessage = 'OCR处理超时，请尝试使用更小的图片';
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = '网络连接问题，无法下载语言包。建议：1) 检查网络连接 2) 尝试手机热点 3) 点击"预加载"按钮';
    } else {
      errorMessage = `OCR识别失败: ${error.message}`;
    }
    
    throw new Error(errorMessage);
  }
};

/**
 * 预加载OCR资源（修复版本）
 * @returns {Promise<boolean>} 是否成功
 */
export const preloadOCRResourcesFixed = async () => {
  try {
    console.log('📦 开始预加载OCR资源（修复版）...');
    
    // 创建测试图片
    const canvas = document.createElement('canvas');
    canvas.width = 100;
    canvas.height = 30;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, 100, 30);
    ctx.fillStyle = 'black';
    ctx.font = '16px Arial';
    ctx.fillText('Test', 10, 20);
    
    const blob = await new Promise(resolve => {
      canvas.toBlob(resolve);
    });
    
    // 先预加载英文
    console.log('📦 预加载英文语言包...');
    await Tesseract.recognize(blob, 'eng', {
      tessedit_pageseg_mode: Tesseract.PSM.AUTO
    });
    
    console.log('✅ 英文语言包预加载成功');
    
    // 再预加载中文（如果可能）
    try {
      console.log('📦 预加载中文语言包...');
      
      // 创建包含中文的测试图片
      const chineseCanvas = document.createElement('canvas');
      chineseCanvas.width = 100;
      chineseCanvas.height = 30;
      const chineseCtx = chineseCanvas.getContext('2d');
      
      chineseCtx.fillStyle = 'white';
      chineseCtx.fillRect(0, 0, 100, 30);
      chineseCtx.fillStyle = 'black';
      chineseCtx.font = '16px SimHei';
      chineseCtx.fillText('测试', 10, 20);
      
      const chineseBlob = await new Promise(resolve => {
        chineseCanvas.toBlob(resolve);
      });
      
      await Tesseract.recognize(chineseBlob, 'chi_sim+eng', {
        tessedit_pageseg_mode: Tesseract.PSM.AUTO
      });
      
      console.log('✅ 中文语言包预加载成功');
      
    } catch (chineseError) {
      console.warn('⚠️ 中文语言包预加载失败，但英文可用:', chineseError.message);
    }
    
    console.log('✅ OCR资源预加载完成');
    return true;
    
  } catch (error) {
    console.error('❌ OCR资源预加载失败:', error);
    return false;
  }
};

/**
 * 改进的文本清理和格式化
 */
const cleanAndFormatText = (text) => {
  if (!text) return '';
  
  return text
    // 移除OCR常见的错误字符
    .replace(/[|\[\]]/g, '') // 移除常见的误识别字符
    .replace(/[""]/g, '"') // 统一引号
    .replace(/['']/g, "'") // 统一单引号
    
    // 处理空格问题
    .replace(/\s+/g, ' ') // 多个空格合并为单个
    .replace(/^\s+|\s+$/gm, '') // 去除行首行尾空格
    
    // 处理中英文混合的空格
    .replace(/([\u4e00-\u9fff])\s+([\u4e00-\u9fff])/g, '$1$2') // 中文字符间去除空格
    .replace(/([\u4e00-\u9fff])\s+([a-zA-Z0-9])/g, '$1 $2') // 中文和英文间保持空格
    .replace(/([a-zA-Z0-9])\s+([\u4e00-\u9fff])/g, '$1 $2') // 英文和中文间保持空格
    
    // 处理标点符号
    .replace(/\s*([,.!?;:，。！？；：])\s*/g, '$1 ') // 标点符号后加空格
    .replace(/\s+([.!?，。！？])/g, '$1') // 移除标点符号前的空格
    
    // 最终清理
    .replace(/\n\s*\n/g, '\n') // 合并多个换行
    .trim(); // 去除首尾空格
};

/**
 * 测试OCR功能
 * @returns {Promise<Object>} 测试结果
 */
export const testOCRFunction = async () => {
  const result = {
    success: false,
    message: '',
    details: {}
  };
  
  try {
    console.log('🧪 开始OCR功能测试...');
    
    // 创建测试图片
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 60;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, 200, 60);
    ctx.fillStyle = 'black';
    ctx.font = '18px Arial';
    ctx.fillText('Hello World 测试', 10, 30);
    ctx.fillText('OCR Test 123', 10, 50);
    
    const blob = await new Promise(resolve => {
      canvas.toBlob(resolve);
    });
    
    const startTime = Date.now();
    const recognizedText = await recognizeTextFixed(blob, {
      onProgress: (progress) => {
        console.log(`🧪 测试进度: ${progress}%`);
      }
    });
    const endTime = Date.now();
    
    const duration = endTime - startTime;
    
    result.success = true;
    result.message = 'OCR功能测试成功';
    result.details = {
      recognizedText,
      duration,
      textLength: recognizedText.length,
      hasContent: recognizedText.length > 0
    };
    
    console.log('✅ OCR功能测试成功:', result.details);
    
  } catch (error) {
    result.success = false;
    result.message = `OCR功能测试失败: ${error.message}`;
    result.details.error = error;
    
    console.error('❌ OCR功能测试失败:', error);
  }
  
  return result;
};

export default {
  recognizeTextFixed,
  preloadOCRResourcesFixed,
  testOCRFunction
}; 