import json
import time
from datetime import datetime
from .llm_client import LLMClient
from utils.logger import get_logger

class ClassificationService:
    """问题分类服务类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.llm_client = LLMClient()
        
        # 默认分类标准
        self.default_classification_standards = [
            {
                "level1": "选股",
                "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求",
                "level2": "选股",
                "level3": "策略选股",
                "level3_definition": "策略条件出发，希望得到满足至少一个条件的股票池",
                "examples": "昨天涨停的票，今天下跌的票，今天主力资金净流入的票，以上条件必须都符合的票是哪支股票"
            },
            {
                "level1": "选股",
                "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求", 
                "level2": "选股",
                "level3": "概念板块选股",
                "level3_definition": "主要是问询某个板块/概念下的股票池",
                "examples": "ai智能电力包括哪些股票"
            },
            {
                "level1": "选股",
                "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求",
                "level2": "选股", 
                "level3": "模糊推荐",
                "level3_definition": "提问很模糊，想知道近期的热门/优秀的公司，未指明范围",
                "examples": "推荐几只股票"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "宏观经济分析",
                "level3": "宏观经济分析", 
                "level3_definition": "主要是跟宏观经济数据相关的问题",
                "examples": "美国的CPI会超预期吗？"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "大盘行业分析",
                "level3": "大盘行业分析",
                "level3_definition": "大盘或具体某个/某些指数、板块、行业相关的内容", 
                "examples": "今天大盘怎么样？现在是牛市吗？"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "综合分析",
                "level3_definition": "包括纯标的等，及分析多个标的（未指明某一维度）之间的对比",
                "examples": "纯标的输入：000001 或者 中国平安；璞泰来与宝明科技比较"
            },
            {
                "level1": "分析", 
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "基本面分析",
                "level3_definition": "基于基本面的分析，也包含股东、高管、机构的增减持情况",
                "examples": "600758股票有什么核心竞争力"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题", 
                "level2": "个股分析",
                "level3": "基本面分析-财务分析",
                "level3_definition": "专门针对公司业绩、财报情况的提问",
                "examples": "瑞可达2025年收入和利润增速预期"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析", 
                "level3": "消息面分析",
                "level3_definition": "询问近期的大事、热点等",
                "examples": "紫光股份的近期热点"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "个股异动及涨跌归因", 
                "level3_definition": "明确问涨跌原因或异动原因",
                "examples": "xx大涨是为啥？"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "资金面分析",
                "level3_definition": "主力资金、龙虎榜、两融、大宗等资金相关的分析", 
                "examples": "帮我分析下渤海汽车的资金情况和筹码分布情况"
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "技术面分析",
                "level3_definition": "包含历史行情（涨跌及成交额）的问询、及技术指标和形态相关的内容",
                "examples": "603993这个股票的最小阻力位是多少"
            },
            {
                "level1": "决策",
                "level1_definition": "解决用户买卖时机和价格的问题", 
                "level2": "个股决策",
                "level3": "股价预测",
                "level3_definition": "对未来的股价表现、涨跌空间进行问询",
                "examples": "银之杰未来一个月预计会涨到多少"
            },
            {
                "level1": "决策",
                "level1_definition": "解决用户买卖时机和价格的问题",
                "level2": "个股决策", 
                "level3": "操作建议",
                "level3_definition": "对明确标的（1个或者多个）的投资操作（买、卖、持有）问询，希望得到解答",
                "examples": "600900股票今天可以买入了吗，贵州茅台和五粮液哪个更值得买"
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "百科",
                "level3": "百科",
                "level3_definition": "涉及证券基础知识的问询，比如什么是分红？高送转？或者其他基础知识问询",
                "examples": "市盈率是怎么计算的？"
            },
            {
                "level1": "信息查询", 
                "level1_definition": "通用查询",
                "level2": "个股信息",
                "level3": "个股信息（指标）",
                "level3_definition": "个股页面下的对于个股信息的基本查询，比如股权登记日，股东大会召开时间",
                "examples": "今日股东大会几点结束"
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "客服帮助",
                "level3": "客服帮助/交易开户", 
                "level3_definition": "用户对于客服、功能操作等的需求，比如怎么买港股，怎么查找龙虎榜历史记录",
                "examples": "如何拔打人工服务?新开的户绑定银行卡怎么操作?"
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "通用查询",
                "level3": "通用查询",
                "level3_definition": "一些比较泛化和轻量级的问题",
                "examples": "XX公司什么时候上市"
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询", 
                "level2": "无效问题",
                "level3": "无效问题",
                "level3_definition": "无意义问题",
                "examples": "老霉死了没股市"
            }
        ]
        
        # 当前分类标准（可以被用户修改）
        self.current_classification_standards = self.default_classification_standards.copy()
    
    def classify_user_input(self, user_input):
        """
        对用户输入进行分类
        
        Args:
            user_input: 用户输入的问题
            
        Returns:
            dict: 分类结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"开始对用户输入进行分类: {user_input[:50]}...")
            
            # 构建分类prompt
            classification_prompt = self._build_classification_prompt(user_input)
            
            self.logger.info("发送分类请求到LLM API")
            
            # 调用LLM进行分类
            classification_response = self.llm_client.get_evaluation(classification_prompt)
            
            self.logger.info("开始解析分类结果")
            
            # 解析分类结果
            parsed_result = self._parse_classification_result(classification_response)
            
            # 添加元数据
            parsed_result.update({
                'timestamp': datetime.now().isoformat(),
                'model_used': self.llm_client.model_name,
                'classification_time_seconds': round(time.time() - start_time, 2),
                'user_input': user_input
            })
            
            self.logger.info(f"分类完成，耗时: {parsed_result['classification_time_seconds']}秒")
            self.logger.info(f"分类结果: {parsed_result.get('level1', 'N/A')} -> {parsed_result.get('level2', 'N/A')} -> {parsed_result.get('level3', 'N/A')}")
            
            return parsed_result
            
        except Exception as e:
            self.logger.error(f"分类过程中发生错误: {str(e)}")
            # 返回默认分类结果
            return {
                'level1': '信息查询',
                'level2': '通用查询', 
                'level3': '通用查询',
                'level1_definition': '通用查询',
                'level2_definition': '通用查询',
                'level3_definition': '一些比较泛化和轻量级的问题',
                'confidence': 0.0,
                'raw_response': f'分类失败: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'model_used': self.llm_client.model_name,
                'classification_time_seconds': round(time.time() - start_time, 2),
                'user_input': user_input
            }
    
    def _build_classification_prompt(self, user_input):
        """构建分类prompt"""
        
        # 构建分类标准文本
        classification_standards_text = self._format_classification_standards()
        
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

        return prompt
    
    def _format_classification_standards(self):
        """格式化分类标准为文本"""
        formatted_text = ""
        
        # 按一级分类分组
        level1_groups = {}
        for standard in self.current_classification_standards:
            level1 = standard['level1']
            if level1 not in level1_groups:
                level1_groups[level1] = {
                    'definition': standard['level1_definition'],
                    'level2_groups': {}
                }
            
            level2 = standard['level2']
            if level2 not in level1_groups[level1]['level2_groups']:
                level1_groups[level1]['level2_groups'][level2] = []
            
            level1_groups[level1]['level2_groups'][level2].append(standard)
        
        # 格式化输出
        for level1, level1_data in level1_groups.items():
            formatted_text += f"\n【{level1}】（{level1_data['definition']}）\n"
            
            for level2, standards in level1_data['level2_groups'].items():
                formatted_text += f"  └─ {level2}\n"
                
                for standard in standards:
                    formatted_text += f"     └─ {standard['level3']}: {standard['level3_definition']}\n"
                    formatted_text += f"        示例: {standard['examples']}\n"
        
        return formatted_text
    
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
                        
                        # 添加原始响应
                        result['raw_response'] = classification_text
                        
                        # 确保所有字段都存在
                        if 'level1_definition' not in result:
                            result['level1_definition'] = result.get('level1', '未知')
                        if 'level2_definition' not in result:
                            result['level2_definition'] = result.get('level2', '未知')
                        if 'level3_definition' not in result:
                            result['level3_definition'] = result.get('level3', '未知')
                        if 'confidence' not in result:
                            result['confidence'] = 0.8
                        if 'reasoning' not in result:
                            result['reasoning'] = '自动解析结果'
                        
                        self.logger.info(f"JSON解析成功: {result['level1']} -> {result['level2']} -> {result['level3']}")
                        return result
                        
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"JSON解析失败: {e}")
                        raise ValueError(f"JSON格式错误: {e}")
            
            # 如果没有找到JSON，尝试其他解析方法
            raise ValueError("无法找到有效的JSON格式")
                
        except Exception as e:
            self.logger.error(f"解析分类结果失败: {str(e)}")
            
            # 使用正则表达式尝试提取分类信息
            try:
                # 尝试从原文中提取分类结果
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
                
                level1 = None
                level2 = None
                level3 = None
                
                for pattern in level1_patterns:
                    match = re.search(pattern, classification_text, re.IGNORECASE)
                    if match:
                        level1 = match.group(1).strip()
                        break
                
                for pattern in level2_patterns:
                    match = re.search(pattern, classification_text, re.IGNORECASE)
                    if match:
                        level2 = match.group(1).strip()
                        break
                
                for pattern in level3_patterns:
                    match = re.search(pattern, classification_text, re.IGNORECASE)
                    if match:
                        level3 = match.group(1).strip()
                        break
                
                if level1 and level2 and level3:
                    # 验证分类是否在允许的范围内
                    valid_result = self._validate_and_correct_classification(level1, level2, level3)
                    if valid_result:
                        valid_result.update({
                            'confidence': 0.6,
                            'reasoning': '正则表达式解析结果',
                            'raw_response': classification_text
                        })
                        return valid_result
                
                self.logger.warning("正则表达式解析也失败，使用默认分类")
                
            except Exception as regex_error:
                self.logger.error(f"正则表达式解析失败: {regex_error}")
            
            # 最后的兜底方案
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
    
    def _validate_and_correct_classification(self, level1, level2, level3):
        """验证并修正分类结果"""
        # 在现有分类标准中查找匹配的分类
        for standard in self.current_classification_standards:
            if (standard['level1'] == level1 and 
                standard['level2'] == level2 and 
                standard['level3'] == level3):
                return {
                    'level1': standard['level1'],
                    'level2': standard['level2'],
                    'level3': standard['level3'],
                    'level1_definition': standard['level1_definition'],
                    'level2_definition': standard.get('level2_definition', standard['level1_definition']),
                    'level3_definition': standard['level3_definition']
                }
        
        # 如果没有完全匹配，尝试部分匹配
        for standard in self.current_classification_standards:
            if standard['level1'] == level1:
                self.logger.warning(f"使用部分匹配: {level1} -> {standard['level2']} -> {standard['level3']}")
                return {
                    'level1': standard['level1'],
                    'level2': standard['level2'],
                    'level3': standard['level3'],
                    'level1_definition': standard['level1_definition'],
                    'level2_definition': standard.get('level2_definition', standard['level1_definition']),
                    'level3_definition': standard['level3_definition']
                }
        
        return None
    
    def get_classification_standards(self):
        """获取当前分类标准"""
        return {
            'standards': self.current_classification_standards,
            'total_count': len(self.current_classification_standards),
            'last_updated': datetime.now().isoformat()
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
            
            self.current_classification_standards = new_standards
            self.logger.info(f"分类标准已更新，共 {len(new_standards)} 条")
            
            return {
                'success': True,
                'message': f'分类标准更新成功，共 {len(new_standards)} 条',
                'updated_count': len(new_standards),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"更新分类标准失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def reset_classification_standards(self):
        """重置为默认分类标准"""
        self.current_classification_standards = self.default_classification_standards.copy()
        self.logger.info("分类标准已重置为默认值")
        
        return {
            'success': True,
            'message': f'分类标准已重置为默认值，共 {len(self.default_classification_standards)} 条',
            'reset_count': len(self.default_classification_standards),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_prompt_template_by_classification(self, classification_result):
        """根据分类结果获取对应的prompt模板"""
        
        level1 = classification_result.get('level1', '信息查询')
        level2 = classification_result.get('level2', '通用查询')
        level3 = classification_result.get('level3', '通用查询')
        
        # 基于分类的专用prompt模板
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