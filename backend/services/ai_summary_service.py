#!/usr/bin/env python3
"""
AI总结服务 - 使用Venus接口的DeepSeek R1进行Badcase原因归纳总结
"""

import json
import os
from utils.logger import get_logger
from services.llm_client import LLMClient

class AISummaryService:
    def __init__(self):
        self.logger = get_logger(__name__)
        # 使用系统现有的Venus接口
        self.llm_client = LLMClient()
        self.logger.info("AI总结服务初始化完成，使用Venus接口")
    
    def summarize_badcase_reasons(self, category, reasons_data):
        """
        使用Venus接口的DeepSeek R1对badcase原因进行归纳总结
        
        Args:
            category: 分类名称
            reasons_data: badcase原因数据
            
        Returns:
            dict: 总结结果
        """
        try:
            # 统计原因类型
            total_reasons = len(reasons_data['reasons'])
            human_reasons_count = len([r for r in reasons_data['reasons'] if r['type'] == 'human'])
            ai_reasons_count = len([r for r in reasons_data['reasons'] if r['type'] == 'ai'])
            
            self.logger.info(f"开始分析分类 {category} 的badcase原因: 总数{total_reasons}条 (人工{human_reasons_count}条, AI{ai_reasons_count}条), 仅使用人工评估的原因")
            
            # 构建prompt - 仅基于人工评估的原因
            prompt = self._build_summary_prompt(category, reasons_data)
            
            # 调用Venus接口，使用summary任务类型（会自动选择deepseek-r1-local-II模型）
            summary_text = self.llm_client.dialog(prompt, task_type='summary')
            
            # 解析总结结果
            parsed_summary = self._parse_summary_result(summary_text)
            
            # 计算实际使用的人工评估原因数
            human_reasons_count = len([r for r in reasons_data['reasons'] if r['type'] == 'human'])
            
            return {
                'success': True,
                'data': {
                    'category': category,
                    'total_reasons': human_reasons_count,  # 只统计人工评估的原因数
                    'summary': parsed_summary,
                    'raw_summary': summary_text
                }
            }
                
        except Exception as e:
            self.logger.error(f"AI总结失败: {str(e)}")
            return {
                'success': False,
                'message': f'AI总结失败: {str(e)}'
            }
    
    def _build_summary_prompt(self, category, reasons_data):
        """构建用于AI总结的prompt，仅基于人工评估的badcase原因"""
        reasons = reasons_data['reasons']
        
        # 只使用人工标记的原因
        human_reasons = [r['reason'] for r in reasons if r['type'] == 'human']
        
        prompt = f"""你是一个专业的质量分析专家，擅长分析问答系统的质量问题并提供改进建议。请严格按照要求的JSON格式输出结果。

请对以下{category}分类下的人工评估Badcase原因进行专业的归纳总结分析：

## 数据概况
- 分类：{category}
- 总Badcase记录数：{reasons_data.get('total_badcases', 0)}
- 人工评估Badcase原因数：{len(human_reasons)}条

## 人工评估的Badcase原因：
"""
        
        for i, reason in enumerate(human_reasons[:30], 1):  # 最多展示前30条，因为只有人工原因了
            prompt += f"{i}. {reason}\n"
        
        if len(human_reasons) > 30:
            prompt += f"... (共{len(human_reasons)}条，仅显示前30条)\n"
        
        if len(human_reasons) == 0:
            prompt += "暂无人工评估的Badcase原因。\n"
        
        prompt += """
## 分析要求
请仅基于上述人工评估的Badcase原因进行专业分析，从以下几个维度：

1. **主要问题类型**：从人工评估的原因中归纳出3-5个主要的问题类型，按严重程度排序
2. **问题频次分析**：统计各类问题在人工评估中出现的频次和占比
3. **根本原因分析**：基于人工专家的判断分析导致这些问题的根本原因
4. **改进建议**：针对人工识别的主要问题提出具体可行的改进建议
5. **优先级建议**：按人工评估的严重程度对问题进行优先级排序

注意：本次分析完全基于人工专家的评估和标记，确保分析结果的专业性和准确性。

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