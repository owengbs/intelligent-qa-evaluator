import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIAssistant:
    def __init__(self):
        self.api_url = 'http://9.135.166.211:8280/cgi-bin/api/llm_plug/chat_no_stream'
        self.params = {
            'x-timestamp': '1723113102',
            'x-sa-v': '3',
            'x-appid': 'snp',
            'x-sa-sign': '1234567890'
        }
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def ask_ai(self, question):
        """
        调用AI大模型来回答用户问题
        
        Args:
            question (str): 用户输入的问题
            
        Returns:
            dict: 包含回答结果和状态的字典
        """
        try:
            logger.info(f"🤖 AI助手收到问题: {question[:50]}...")
            
            # 构建请求数据
            data = {
                'meta': {
                    'platform': 'lily',
                    'model': 'deepseek'
                },
                'input': {
                    'messages': [question]
                }
            }
            
            # 发送请求
            logger.info("📡 正在向AI大模型发送请求...")
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                params=self.params, 
                data=json.dumps(data),
                timeout=180  # 增加到3分钟超时，适应大模型长时间处理
            )
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info("✅ AI大模型响应成功")
                
                # 提取回答内容
                if 'result' in response_data:
                    ai_answer = response_data['result']
                    return {
                        'success': True,
                        'answer': ai_answer,
                        'message': 'AI回答获取成功'
                    }
                else:
                    logger.error("❌ AI响应格式异常")
                    return {
                        'success': False,
                        'answer': '',
                        'message': 'AI响应格式异常'
                    }
            else:
                logger.error(f"❌ AI API请求失败，状态码: {response.status_code}")
                return {
                    'success': False,
                    'answer': '',
                    'message': f'AI API请求失败，状态码: {response.status_code}'
                }
                
        except requests.exceptions.Timeout:
            logger.error("⏰ AI API请求超时")
            return {
                'success': False,
                'answer': '',
                'message': 'AI API请求超时，请重试'
            }
        except requests.exceptions.ConnectionError:
            logger.error("🌐 AI API连接失败")
            return {
                'success': False,
                'answer': '',
                'message': 'AI API连接失败，请检查网络'
            }
        except Exception as e:
            logger.error(f"💥 AI调用发生未知错误: {str(e)}")
            return {
                'success': False,
                'answer': '',
                'message': f'AI调用发生错误: {str(e)}'
            }

# 创建全局实例
ai_assistant = AIAssistant() 