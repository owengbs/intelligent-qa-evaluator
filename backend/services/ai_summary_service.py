#!/usr/bin/env python3
"""
AI总结服务 - 使用DeepSeek V3进行Badcase原因归纳总结
"""

import requests
import json
import os
from utils.logger import get_logger

class AISummaryService:
    def __init__(self):
        self.logger = get_logger(__name__)
        # DeepSeek API配置
        self.api_url = "https://api.deepseek.com/chat/completions"
        self.api_key = os.getenv('DEEPSEEK_API_KEY', '')
        
        if not self.api_key:
            self.logger.warning("DEEPSEEK_API_KEY 环境变量未设置，AI总结功能将无法使用")
    
    def summarize_badcase_reasons(self, category, reasons_data):
        """
        使用DeepSeek V3对badcase原因进行归纳总结
        
        Args:
            category: 分类名称
            reasons_data: badcase原因数据
            
        Returns:
            dict: 总结结果
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'message': 'DeepSeek API密钥未配置，请联系管理员'
                }
            
            # 构建prompt
            prompt = self._build_summary_prompt(category, reasons_data)
            
            # 调用DeepSeek API
            response = self._call_deepseek_api(prompt)
            
            if response['success']:
                summary_text = response['data']
                
                # 解析总结结果
                parsed_summary = self._parse_summary_result(summary_text)
                
                return {
                    'success': True,
                    'data': {
                        'category': category,
                        'total_reasons': len(reasons_data['reasons']),
                        'summary': parsed_summary,
                        'raw_summary': summary_text
                    }
                }
            else:
                return response
                
        except Exception as e:
            self.logger.error(f"AI总结失败: {str(e)}")
            return {
                'success': False,
                'message': f'AI总结失败: {str(e)}'
            }
    
    def _build_summary_prompt(self, category, reasons_data):
        """构建用于AI总结的prompt"""
        reasons = reasons_data['reasons']
        
        # 按类型分组原因
        ai_reasons = [r['reason'] for r in reasons if r['type'] == 'ai']
        human_reasons = [r['reason'] for r in reasons if r['type'] == 'human']
        
        prompt = f"""请对以下{category}分类下的Badcase原因进行专业的归纳总结分析：

## 数据概况
- 分类：{category}
- 总Badcase记录数：{reasons_data.get('total_badcases', 0)}
- 有原因说明的记录数：{len(reasons)}
- AI判断的Badcase原因：{len(ai_reasons)}条
- 人工标记的Badcase原因：{len(human_reasons)}条

## AI判断的Badcase原因：
"""
        
        for i, reason in enumerate(ai_reasons[:20], 1):  # 最多展示前20条
            prompt += f"{i}. {reason}\n"
        
        if len(ai_reasons) > 20:
            prompt += f"... (共{len(ai_reasons)}条，仅显示前20条)\n"
        
        prompt += "\n## 人工标记的Badcase原因：\n"
        
        for i, reason in enumerate(human_reasons[:20], 1):  # 最多展示前20条
            prompt += f"{i}. {reason}\n"
        
        if len(human_reasons) > 20:
            prompt += f"... (共{len(human_reasons)}条，仅显示前20条)\n"
        
        prompt += """
## 分析要求
请从以下几个维度进行专业分析：

1. **主要问题类型**：归纳出3-5个主要的问题类型，按严重程度排序
2. **问题频次分析**：统计各类问题出现的频次和占比
3. **根本原因分析**：分析导致这些问题的根本原因
4. **改进建议**：针对主要问题提出具体可行的改进建议
5. **优先级建议**：按紧急程度对问题进行优先级排序

## 输出格式
请按以下JSON格式输出（不要包含任何其他内容）：
```json
{
    "main_issues": [
        {
            "type": "问题类型名称",
            "description": "问题描述",
            "frequency": "出现频次",
            "percentage": "占比（%）",
            "severity": "严重程度（高/中/低）"
        }
    ],
    "root_causes": [
        "根本原因1",
        "根本原因2"
    ],
    "improvement_suggestions": [
        {
            "problem": "针对的问题",
            "suggestion": "具体改进建议",
            "priority": "优先级（高/中/低）"
        }
    ],
    "summary": "整体总结（2-3句话）"
}
```
"""
        
        return prompt
    
    def _call_deepseek_api(self, prompt):
        """调用DeepSeek API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的质量分析专家，擅长分析问答系统的质量问题并提供改进建议。请严格按照要求的JSON格式输出结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }
            
            self.logger.info("正在调用DeepSeek API进行badcase原因总结...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                self.logger.info("DeepSeek API调用成功")
                return {
                    'success': True,
                    'data': content
                }
            else:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                self.logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except requests.exceptions.Timeout:
            error_msg = "API调用超时"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
        except Exception as e:
            error_msg = f"API调用异常: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def _parse_summary_result(self, summary_text):
        """解析AI总结结果"""
        try:
            # 提取JSON内容
            start_idx = summary_text.find('{')
            end_idx = summary_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = summary_text[start_idx:end_idx]
                parsed_result = json.loads(json_str)
                
                # 验证必需字段
                required_fields = ['main_issues', 'root_causes', 'improvement_suggestions', 'summary']
                for field in required_fields:
                    if field not in parsed_result:
                        self.logger.warning(f"总结结果缺少字段: {field}")
                        parsed_result[field] = []
                
                return parsed_result
            else:
                # 如果无法解析JSON，返回原始文本
                self.logger.warning("无法解析AI总结的JSON格式，返回原始文本")
                return {
                    'main_issues': [],
                    'root_causes': [],
                    'improvement_suggestions': [],
                    'summary': summary_text,
                    'parse_error': True
                }
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {str(e)}")
            return {
                'main_issues': [],
                'root_causes': [],
                'improvement_suggestions': [],
                'summary': summary_text,
                'parse_error': True
            }
        except Exception as e:
            self.logger.error(f"总结结果解析失败: {str(e)}")
            return {
                'main_issues': [],
                'root_causes': [],
                'improvement_suggestions': [],
                'summary': "解析失败，请查看原始总结内容",
                'parse_error': True
            }

# 创建全局实例
ai_summary_service = AISummaryService() 