import re
import time
from datetime import datetime
from .llm_client import LLMClient
from utils.logger import get_logger

class EvaluationService:
    """问答质量评估服务类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.llm_client = LLMClient()
        
        # 定义变量名映射，支持多种变体
        self.variable_mapping = {
            # 用户输入的各种变体
            'user_input': ['user_input', 'user_query', 'user_question', 'question', 'query'],
            # 模型回答的各种变体  
            'model_answer': ['model_answer', 'model_response', 'model_output', 'response', 'answer'],
            # 参考答案的各种变体
            'reference_answer': ['reference_answer', 'reference', 'standard_answer', 'correct_answer', 'target_answer'],
            # 问题时间的各种变体
            'question_time': ['question_time', 'ask_time', 'time', 'timestamp', 'date'],
            # 评估标准的各种变体
            'evaluation_criteria': ['evaluation_criteria', 'criteria', 'standards', 'scoring_criteria', 'eval_standards']
        }
        
    def evaluate_response(self, user_query, model_response, reference_answer, scoring_prompt, question_time=None, evaluation_criteria=None):
        """
        评估模型回答质量
        
        Args:
            user_query: 用户原始问题
            model_response: 待评估的模型回答
            reference_answer: 参考标准答案
            scoring_prompt: 评分规则模板
            question_time: 问题提出时间 (可选)
            evaluation_criteria: 详细的评估标准 (可选)
            
        Returns:
            dict: 包含评分结果的字典
        """
        start_time = time.time()
        
        try:
            self.logger.info("开始构建评估prompt")
            
            # 构建完整的评估prompt
            full_prompt = self._build_evaluation_prompt(
                user_query, model_response, reference_answer, scoring_prompt, question_time, evaluation_criteria
            )
            
            self.logger.info("发送请求到LLM API进行质量评估")
            
            # 调用LLM API进行评估，指定使用evaluation任务类型
            evaluation_response = self.llm_client.get_evaluation(full_prompt, task_type='evaluation')
            
            self.logger.info("开始解析评估结果")
            
            # 解析评估结果
            parsed_result = self._parse_evaluation_result(evaluation_response)
            
            # 添加元数据
            parsed_result.update({
                'timestamp': datetime.now().isoformat(),
                'evaluation_time_seconds': round(time.time() - start_time, 2),
                'question_time': question_time,  # 保存问题时间
                'evaluation_criteria_used': evaluation_criteria  # 保存评估标准
            })
            
            self.logger.info(f"评估完成，耗时: {parsed_result['evaluation_time_seconds']}秒")
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"评估过程中发生错误: {str(e)}")
            raise e
    
    def _build_evaluation_prompt(self, user_query, model_response, reference_answer, scoring_prompt, question_time=None, evaluation_criteria=None):
        """构建完整的评估prompt，支持多种变量名变体"""
        
        full_prompt = scoring_prompt
        replacement_count = 0
        
        # 创建替换值映射
        replacement_values = {
            'user_input': user_query,
            'model_answer': model_response, 
            'reference_answer': reference_answer,
            'question_time': question_time,
            'evaluation_criteria': evaluation_criteria
        }
        
        # 对每种标准变量名和其变体进行替换
        for standard_var, value in replacement_values.items():
            for variant in self.variable_mapping[standard_var]:
                pattern = '{' + variant + '}'
                if pattern in full_prompt:
                    full_prompt = full_prompt.replace(pattern, value)
                    replacement_count += 1
                    self.logger.debug(f"替换变量 {pattern} -> 内容长度: {len(value)}")
        
        # 检查是否还有未替换的变量
        remaining_vars = re.findall(r'\{([^}]+)\}', full_prompt)
        if remaining_vars:
            self.logger.warning(f"发现未识别的变量: {remaining_vars}")
            
        self.logger.info(f"总共替换了 {replacement_count} 个变量，构建的prompt长度: {len(full_prompt)}")
        
        # 如果没有进行任何替换，说明可能没有使用变量
        if replacement_count == 0:
            self.logger.warning("未发现任何可替换的变量，可能是prompt格式不正确")
            
        return full_prompt
    
    def validate_prompt_variables(self, scoring_prompt):
        """
        验证prompt中的变量是否正确
        
        Args:
            scoring_prompt: 评分规则模板
            
        Returns:
            dict: 验证结果，包含是否有效和缺失的变量
        """
        required_vars = ['user_input', 'model_answer', 'reference_answer', 'question_time', 'evaluation_criteria']
        found_vars = set()
        
        # 检查每个必需变量的所有变体
        for required_var in required_vars:
            for variant in self.variable_mapping[required_var]:
                pattern = '{' + variant + '}'
                if pattern in scoring_prompt:
                    found_vars.add(required_var)
                    break
        
        missing_vars = set(required_vars) - found_vars
        
        return {
            'is_valid': len(missing_vars) == 0,
            'missing_variables': list(missing_vars),
            'found_variables': list(found_vars)
        }
    
    def _parse_evaluation_result(self, evaluation_text):
        """
        解析大模型返回的评估结果
        提取总分和评分理由
        """
        try:
            # 使用正则表达式提取总分
            score_pattern = r'总分[：:]\s*(\d+(?:\.\d+)?)\s*/\s*10'
            score_match = re.search(score_pattern, evaluation_text)
            
            if score_match:
                score = float(score_match.group(1))
            else:
                # 备用模式
                score_pattern_alt = r'(\d+(?:\.\d+)?)\s*/\s*10'
                score_match_alt = re.search(score_pattern_alt, evaluation_text)
                score = float(score_match_alt.group(1)) if score_match_alt else 0.0
            
            # 提取评分理由
            reasoning_pattern = r'评分理由[：:]?\s*(.+)'
            reasoning_match = re.search(reasoning_pattern, evaluation_text, re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else evaluation_text
            
            # 尝试提取各维度分数 (可选功能)
            dimensions = self._extract_dimension_scores(evaluation_text)
            
            result = {
                'score': min(max(score, 0), 10),  # 确保分数在0-10范围内
                'reasoning': reasoning,
                'dimensions': dimensions,
                'raw_response': evaluation_text
            }
            
            self.logger.info(f"解析结果 - 总分: {result['score']}")
            return result
            
        except Exception as e:
            self.logger.error(f"解析评估结果时发生错误: {str(e)}")
            return {
                'score': 0.0,
                'reasoning': '解析评估结果失败，请检查输入格式',
                'dimensions': {},
                'raw_response': evaluation_text
            }
    
    def _extract_dimension_scores(self, text):
        """提取各维度评分（可选功能）"""
        dimensions = {}
        
        patterns = {
            'accuracy': r'准确性[：:]?\s*(\d+(?:\.\d+)?)',
            'completeness': r'完整性[：:]?\s*(\d+(?:\.\d+)?)', 
            'fluency': r'流畅性[：:]?\s*(\d+(?:\.\d+)?)',
            'safety': r'安全性[：:]?\s*(\d+(?:\.\d+)?)'
        }
        
        for dimension, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                dimensions[dimension] = float(match.group(1))
        
        return dimensions 

    def evaluate_qa(self, user_input, model_answer, evaluation_criteria, question_time=None, prompt_template=None):
        """
        评估问答质量（新的统一接口）
        
        Args:
            user_input: 用户输入
            model_answer: 模型回答
            evaluation_criteria: 评估标准
            question_time: 问题时间
            prompt_template: 可选的prompt模板
            
        Returns:
            dict: 评估结果
        """
        start_time = time.time()
        
        try:
            self.logger.info("开始构建QA评估prompt")
            
            # 如果提供了prompt模板，使用模板，否则使用默认模板
            if prompt_template:
                full_prompt = prompt_template
            else:
                full_prompt = self._get_default_qa_prompt()
            
            # 进行变量替换
            full_prompt = self._replace_variables(full_prompt, {
                'user_input': user_input,
                'model_answer': model_answer,
                'evaluation_criteria': evaluation_criteria,
                'question_time': question_time or datetime.now().isoformat()
            })
            
            self.logger.info("发送请求到LLM API进行QA质量评估")
            
            # 调用LLM API进行评估，指定使用evaluation任务类型
            evaluation_response = self.llm_client.get_evaluation(full_prompt, task_type='evaluation')
            
            self.logger.info("开始解析QA评估结果")
            
            # 解析评估结果
            parsed_result = self._parse_evaluation_result(evaluation_response)
            
            # 添加元数据
            parsed_result.update({
                'timestamp': datetime.now().isoformat(),
                'evaluation_time_seconds': round(time.time() - start_time, 2),
                'question_time': question_time,
                'evaluation_criteria_used': evaluation_criteria,
                'total_score': parsed_result.get('score', 0)
            })
            
            self.logger.info(f"QA评估完成，总分: {parsed_result.get('score', 0)}, 耗时: {parsed_result['evaluation_time_seconds']}秒")
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"QA评估过程中发生错误: {str(e)}")
            raise e
    
    def _get_default_qa_prompt(self):
        """获取默认的QA评估prompt模板"""
        return """请根据以下评估标准对模型回答进行评分：

评估标准：
{evaluation_criteria}

评估信息：
问题时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}

请严格按照以下格式返回评估结果:
总分: [分数]/10
评分理由: [详细的评分分析，按照评估标准逐项说明]"""
    
    def _replace_variables(self, template, variables):
        """替换模板中的变量"""
        result = template
        for key, value in variables.items():
            if value is not None:
                result = result.replace(f'{{{key}}}', str(value))
        return result 