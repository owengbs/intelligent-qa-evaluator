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
        self.model_name = os.getenv('LLM_MODEL', "deepseek-r1-local-II")
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '10000'))
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.1'))
        self.timeout = int(os.getenv('LLM_TIMEOUT', '60'))
        
        self.logger.info(f"LLM客户端初始化完成，使用模型: {self.model_name}")
    
    def dialog(self, prompt):
        """
        调用LLM API获取响应
        
        Args:
            prompt: 输入的prompt内容
            
        Returns:
            str: LLM的响应内容
        """
        
        try:
            self.logger.info(f"发送请求到LLM API - 模型: {self.model_name}")
            self.logger.debug(f"Prompt长度: {len(prompt)}")
            
            # 构建API请求数据
            data = {
                "model": self.model_name,
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
                    self.logger.info(f"LLM API调用成功，响应长度: {len(content)}")
                    
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
    
    def get_evaluation(self, prompt, max_tokens=None, temperature=None):
        """
        获取评估结果（为了保持接口兼容性）
        
        Args:
            prompt: 评估用的完整prompt
            max_tokens: 最大token数（可选，使用默认值）
            temperature: 温度参数（可选，使用默认值）
            
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
            result = self.dialog(prompt)
            return result
        finally:
            # 恢复原始参数
            self.max_tokens = original_max_tokens
            self.temperature = original_temperature 