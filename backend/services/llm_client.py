import json
import os
import requests
from utils.logger import get_logger

class LLMClient:
    """基于用户现有API的LLM客户端封装类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # 从环境变量或使用默认配置
        self.api_base = os.getenv('LLM_API_BASE', "http://v2.open.venus.oa.com/llmproxy")
        self.api_key = os.getenv('LLM_API_KEY', "xxBZykeTGIVeqyGNaxNoMDro@2468")
        self.default_model = os.getenv('LLM_MODEL', "deepseek-v3-local-II")
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '10000'))
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.1'))
        self.timeout = int(os.getenv('LLM_TIMEOUT', '100'))
        
        # 预定义不同任务使用的模型
        self.models = {
            'classification': "deepseek-v3-local-II",  # 分类任务使用 v3
            'evaluation': "deepseek-r1-local-II",     # 评估任务使用 r1
            'default': self.default_model
        }
        
        self.logger.info(f"LLM客户端初始化完成，默认模型: {self.default_model}")
        self.logger.info(f"分类模型: {self.models['classification']}, 评估模型: {self.models['evaluation']}")
    
    def dialog(self, prompt, task_type='default'):
        """
        调用LLM API获取响应
        
        Args:
            prompt: 输入的prompt内容
            task_type: 任务类型 ('classification', 'evaluation', 'default')
            
        Returns:
            str: LLM的响应内容
        """
        # 根据任务类型选择模型
        model_name = self.models.get(task_type, self.default_model)
        
        try:
            self.logger.info(f"发送请求到LLM API - 任务类型: {task_type}, 模型: {model_name}")
            self.logger.debug(f"Prompt长度: {len(prompt)}")
            
            # 构建API请求数据
            data = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 使用requests发送POST请求
            response = requests.post(
                f"{self.api_base}/chat/completions",
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 提取响应内容
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content']
                    self.logger.info(f"LLM API调用成功，任务: {task_type}, 模型: {model_name}, 响应长度: {len(content)}")
                    
                    # 记录token使用情况（如果API返回）
                    if 'usage' in result:
                        self.logger.debug(f"使用的tokens: {result['usage']}")
                    
                    return content
                else:
                    raise Exception("API响应格式错误：没有找到choices字段")
            else:
                raise Exception(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                        
        except requests.exceptions.Timeout:
            self.logger.error(f"LLM API调用超时，超时时间: {self.timeout}秒")
            raise Exception("LLM API调用超时")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"LLM API请求异常: {str(e)}")
            raise Exception(f"LLM API请求失败: {str(e)}")
        except Exception as e:
            self.logger.error(f"LLM API调用失败: {str(e)}")
            raise e
    
    def get_evaluation(self, prompt, max_tokens=None, temperature=None, task_type='evaluation'):
        """
        获取评估结果（为了保持接口兼容性）
        
        Args:
            prompt: 评估用的完整prompt
            max_tokens: 最大token数（可选，使用默认值）
            temperature: 温度参数（可选，使用默认值）
            task_type: 任务类型，默认为evaluation
            
        Returns:
            str: 大模型的评估响应
        """
        # 临时调整参数（如果提供）
        original_max_tokens = self.max_tokens
        original_temperature = self.temperature
        
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
            
        try:
            result = self.dialog(prompt, task_type=task_type)
            return result
        finally:
            # 恢复原始参数
            self.max_tokens = original_max_tokens
            self.temperature = original_temperature 