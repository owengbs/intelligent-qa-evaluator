// OCR功能测试脚本
// 该文件仅用于开发测试，生产环境可删除

import { recognizeText, isValidImageFile, isValidFileSize } from './ocrProcessor';

/**
 * 测试OCR识别功能
 * 可在浏览器控制台中调用此函数进行测试
 */
export const testOCRFunction = async () => {
  console.log('🔍 OCR功能测试开始...');
  
  try {
    // 创建一个简单的测试图片（Base64格式的文本图片）
    const testImageBase64 = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
    
    console.log('📝 正在测试图片识别...');
    
    // 模拟进度回调
    const onProgress = (progress) => {
      console.log(`⏳ 识别进度: ${progress}%`);
    };
    
    // 执行OCR识别
    const result = await recognizeText(testImageBase64, { onProgress });
    
    console.log('✅ OCR识别完成');
    console.log('📄 识别结果:', result);
    
    return result;
  } catch (error) {
    console.error('❌ OCR测试失败:', error);
    throw error;
  }
};

/**
 * 测试文件验证功能
 */
export const testFileValidation = () => {
  console.log('🔧 文件验证功能测试开始...');
  
  // 创建模拟文件对象
  const mockPngFile = {
    type: 'image/png',
    size: 1024 * 1024, // 1MB
    name: 'test.png'
  };
  
  const mockLargeFile = {
    type: 'image/jpeg',
    size: 10 * 1024 * 1024, // 10MB
    name: 'large.jpg'
  };
  
  const mockInvalidFile = {
    type: 'text/plain',
    size: 1024,
    name: 'test.txt'
  };
  
  // 测试有效图片文件
  console.log('✅ PNG文件验证:', isValidImageFile(mockPngFile));
  console.log('✅ PNG文件大小验证:', isValidFileSize(mockPngFile));
  
  // 测试大文件
  console.log('❌ 大文件大小验证:', isValidFileSize(mockLargeFile));
  
  // 测试无效文件类型
  console.log('❌ 无效文件类型验证:', isValidImageFile(mockInvalidFile));
  
  console.log('🔧 文件验证测试完成');
};

/**
 * 模拟粘贴事件测试
 */
export const simulatePasteEvent = () => {
  console.log('📋 模拟粘贴事件测试...');
  
  // 创建模拟的ClipboardEvent
  const mockClipboardEvent = {
    clipboardData: {
      items: [
        {
          type: 'image/png',
          getAsFile: () => ({
            type: 'image/png',
            size: 1024 * 100, // 100KB
            name: 'pasted-image.png'
          })
        }
      ]
    }
  };
  
  // 测试图片提取
  const { extractImageFromPaste } = require('./ocrProcessor');
  const extractedFile = extractImageFromPaste(mockClipboardEvent);
  
  console.log('📋 粘贴事件图片提取结果:', extractedFile);
  
  return extractedFile;
};

/**
 * 在浏览器控制台中运行所有测试
 */
export const runAllTests = async () => {
  console.log('🚀 开始执行所有OCR功能测试...');
  console.log('='.repeat(50));
  
  try {
    // 1. 文件验证测试
    testFileValidation();
    console.log('='.repeat(50));
    
    // 2. 粘贴事件测试
    simulatePasteEvent();
    console.log('='.repeat(50));
    
    // 3. OCR识别测试
    // 注意：在实际使用中，这个测试需要有效的图片数据
    console.log('⚠️  OCR识别测试需要有效的图片数据，请手动测试');
    console.log('💡 使用方法：在评估页面上传包含文字的图片进行测试');
    
    console.log('='.repeat(50));
    console.log('✅ 所有可自动化测试完成');
    
  } catch (error) {
    console.error('❌ 测试过程中出现错误:', error);
  }
};

// 如果在Node.js环境中运行，导出测试函数
if (typeof window === 'undefined') {
  module.exports = {
    testOCRFunction,
    testFileValidation,
    simulatePasteEvent,
    runAllTests
  };
}

// 在浏览器环境中，将测试函数添加到全局对象
if (typeof window !== 'undefined') {
  window.ocrTests = {
    testOCRFunction,
    testFileValidation,
    simulatePasteEvent,
    runAllTests
  };
  
  console.log('🔧 OCR测试功能已加载到 window.ocrTests');
  console.log('💡 在控制台中运行 window.ocrTests.runAllTests() 开始测试');
} 