import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

class EvaluationService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 120000, // 2分钟超时，因为LLM评估可能需要较长时间
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        console.log('API请求:', config.method.toUpperCase(), config.url);
        return config;
      },
      (error) => {
        console.error('API请求错误:', error);
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.api.interceptors.response.use(
      (response) => {
        console.log('API响应成功:', response.status);
        return response;
      },
      (error) => {
        console.error('API响应错误:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  async evaluate(evaluationData) {
    try {
      console.log('发送评估请求:', evaluationData);
      
      // 对于评估请求，使用更长的超时时间
      const response = await this.api.post('/evaluate', evaluationData, {
        timeout: 180000, // 3分钟超时，专门针对评估请求
      });
      
      console.log('收到评估响应:', response.data);
      return response.data;
      
    } catch (error) {
      console.error('评估请求失败:', error);
      
      if (error.code === 'ECONNABORTED') {
        // 请求超时
        throw new Error('评估请求超时，大模型可能正在处理复杂内容，请稍后重试');
      } else if (error.response) {
        // 服务器返回错误响应
        throw new Error(error.response.data.error || '服务器错误');
      } else if (error.request) {
        // 请求发送失败
        throw new Error('无法连接到服务器，请检查网络连接');
      } else {
        // 其他错误
        throw new Error('请求配置错误');
      }
    }
  }

  async healthCheck() {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error('健康检查失败');
    }
  }
}

export const evaluationService = new EvaluationService(); 