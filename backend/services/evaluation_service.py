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
        """动态提取各维度评分"""
        dimensions = {}
        
        # 首先查找"各维度评分:"部分
        dimension_section_pattern = r'各维度评分[：:]?\s*\n(.+?)(?=\n评分理由|$)'
        dimension_section_match = re.search(dimension_section_pattern, text, re.DOTALL)
        
        if dimension_section_match:
            dimension_section = dimension_section_match.group(1)
            self.logger.info("找到各维度评分部分，开始解析")
            
            # 解析每一行的维度分数，支持多种格式
            lines = dimension_section.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 尝试多种模式来匹配维度分数
                patterns = [
                    r'(.+?)[：:]\s*(\d+(?:\.\d+)?)\s*/?\s*(\d+)?',  # 准确性: 4/4 或 准确性: 4
                    r'(.+?)\s*(\d+(?:\.\d+)?)\s*/\s*(\d+)',        # 准确性 4/4
                    r'(.+?)[：:]\s*\[.*?(\d+(?:\.\d+)?).*?\]',      # 准确性: [详细说明 4分]
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        dimension_name = match.group(1).strip()
                        score = float(match.group(2))
                        
                        # 标准化维度名称映射
                        dimension_key = self._normalize_dimension_name(dimension_name)
                        dimensions[dimension_key] = score
                        
                        self.logger.debug(f"提取维度分数: {dimension_name} -> {dimension_key} = {score}")
                        break
        else:
            # 回退到新维度体系的模式匹配
            self.logger.info("未找到标准的各维度评分格式，尝试新维度体系模式匹配")
            new_dimension_patterns = {
                '数据准确性': [r'数据准确性[：:]?\s*(\d+(?:\.\d+)?)', r'准确性[：:]?\s*(\d+(?:\.\d+)?)'],
                '数据时效性': [r'数据时效性[：:]?\s*(\d+(?:\.\d+)?)', r'时效性[：:]?\s*(\d+(?:\.\d+)?)'],
                '内容完整性': [r'内容完整性[：:]?\s*(\d+(?:\.\d+)?)', r'完整性[：:]?\s*(\d+(?:\.\d+)?)'],
                '用户视角': [r'用户视角[：:]?\s*(\d+(?:\.\d+)?)', r'用户体验[：:]?\s*(\d+(?:\.\d+)?)', r'清晰度[：:]?\s*(\d+(?:\.\d+)?)', r'可用性[：:]?\s*(\d+(?:\.\d+)?)']
            }
            
            for dimension_name, patterns in new_dimension_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        dimensions[dimension_name] = float(match.group(1))
                        self.logger.debug(f"新维度体系匹配: {dimension_name} = {match.group(1)}")
                        break  # 找到匹配就跳出内层循环
        
        self.logger.info(f"成功提取 {len(dimensions)} 个维度分数: {list(dimensions.keys())}")
        return dimensions
    
    def _normalize_dimension_name(self, dimension_name):
        """标准化维度名称为新维度体系的名称"""
        # 新维度体系的映射表，完全使用中文名称
        new_dimension_mapping = {
            '数据准确性': '数据准确性',
            '数据时效性': '数据时效性', 
            '内容完整性': '内容完整性',
            '用户视角': '用户视角',
            # 兼容旧维度名称到新维度的映射
            '准确性': '数据准确性',
            '时效性': '数据时效性',
            '完整性': '内容完整性',
            '用户体验': '用户视角',
            '清晰度': '用户视角',
            '可用性': '用户视角',
            # 英文维度到新维度的映射
            'accuracy': '数据准确性',
            'timeliness': '数据时效性',
            'completeness': '内容完整性',
            'usability': '用户视角',
            'clarity': '用户视角',
            'user_experience': '用户视角'
        }
        
        # 移除可能的特殊字符和空格
        clean_name = dimension_name.strip('[](){}').strip()
        
        # 查找映射
        if clean_name in new_dimension_mapping:
            return new_dimension_mapping[clean_name]
        
        # 模糊匹配（处理部分匹配的情况）
        for key, value in new_dimension_mapping.items():
            if key in clean_name or clean_name in key:
                return value
        
        # 如果没有找到映射，直接返回原名称（保持中文）
        return clean_name if clean_name else 'unknown_dimension'

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
        return """请根据以下评估标准对模型回答进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 严格按照上述评估标准进行评分，不得放宽标准
2. 必须按照每个维度分别评分，然后计算总分
3. 每个维度都要给出具体分数和理由
4. 总分为各维度分数之和
5. 评分应趋向保守，只有真正优秀的回答才能获得高分

评估信息：
问题时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

总分: [各维度分数之和]/10

评分理由: [综合说明各维度的评分依据和总体评价]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 各维度分数相加即为总分"""
    
    def _replace_variables(self, template, variables):
        """替换模板中的变量"""
        result = template
        for key, value in variables.items():
            if value is not None:
                result = result.replace(f'{{{key}}}', str(value))
        return result 