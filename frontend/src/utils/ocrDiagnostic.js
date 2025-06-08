// OCR诊断工具
// 帮助用户检查OCR功能状态和网络连接

/**
 * 检查Tesseract.js库是否正常加载
 */
export const checkTesseractAvailability = () => {
  try {
    // 检查Tesseract是否存在
    if (typeof window !== 'undefined' && window.Tesseract) {
      console.log('✅ Tesseract.js 库已加载');
      return true;
    } else {
      console.log('❌ Tesseract.js 库未加载');
      return false;
    }
  } catch (error) {
    console.error('❌ 检查Tesseract时出错:', error);
    return false;
  }
};

/**
 * 测试网络连接到CDN
 */
export const checkCDNAccess = async () => {
  const testUrls = [
    'https://unpkg.com/tesseract.js@4.1.4/dist/worker.min.js',
    'https://unpkg.com/tesseract.js-core@4.0.4/tesseract-core.wasm.js',
    'https://tessdata.projectnaptha.com/4.0.0/eng.traineddata.gz'
  ];

  const results = {};
  
  for (const url of testUrls) {
    try {
      const response = await fetch(url, { method: 'HEAD', mode: 'no-cors' });
      results[url] = 'accessible';
      console.log(`✅ 可访问: ${url}`);
    } catch (error) {
      results[url] = 'blocked';
      console.log(`❌ 无法访问: ${url}`);
    }
  }
  
  return results;
};

/**
 * 检查浏览器WebWorker支持
 */
export const checkWebWorkerSupport = () => {
  const supported = typeof Worker !== 'undefined';
  console.log(supported ? '✅ 浏览器支持WebWorker' : '❌ 浏览器不支持WebWorker');
  return supported;
};

/**
 * 检查WebAssembly支持
 */
export const checkWebAssemblySupport = () => {
  const supported = typeof WebAssembly === 'object' && typeof WebAssembly.instantiate === 'function';
  console.log(supported ? '✅ 浏览器支持WebAssembly' : '❌ 浏览器不支持WebAssembly');
  return supported;
};

/**
 * 运行完整的OCR环境诊断
 */
export const runOCRDiagnostic = async () => {
  console.log('🔍 开始OCR环境诊断...');
  console.log('='.repeat(50));
  
  const diagnosticResults = {
    tesseractLoaded: false,
    webWorkerSupport: false,
    webAssemblySupport: false,
    cdnAccess: {},
    recommendations: []
  };

  // 1. 检查基础环境
  console.log('📋 检查基础环境支持...');
  diagnosticResults.webWorkerSupport = checkWebWorkerSupport();
  diagnosticResults.webAssemblySupport = checkWebAssemblySupport();
  diagnosticResults.tesseractLoaded = checkTesseractAvailability();

  // 2. 检查网络连接
  console.log('🌐 检查网络连接...');
  try {
    diagnosticResults.cdnAccess = await checkCDNAccess();
  } catch (error) {
    console.error('网络检查失败:', error);
    diagnosticResults.cdnAccess = { error: error.message };
  }

  // 3. 生成建议
  console.log('💡 生成诊断建议...');
  
  if (!diagnosticResults.webWorkerSupport) {
    diagnosticResults.recommendations.push('浏览器不支持WebWorker，请使用现代浏览器');
  }
  
  if (!diagnosticResults.webAssemblySupport) {
    diagnosticResults.recommendations.push('浏览器不支持WebAssembly，请更新浏览器版本');
  }
  
  if (!diagnosticResults.tesseractLoaded) {
    diagnosticResults.recommendations.push('Tesseract.js库未正确加载，请检查网络连接');
  }

  const blockedUrls = Object.entries(diagnosticResults.cdnAccess)
    .filter(([_, status]) => status === 'blocked')
    .length;
    
  if (blockedUrls > 0) {
    diagnosticResults.recommendations.push('部分CDN资源无法访问，可能影响OCR功能，请检查网络设置');
  }

  // 4. 输出诊断结果
  console.log('='.repeat(50));
  console.log('📊 诊断结果总结:');
  console.log(`WebWorker支持: ${diagnosticResults.webWorkerSupport ? '✅' : '❌'}`);
  console.log(`WebAssembly支持: ${diagnosticResults.webAssemblySupport ? '✅' : '❌'}`);
  console.log(`Tesseract库状态: ${diagnosticResults.tesseractLoaded ? '✅' : '❌'}`);
  console.log(`CDN访问状态: ${blockedUrls === 0 ? '✅' : `❌ (${blockedUrls}个资源不可访问)`}`);
  
  if (diagnosticResults.recommendations.length > 0) {
    console.log('💡 建议:');
    diagnosticResults.recommendations.forEach((rec, index) => {
      console.log(`   ${index + 1}. ${rec}`);
    });
  } else {
    console.log('✅ 环境检查通过，OCR功能应该可以正常工作');
  }

  console.log('='.repeat(50));
  
  return diagnosticResults;
};

/**
 * 快速OCR测试
 */
export const quickOCRTest = async () => {
  try {
    console.log('🚀 执行快速OCR测试...');
    
    // 创建一个简单的测试canvas
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 50;
    const ctx = canvas.getContext('2d');
    
    // 绘制测试文字
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, 200, 50);
    ctx.fillStyle = 'black';
    ctx.font = '20px Arial';
    ctx.fillText('TEST OCR', 10, 30);
    
    // 转换为Blob
    return new Promise((resolve) => {
      canvas.toBlob(async (blob) => {
        try {
          // 动态导入Tesseract
          const Tesseract = await import('tesseract.js');
          
          const worker = await Tesseract.createWorker({
            logger: (m) => console.log('测试进度:', m.status, m.progress)
          });
          
          await worker.loadLanguage('eng');
          await worker.initialize('eng');
          
          const { data: { text } } = await worker.recognize(blob);
          await worker.terminate();
          
          const success = text.toLowerCase().includes('test');
          console.log(success ? '✅ OCR测试成功' : '❌ OCR测试失败');
          console.log('识别结果:', text);
          
          resolve({ success, text });
        } catch (error) {
          console.error('❌ OCR测试失败:', error);
          resolve({ success: false, error: error.message });
        }
      });
    });
  } catch (error) {
    console.error('❌ 无法执行OCR测试:', error);
    return { success: false, error: error.message };
  }
};

// 在浏览器环境中添加到全局对象
if (typeof window !== 'undefined') {
  window.ocrDiagnostic = {
    runOCRDiagnostic,
    quickOCRTest,
    checkTesseractAvailability,
    checkCDNAccess,
    checkWebWorkerSupport,
    checkWebAssemblySupport
  };
  
  console.log('🔧 OCR诊断工具已加载到 window.ocrDiagnostic');
  console.log('💡 运行 window.ocrDiagnostic.runOCRDiagnostic() 开始诊断');
} 