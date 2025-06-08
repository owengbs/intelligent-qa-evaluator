import Tesseract from 'tesseract.js';

/**
 * 本地化OCR处理器
 * 针对国内网络环境优化，使用更稳定的CDN和配置
 */

/**
 * 使用本地化配置的OCR识别
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextLocal = async (image, options = {}) => {
  let worker = null;
  
  try {
    const { onProgress = null, timeout = 30000 } = options;
    
    console.log('🔍 使用本地化OCR识别...');
    
    // 进度更新函数
    const updateProgress = (status, progress = 0) => {
      console.log(`📈 OCR状态: ${status}, 进度: ${progress}%`);
      if (onProgress) {
        onProgress(Math.round(progress));
      }
    };

    updateProgress('初始化本地OCR引擎', 5);

    // 使用更简单的配置创建Worker（修复DataCloneError）
    worker = await Tesseract.createWorker({
      // 不指定CDN路径，让Tesseract使用默认配置
      cachePath: '.', // 使用当前目录作为缓存
      // 移除logger函数避免序列化问题
      logger: undefined
    });
    
    // 手动监听Worker事件（避免函数序列化问题）
    const originalPostMessage = worker.postMessage;
    if (originalPostMessage) {
      worker.postMessage = function(message) {
        // 监听消息但不传递函数
        return originalPostMessage.call(this, message);
      };
    }

    console.log('✅ Worker创建成功');

    // 创建超时Promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`操作超时 (${timeout/1000}秒)`)), timeout);
    });

    // 只使用英文语言包（更快，更稳定）
    updateProgress('加载英文语言包', 25);
    
    const loadLanguagePromise = worker.loadLanguage('eng');
    await Promise.race([loadLanguagePromise, timeoutPromise]);
    
    console.log('✅ 英文语言包加载成功');
    updateProgress('初始化语言模型', 50);
    
    const initializePromise = worker.initialize('eng');
    await Promise.race([initializePromise, timeoutPromise]);
    
    console.log('✅ 语言初始化成功');
    updateProgress('开始文字识别', 70);

    // 执行OCR识别
    const recognizePromise = worker.recognize(image);
    const { data: { text } } = await Promise.race([recognizePromise, timeoutPromise]);
    
    console.log('✅ OCR识别完成');
    updateProgress('处理识别结果', 95);

    // 清理文本
    const cleanedText = cleanText(text);
    console.log('📄 识别结果:', cleanedText);
    
    updateProgress('完成', 100);
    return cleanedText;
    
  } catch (error) {
    console.error('❌ 本地OCR识别失败:', error);
    
    // 提供具体的错误信息
    let errorMessage = 'OCR识别失败';
    if (error.message.includes('timeout') || error.message.includes('超时')) {
      errorMessage = '网络超时，请检查网络连接';
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = '无法下载OCR资源，请检查网络连接';
    } else {
      errorMessage = `OCR识别失败: ${error.message}`;
    }
    
    throw new Error(errorMessage);
  } finally {
    // 清理Worker
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
 * 极简OCR识别（最后的备选方案）
 * @param {File|Blob|string} image - 图片文件
 * @param {Object} options - 识别选项
 * @returns {Promise<string>} 识别出的文字内容
 */
export const recognizeTextMinimal = async (image, options = {}) => {
  const { onProgress = null } = options;
  
  try {
    console.log('🔍 使用极简OCR模式...');
    
    if (onProgress) onProgress(10);
    
    // 最简单的Tesseract配置
    const { data: { text } } = await Tesseract.recognize(image, 'eng', {
      logger: m => {
        console.log('极简OCR:', m.status);
        if (m.progress && onProgress) {
          onProgress(Math.round(m.progress * 100));
        }
      }
    });
    
    if (onProgress) onProgress(100);
    
    return cleanText(text);
    
  } catch (error) {
    console.error('❌ 极简OCR也失败:', error);
    throw new Error('OCR服务暂时不可用，请稍后重试');
  }
};

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'loading tesseract core': '加载OCR核心模块',
    'initializing tesseract': '初始化Tesseract',
    'loading language traineddata': '下载语言数据包',
    'initializing api': '初始化API',
    'recognizing text': '识别文字内容'
  };
  
  return statusMap[status] || status;
};

/**
 * 清理识别的文本
 */
const cleanText = (text) => {
  if (!text) return '';
  
  return text
    .replace(/\s+/g, ' ')
    .replace(/^\s+|\s+$/gm, '')
    .replace(/\n\s*\n/g, '\n')
    .trim();
};

/**
 * 网络连接测试
 */
export const testNetworkConnectivity = async () => {
  const testUrls = [
    'https://unpkg.com/tesseract.js@4.1.4/package.json',
    'https://cdn.jsdelivr.net/npm/tesseract.js@4.1.4/package.json'
  ];

  const results = [];
  
  for (const url of testUrls) {
    try {
      const response = await fetch(url, { 
        method: 'HEAD', 
        timeout: 5000 
      });
      results.push({ url, status: 'accessible', code: response.status });
    } catch (error) {
      results.push({ url, status: 'failed', error: error.message });
    }
  }
  
  return results;
};

/**
 * 智能OCR识别（带网络检测和降级）
 */
export const smartOCRRecognize = async (image, options = {}) => {
  const { onProgress = null } = options;
  
  try {
    // 先测试网络连接
    console.log('🌐 检测网络连接...');
    if (onProgress) onProgress(5);
    
    const networkStatus = await testNetworkConnectivity();
    const hasGoodNetwork = networkStatus.some(r => r.status === 'accessible');
    
    if (hasGoodNetwork) {
      console.log('✅ 网络连接良好，使用本地化OCR');
      return await recognizeTextLocal(image, options);
    } else {
      console.log('⚠️ 网络连接不佳，使用极简OCR');
      return await recognizeTextMinimal(image, options);
    }
    
  } catch (error) {
    console.error('❌ 智能OCR失败:', error);
    
    // 最后尝试极简模式
    console.log('🔄 尝试极简模式作为最后备选...');
    try {
      return await recognizeTextMinimal(image, { onProgress });
    } catch (fallbackError) {
      throw new Error('所有OCR方法都失败了，请检查网络连接或稍后重试');
    }
  }
};

export default {
  recognizeTextLocal,
  recognizeTextMinimal,
  smartOCRRecognize,
  testNetworkConnectivity
}; 