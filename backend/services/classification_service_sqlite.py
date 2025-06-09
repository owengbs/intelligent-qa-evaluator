"""
基于SQLite的问题分类服务类
"""
import json
import time
from datetime import datetime
from .llm_client import LLMClient
from utils.logger import get_logger
from models.classification import db, ClassificationStandard, ClassificationHistory
from sqlalchemy.exc import SQLAlchemyError

class ClassificationService:
    """问题分类服务类 - SQLite版本"""
    
    def __init__(self, app=None):
        self.logger = get_logger(__name__)
        self.llm_client = LLMClient()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
        # 不需要重复初始化 db，因为在 app.py 中已经初始化过了
    
    def classify_user_input(self, user_input):
        """
        对用户输入进行分类
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            dict: 分类结果
        """
        try:
            self.logger.info(f"开始分类用户输入，输入长度: {len(user_input)}")
            start_time = time.time()
            
            # 获取分类标准
            standards = self.get_classification_standards()
            if not standards:
                raise Exception("未找到分类标准")
            
            # 构建分类prompt
            prompt = self._build_classification_prompt(user_input, standards)
            
            # 调用LLM进行分类，指定使用classification任务类型
            response = self.llm_client.dialog(prompt, task_type='classification')
            
            # 解析分类结果
            classification_result = self._parse_classification_result(response)
            
            # 计算分类耗时
            classification_time = time.time() - start_time
            classification_result['classification_time_seconds'] = round(classification_time, 3)
            
            # 保存分类历史
            self._save_classification_history(user_input, classification_result, classification_time)
            
            self.logger.info(f"分类完成: {classification_result.get('level1')} -> {classification_result.get('level2')} -> {classification_result.get('level3')}, 耗时: {classification_time:.3f}s")
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"用户输入分类失败: {str(e)}")
            # 返回默认分类结果
            return {
                'level1': '信息查询',
                'level1_definition': '解决用户对股票市场信息的查询需求',
                'level2': '信息查询', 
                'level3': '通用查询',
                'level3_definition': '一些比较泛化和轻量级的问题',
                'confidence': 0.5,
                'classification_time_seconds': 0,
                'error': str(e)
            }
    
    def _save_classification_history(self, user_input, classification_result, classification_time):
        """保存分类历史到数据库"""
        try:
            # 获取当前使用的模型名称
            current_model = self.llm_client.models.get('classification', self.llm_client.default_model)
            
            history = ClassificationHistory(
                user_input=user_input,
                classification_result=json.dumps(classification_result, ensure_ascii=False),
                confidence=classification_result.get('confidence'),
                classification_time=classification_time,
                model_used=current_model
            )
            
            db.session.add(history)
            db.session.commit()
            
            self.logger.debug(f"分类历史已保存: {history.id}")
            
        except SQLAlchemyError as e:
            self.logger.error(f"保存分类历史失败: {str(e)}")
            db.session.rollback()
    
    def _build_classification_prompt(self, user_input, standards):
        """构建分类prompt"""
        
        # 记录用户输入
        self.logger.info(f"构建分类prompt - 用户输入: '{user_input}' (长度: {len(user_input)})")
        
        # 从数据库获取分类标准
        classification_standards_text = self._format_classification_standards(standards)
        
        # 记录分类标准
        self.logger.debug(f"分类标准文本长度: {len(classification_standards_text)}")
        
        prompt = f"""请根据以下分类标准，对用户输入进行准确分类。

分类标准：
{classification_standards_text}

用户输入：{user_input}

请分析用户输入的问题类型，并严格按照以下JSON格式返回分类结果：

{{
    "level1": "一级分类名称",
    "level2": "二级分类名称", 
    "level3": "三级分类名称",
    "level1_definition": "一级分类定义",
    "level2_definition": "二级分类定义",
    "level3_definition": "三级分类定义",
    "confidence": 0.95,
    "reasoning": "分类理由和分析过程"
}}

注意：
1. 请仔细分析用户问题的核心意图
2. 置信度用0-1之间的数字表示
3. 必须选择已有的分类，不能创建新分类
4. 如果不确定，选择最相近的分类"""

        # 记录完整的prompt
        self.logger.info(f"构建的完整prompt (总长度: {len(prompt)}):")
        self.logger.info("=" * 50)
        self.logger.info(prompt)
        self.logger.info("=" * 50)

        return prompt
    
    def _format_classification_standards(self, standards):
        """从数据库格式化分类标准为文本"""
        try:
            formatted_text = ""
            
            # 格式化输出
            for standard in standards['standards']:
                formatted_text += f"\n【{standard['level1']}】（{standard['level1_definition']}）\n"
                
                formatted_text += f"  └─ {standard['level2']}\n"
                
                formatted_text += f"     └─ {standard['level3']}: {standard['level3_definition']}\n"
                formatted_text += f"        示例: {standard['examples']}\n"
            
            return formatted_text
            
        except SQLAlchemyError as e:
            self.logger.error(f"从数据库获取分类标准失败: {str(e)}")
            return self._get_default_standards_text()
    
    def _get_default_standards_text(self):
        """获取默认分类标准文本（备用）"""
        return """
【选股】（解决用户没有明确标的时，筛选投资标的的需求）
  └─ 选股
     └─ 策略选股: 策略条件出发，希望得到满足至少一个条件的股票池
        示例: 昨天涨停的票，今天下跌的票
     └─ 概念板块选股: 主要是问询某个板块/概念下的股票池
        示例: ai智能电力包括哪些股票
     └─ 模糊推荐: 提问很模糊，想知道近期的热门/优秀的公司
        示例: 推荐几只股票

【分析】（解决用户有明确投资标的时，该标的是否值得买的问题）
  └─ 宏观经济分析
     └─ 宏观经济分析: 主要是跟宏观经济数据相关的问题
        示例: 美国的CPI会超预期吗？
  └─ 个股分析
     └─ 综合分析: 包括纯标的等，及分析多个标的之间的对比
        示例: 纯标的输入：000001 或者 中国平安

【决策】（解决用户买卖时机和价格的问题）
  └─ 个股决策
     └─ 股价预测: 对未来的股价表现、涨跌空间进行问询
        示例: 银之杰未来一个月预计会涨到多少
     └─ 操作建议: 对明确标的的投资操作问询
        示例: 600900股票今天可以买入了吗

【信息查询】（通用查询）
  └─ 百科
     └─ 百科: 涉及证券基础知识的问询
        示例: 市盈率是怎么计算的？
  └─ 通用查询
     └─ 通用查询: 一些比较泛化和轻量级的问题
        示例: XX公司什么时候上市
"""
    
    def _parse_classification_result(self, classification_text):
        """解析分类结果"""
        try:
            self.logger.debug(f"原始分类响应: {classification_text}")
            
            # 尝试提取JSON - 使用更好的正则表达式
            import re
            
            # 查找JSON对象的起始和结束位置
            json_start = classification_text.find('{')
            if json_start != -1:
                # 从第一个{开始查找匹配的}
                brace_count = 0
                json_end = -1
                for i, char in enumerate(classification_text[json_start:], json_start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end != -1:
                    json_str = classification_text[json_start:json_end]
                    # 清理JSON字符串，移除注释
                    json_str = re.sub(r'//.*', '', json_str)  # 移除行注释
                    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)  # 移除块注释
                    
                    try:
                        result = json.loads(json_str)
                        
                        # 验证必需字段
                        required_fields = ['level1', 'level2', 'level3']
                        for field in required_fields:
                            if field not in result:
                                raise ValueError(f"缺少必需字段: {field}")
                        
                        # 验证分类是否在数据库中存在
                        if self._validate_classification_exists(result['level1'], result['level2'], result['level3']):
                            # 添加原始响应
                            result['raw_response'] = classification_text
                            
                            # 确保所有字段都存在
                            self._fill_missing_fields(result)
                            
                            self.logger.info(f"JSON解析成功: {result['level1']} -> {result['level2']} -> {result['level3']}")
                            return result
                        else:
                            self.logger.warning(f"分类不存在于数据库中: {result['level1']} -> {result['level2']} -> {result['level3']}")
                            
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON解析失败: {e}")
                        raise ValueError(f"JSON格式错误: {e}")
            
            # 如果没有找到JSON，尝试其他解析方法
            raise ValueError("无法找到有效的JSON格式")
                
        except Exception as e:
            self.logger.error(f"解析分类结果失败: {str(e)}")
            
            # 使用正则表达式尝试提取分类信息
            try:
                result = self._regex_parse_classification(classification_text)
                if result:
                    return result
                
            except Exception as regex_error:
                self.logger.error(f"正则表达式解析失败: {regex_error}")
            
            # 最后的兜底方案 - 返回数据库中的第一个分类
            return self._get_fallback_classification(classification_text)
    
    def _validate_classification_exists(self, level1, level2, level3):
        """验证分类是否在数据库中存在"""
        try:
            exists = ClassificationStandard.query.filter_by(
                level1=level1,
                level2=level2, 
                level3=level3
            ).first() is not None
            
            return exists
            
        except SQLAlchemyError as e:
            self.logger.error(f"验证分类存在性失败: {str(e)}")
            return False
    
    def _fill_missing_fields(self, result):
        """填充缺失的字段"""
        try:
            # 从数据库获取完整信息
            standard = ClassificationStandard.query.filter_by(
                level1=result['level1'],
                level2=result['level2'],
                level3=result['level3']
            ).first()
            
            if standard:
                result['level1_definition'] = result.get('level1_definition') or standard.level1_definition
                result['level2_definition'] = result.get('level2_definition') or standard.level1_definition
                result['level3_definition'] = result.get('level3_definition') or standard.level3_definition
            else:
                # 使用默认值
                result['level1_definition'] = result.get('level1_definition') or result.get('level1', '未知')
                result['level2_definition'] = result.get('level2_definition') or result.get('level2', '未知')
                result['level3_definition'] = result.get('level3_definition') or result.get('level3', '未知')
            
            # 其他默认字段
            if 'confidence' not in result:
                result['confidence'] = 0.8
            if 'reasoning' not in result:
                result['reasoning'] = '自动解析结果'
                
        except SQLAlchemyError as e:
            self.logger.error(f"填充字段信息失败: {str(e)}")
            # 使用默认值
            result['level1_definition'] = result.get('level1', '未知')
            result['level2_definition'] = result.get('level2', '未知')  
            result['level3_definition'] = result.get('level3', '未知')
            result['confidence'] = 0.8
            result['reasoning'] = '自动解析结果'
    
    def _regex_parse_classification(self, classification_text):
        """使用正则表达式解析分类"""
        import re
        
        level1_patterns = [
            r'"level1"\s*:\s*"([^"]+)"',
            r'一级分类[：:]\s*"?([^"\\n\\r,}]+)"?',
            r'level1[：:]\s*"?([^"\\n\\r,}]+)"?'
        ]
        
        level2_patterns = [
            r'"level2"\s*:\s*"([^"]+)"',
            r'二级分类[：:]\s*"?([^"\\n\\r,}]+)"?',
            r'level2[：:]\s*"?([^"\\n\\r,}]+)"?'
        ]
        
        level3_patterns = [
            r'"level3"\s*:\s*"([^"]+)"',
            r'三级分类[：:]\s*"?([^"\\n\\r,}]+)"?',
            r'level3[：:]\s*"?([^"\\n\\r,}]+)"?'
        ]
        
        level1 = self._extract_with_patterns(level1_patterns, classification_text)
        level2 = self._extract_with_patterns(level2_patterns, classification_text)
        level3 = self._extract_with_patterns(level3_patterns, classification_text)
        
        if level1 and level2 and level3:
            # 验证分类是否在数据库中存在
            if self._validate_classification_exists(level1, level2, level3):
                result = {
                    'level1': level1,
                    'level2': level2,
                    'level3': level3,
                    'confidence': 0.6,
                    'reasoning': '正则表达式解析结果',
                    'raw_response': classification_text
                }
                self._fill_missing_fields(result)
                return result
        
        return None
    
    def _extract_with_patterns(self, patterns, text):
        """使用多个模式尝试提取"""
        import re
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _get_fallback_classification(self, classification_text):
        """获取兜底分类"""
        try:
            # 获取数据库中的第一个"信息查询"分类
            fallback = ClassificationStandard.query.filter_by(level1='信息查询').first()
            
            if fallback:
                return {
                    'level1': fallback.level1,
                    'level2': fallback.level2,
                    'level3': fallback.level3,
                    'level1_definition': fallback.level1_definition,
                    'level2_definition': fallback.level1_definition,
                    'level3_definition': fallback.level3_definition,
                    'confidence': 0.0,
                    'reasoning': '解析失败，使用兜底分类',
                    'raw_response': classification_text
                }
            else:
                # 如果数据库中也没有，使用硬编码的默认值
                return {
                    'level1': '信息查询',
                    'level2': '通用查询',
                    'level3': '通用查询',
                    'level1_definition': '通用查询',
                    'level2_definition': '通用查询',
                    'level3_definition': '一些比较泛化和轻量级的问题',
                    'confidence': 0.0,
                    'reasoning': '解析失败，使用默认分类',
                    'raw_response': classification_text
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"获取兜底分类失败: {str(e)}")
            return {
                'level1': '信息查询',
                'level2': '通用查询',
                'level3': '通用查询',
                'level1_definition': '通用查询',
                'level2_definition': '通用查询',
                'level3_definition': '一些比较泛化和轻量级的问题',
                'confidence': 0.0,
                'reasoning': '解析失败，使用默认分类',
                'raw_response': classification_text
            }
    
    def get_classification_standards(self):
        """获取当前分类标准"""
        try:
            standards = ClassificationStandard.query.all()
            standards_list = [standard.to_dict() for standard in standards]
            
            return {
                'standards': standards_list,
                'total_count': len(standards_list),
                'last_updated': datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取分类标准失败: {str(e)}")
            return {
                'standards': [],
                'total_count': 0,
                'last_updated': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def update_classification_standards(self, new_standards):
        """更新分类标准"""
        try:
            # 验证新标准格式
            required_fields = ['level1', 'level1_definition', 'level2', 'level3', 'level3_definition', 'examples']
            
            for standard in new_standards:
                for field in required_fields:
                    if field not in standard:
                        raise ValueError(f"分类标准缺少必需字段: {field}")
            
            # 开始数据库事务
            # 删除所有非默认标准
            ClassificationStandard.query.filter_by(is_default=False).delete()
            
            # 插入新标准
            for standard_data in new_standards:
                # 检查是否为默认标准（如果ID存在且is_default=True）
                is_default = standard_data.get('is_default', False)
                
                # 如果是更新现有的默认标准
                if 'id' in standard_data and is_default:
                    existing = ClassificationStandard.query.get(standard_data['id'])
                    if existing and existing.is_default:
                        # 更新现有的默认标准
                        existing.level1 = standard_data['level1']
                        existing.level1_definition = standard_data['level1_definition']
                        existing.level2 = standard_data['level2']
                        existing.level3 = standard_data['level3']
                        existing.level3_definition = standard_data['level3_definition']
                        existing.examples = standard_data['examples']
                        continue
                
                # 创建新标准（不设置is_default，默认为False）
                new_standard = ClassificationStandard.from_dict(standard_data)
                new_standard.is_default = False  # 用户添加的标准不是默认标准
                db.session.add(new_standard)
            
            db.session.commit()
            self.logger.info(f"分类标准已更新，共 {len(new_standards)} 条")
            
            return {
                'success': True,
                'message': f'分类标准更新成功，共 {len(new_standards)} 条',
                'updated_count': len(new_standards),
                'timestamp': datetime.now().isoformat()
            }
            
        except (SQLAlchemyError, ValueError) as e:
            db.session.rollback()
            self.logger.error(f"更新分类标准失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def reset_classification_standards(self):
        """重置为默认分类标准"""
        try:
            # 删除所有非默认标准
            deleted_count = ClassificationStandard.query.filter_by(is_default=False).delete()
            
            db.session.commit()
            
            # 获取剩余的默认标准数量
            default_count = ClassificationStandard.query.filter_by(is_default=True).count()
            
            self.logger.info(f"分类标准已重置，删除了 {deleted_count} 条用户标准，保留 {default_count} 条默认标准")
            
            return {
                'success': True,
                'message': f'分类标准已重置为默认值，当前共 {default_count} 条标准',
                'reset_count': default_count,
                'deleted_count': deleted_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"重置分类标准失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_classification_history(self, limit=100):
        """获取分类历史记录"""
        try:
            history = ClassificationHistory.query.order_by(
                ClassificationHistory.created_at.desc()
            ).limit(limit).all()
            
            history_list = [record.to_dict() for record in history]
            
            return {
                'history': history_list,
                'total_count': len(history_list),
                'timestamp': datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取分类历史失败: {str(e)}")
            return {
                'history': [],
                'total_count': 0,
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def get_prompt_template_by_classification(self, classification_result):
        """根据分类结果获取对应的prompt模板"""
        
        level1 = classification_result.get('level1', '信息查询')
        level2 = classification_result.get('level2', '通用查询')
        level3 = classification_result.get('level3', '通用查询')
        
        # 基于分类的专用prompt模板（与原版本相同）
        prompt_templates = {
            '选股': {
                'default': """请根据以下详细的评估标准对选股类问题的回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 股票推荐必须有充分的基本面分析支撑，缺乏深度分析应大幅扣分
2. 投资策略必须完整包含买入时机、持有期限、止损策略等，否则严重扣分
3. 风险提示必须具体且充分，通用风险警告不得分
4. 数据的准确性要求极高，任何数据错误都应重罚
5. 评分应趋向保守，只有真正优秀的回答才能获得高分
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，特别关注选股建议的专业性缺陷和风险提示不足]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数"""
            },
            '分析': {
                'default': """请根据以下详细的评估标准对分析类问题的回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 分析必须具有专业深度，浅显分析应大幅扣分
2. 数据引用必须准确且有来源，未标注来源或数据错误应重罚
3. 逻辑推理必须严密完整，存在逻辑跳跃或漏洞应扣分
4. 结论必须客观中立，过于主观或缺乏依据应扣分
5. 评分标准从严，普通回答最多得到中等分数
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，必须指出分析的具体不足和专业性缺陷]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数""",
                
                '个股分析': """请根据以下详细的评估标准对个股分析的回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 个股基本面分析必须详细且准确，简单罗列财务指标不得高分
2. 财务数据必须准确无误，任何数据错误都应严重扣分
3. 行业对比必须具体且有说服力，泛泛而谈应扣分
4. 投资价值判断必须有充分依据，主观臆断应重罚
5. 评分从严执行，避免给出过高分数
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，必须说明个股分析的具体问题和专业性不足之处]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数"""
            },
            '决策': {
                'default': """请根据以下详细的评估标准对投资决策类问题的回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 投资建议必须有充分的分析基础，缺乏依据的建议应重罚
2. 风险评估必须具体且全面，通用风险警告不得分
3. 时机判断必须有明确依据，模糊判断应扣分
4. 操作建议必须具体可执行，空泛建议应大幅扣分
5. 决策类回答标准最严，因涉及实际投资决策
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，必须说明投资建议的问题和风险评估的不足]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数"""
            },
            '信息查询': {
                'default': """请根据以下详细的评估标准对信息查询类问题的回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 信息准确性要求极高，任何错误信息都应严重扣分
2. 回答必须高度相关，冗余或偏离主题应扣分
3. 表达必须清晰简洁，冗长啰嗦应扣分
4. 实用性要求高，对用户无实际帮助应扣分
5. 即使是信息查询也要从严评分
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，必须说明信息准确性和实用性的具体问题]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数"""
            }
        }
        
        # 选择最合适的模板
        if level1 in prompt_templates:
            if level2 in prompt_templates[level1]:
                selected_template = prompt_templates[level1][level2]
            else:
                selected_template = prompt_templates[level1]['default']
        else:
            # 使用通用模板
            selected_template = """请根据以下详细的评估标准对回答质量进行严格评分：

评估标准：
{evaluation_criteria}

严格评分要求：
1. 严格按照上述评估标准进行评分，不得放宽标准
2. 特别注意问题提出时间 {question_time}，时效性判断要求严格
3. 任何信息错误都应严重扣分，时间敏感内容要求更高
4. 回答质量评判从严，避免给出过高分数
5. 只有真正优秀的回答才能获得高分
6. 无需计算总分，总分将根据各维度分数的加权平均自动计算

评估信息：
问题提出时间: {question_time}
用户输入: {user_input}
模型回答: {model_answer}  
参考答案: {reference_answer}

评估要求：
1. 严格按照上述评估标准进行评分
2. 特别注意问题提出时间 {question_time}，判断答案在当时是否准确
3. 某些信息可能随时间变化，需要基于当时的情况进行评判
4. 对于时间敏感的内容（如历史事件、政策法规、技术发展等）要格外注意

请严格按照以下格式返回评估结果，必须包含评估标准中的所有维度:

各维度评分:
[请根据上述评估标准中的具体维度进行评分，每个维度都要有具体分数和理由]

评分理由: [详细的多行评分分析，综合说明各维度的评分依据，必须说明扣分理由，按照评估标准逐项说明问题，特别注明时间因素的考虑]

注意事项：
1. 必须为评估标准中的每个维度都给出具体分数
2. 分数必须在该维度的最大分数范围内
3. 评分格式请使用：维度名称: [分数] 分 - [评分理由]
4. 不要给出总分，系统将自动计算加权平均分数"""
        
        self.logger.info(f"为分类 {level1}->{level2}->{level3} 选择了对应的prompt模板")
        return selected_template 