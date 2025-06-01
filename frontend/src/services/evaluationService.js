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
      
      // 评估成功后，自动保存到历史记录
      if (response.data && response.data.score !== undefined) {
        try {
          await this.saveEvaluationHistory({
            user_input: evaluationData.user_input,
            model_answer: evaluationData.model_answer,
            reference_answer: evaluationData.reference_answer,
            question_time: evaluationData.question_time,
            evaluation_criteria: evaluationData.evaluation_criteria,
            total_score: response.data.score,
            dimensions: response.data.dimensions || {},
            reasoning: response.data.reasoning,
            raw_response: response.data.raw_response
          });
          console.log('评估结果已保存到历史记录');
        } catch (saveError) {
          console.warn('保存评估历史失败，但评估结果正常返回:', saveError);
          // 不影响主要的评估流程，只是记录警告
        }
      }
      
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

  // 保存评估结果到历史记录
  async saveEvaluationHistory(historyData) {
    try {
      const response = await this.api.post('/evaluation-history', historyData);
      return response.data;
    } catch (error) {
      console.error('保存评估历史失败:', error);
      throw new Error('保存评估历史失败');
    }
  }

  // 获取评估历史记录
  async getEvaluationHistory(params = {}) {
    try {
      const response = await this.api.get('/evaluation-history', { params });
      return response.data;
    } catch (error) {
      console.error('获取评估历史失败:', error);
      throw new Error('获取评估历史失败');
    }
  }

  // 删除评估历史记录
  async deleteEvaluationHistory(historyId) {
    try {
      const response = await this.api.delete(`/evaluation-history/${historyId}`);
      return response.data;
    } catch (error) {
      console.error('删除评估历史失败:', error);
      throw new Error('删除评估历史失败');
    }
  }

  // 获取评估统计数据
  async getEvaluationStatistics() {
    try {
      const response = await this.api.get('/evaluation-statistics');
      return response.data;
    } catch (error) {
      console.error('获取评估统计失败:', error);
      throw new Error('获取评估统计失败');
    }
  }

  // 获取维度统计数据
  async getDimensionStatistics() {
    try {
      const response = await this.api.get('/dimension-statistics');
      return response.data;
    } catch (error) {
      console.error('获取维度统计失败:', error);
      throw new Error('获取维度统计失败');
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