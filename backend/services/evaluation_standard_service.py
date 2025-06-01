"""
评估标准服务类
"""
import json
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from models.classification import db, EvaluationStandard
from utils.logger import get_logger

class EvaluationStandardService:
    """评估标准管理服务类"""
    
    def __init__(self, app=None):
        self.logger = get_logger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
    
    def get_all_evaluation_standards(self):
        """获取所有评估标准"""
        try:
            standards = EvaluationStandard.query.order_by(
                EvaluationStandard.level2_category,
                EvaluationStandard.dimension
            ).all()
            
            result = []
            for standard in standards:
                result.append(standard.to_dict())
            
            self.logger.info(f"成功获取 {len(result)} 条评估标准")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取评估标准失败: {str(e)}")
            return []
    
    def get_evaluation_standards_by_category(self, level2_category):
        """根据二级分类获取评估标准"""
        try:
            standards = EvaluationStandard.query.filter_by(
                level2_category=level2_category
            ).order_by(EvaluationStandard.dimension).all()
            
            result = []
            for standard in standards:
                result.append(standard.to_dict())
            
            self.logger.info(f"成功获取分类 {level2_category} 的 {len(result)} 条评估标准")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取分类 {level2_category} 的评估标准失败: {str(e)}")
            return []
    
    def create_evaluation_standard(self, standard_data):
        """创建新的评估标准"""
        try:
            # 验证必要字段
            required_fields = ['level2_category', 'dimension', 'reference_standard', 'scoring_principle']
            for field in required_fields:
                if field not in standard_data or not standard_data[field]:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 检查是否已存在相同的评估标准
            existing = EvaluationStandard.query.filter_by(
                level2_category=standard_data['level2_category'],
                dimension=standard_data['dimension']
            ).first()
            
            if existing:
                raise ValueError(f"分类 {standard_data['level2_category']} 的维度 {standard_data['dimension']} 已存在")
            
            # 创建新的评估标准
            new_standard = EvaluationStandard.from_dict(standard_data)
            db.session.add(new_standard)
            db.session.commit()
            
            self.logger.info(f"成功创建评估标准: {new_standard.level2_category}-{new_standard.dimension}")
            return new_standard.to_dict()
            
        except ValueError as e:
            self.logger.warning(f"创建评估标准验证失败: {str(e)}")
            raise e
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"创建评估标准失败: {str(e)}")
            raise Exception(f"数据库操作失败: {str(e)}")
    
    def update_evaluation_standard(self, standard_id, standard_data):
        """更新评估标准"""
        try:
            standard = EvaluationStandard.query.get(standard_id)
            if not standard:
                raise ValueError(f"评估标准 ID {standard_id} 不存在")
            
            # 检查是否是默认标准，默认标准不允许修改分类和维度
            if standard.is_default and (
                'level2_category' in standard_data and standard_data['level2_category'] != standard.level2_category or
                'dimension' in standard_data and standard_data['dimension'] != standard.dimension
            ):
                raise ValueError("默认评估标准不允许修改分类和维度")
            
            # 更新字段
            updatable_fields = ['reference_standard', 'scoring_principle', 'max_score']
            if not standard.is_default:
                updatable_fields.extend(['level2_category', 'dimension'])
            
            for field in updatable_fields:
                if field in standard_data:
                    setattr(standard, field, standard_data[field])
            
            standard.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.logger.info(f"成功更新评估标准: {standard.level2_category}-{standard.dimension}")
            return standard.to_dict()
            
        except ValueError as e:
            self.logger.warning(f"更新评估标准验证失败: {str(e)}")
            raise e
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"更新评估标准失败: {str(e)}")
            raise Exception(f"数据库操作失败: {str(e)}")
    
    def delete_evaluation_standard(self, standard_id):
        """删除评估标准"""
        try:
            standard = EvaluationStandard.query.get(standard_id)
            if not standard:
                raise ValueError(f"评估标准 ID {standard_id} 不存在")
            
            # 检查是否是默认标准
            if standard.is_default:
                raise ValueError("不能删除默认评估标准")
            
            db.session.delete(standard)
            db.session.commit()
            
            self.logger.info(f"成功删除评估标准: {standard.level2_category}-{standard.dimension}")
            return True
            
        except ValueError as e:
            self.logger.warning(f"删除评估标准验证失败: {str(e)}")
            raise e
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"删除评估标准失败: {str(e)}")
            raise Exception(f"数据库操作失败: {str(e)}")
    
    def batch_update_evaluation_standards(self, standards_list):
        """批量更新评估标准"""
        try:
            updated_count = 0
            
            for standard_data in standards_list:
                if 'id' in standard_data:
                    # 更新现有标准
                    standard_id = standard_data.pop('id')
                    self.update_evaluation_standard(standard_id, standard_data)
                    updated_count += 1
                else:
                    # 创建新标准
                    self.create_evaluation_standard(standard_data)
                    updated_count += 1
            
            self.logger.info(f"批量更新完成，共处理 {updated_count} 条评估标准")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"批量更新评估标准失败: {str(e)}")
            raise e
    
    def get_evaluation_standards_grouped_by_category(self):
        """按分类分组获取评估标准"""
        try:
            standards = self.get_all_evaluation_standards()
            
            # 按分类分组
            grouped_standards = {}
            for standard in standards:
                category = standard['level2_category']
                if category not in grouped_standards:
                    grouped_standards[category] = []
                grouped_standards[category].append(standard)
            
            self.logger.info(f"成功按分类分组获取评估标准，共 {len(grouped_standards)} 个分类")
            return grouped_standards
            
        except Exception as e:
            self.logger.error(f"按分类分组获取评估标准失败: {str(e)}")
            return {}
    
    def get_evaluation_template_by_category(self, level2_category):
        """根据分类获取评估模板"""
        try:
            standards = self.get_evaluation_standards_by_category(level2_category)
            
            if not standards:
                self.logger.warning(f"分类 {level2_category} 没有找到评估标准")
                return None
            
            # 构建评估模板
            template = {
                'category': level2_category,
                'dimensions': [],
                'total_max_score': 0
            }
            
            for standard in standards:
                dimension = {
                    'name': standard['dimension'],
                    'reference_standard': standard['reference_standard'],
                    'scoring_principle': standard['scoring_principle'],
                    'max_score': standard['max_score']
                }
                template['dimensions'].append(dimension)
                template['total_max_score'] += standard['max_score']
            
            self.logger.info(f"成功生成分类 {level2_category} 的评估模板，包含 {len(standards)} 个维度")
            return template
            
        except Exception as e:
            self.logger.error(f"生成评估模板失败: {str(e)}")
            return None
    
    def init_default_evaluation_standards(self):
        """初始化默认评估标准"""
        try:
            # 检查是否已有评估标准数据
            existing_count = EvaluationStandard.query.count()
            if existing_count > 0:
                self.logger.info(f"数据库中已存在 {existing_count} 条评估标准，跳过初始化")
                return True
            
            # 默认评估标准数据
            default_standards = [
                # 选股评估标准
                {
                    "level2_category": "选股",
                    "dimension": "准确性",
                    "reference_standard": "返回股票完全符合筛选条件（如日期、资金流、涨跌幅等）",
                    "scoring_principle": "0-4分：完全符合=4分；部分符合=2分；完全不符=0分",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "选股",
                    "dimension": "完整性",
                    "reference_standard": "覆盖全部符合条件的股票（无遗漏），模糊推荐需提供推荐理由",
                    "scoring_principle": "0-3分：完整覆盖=3分；遗漏≤20%=2分；遗漏>20%=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "选股",
                    "dimension": "相关性",
                    "reference_standard": "不推荐ST/*ST股（除非明确要求），板块选股需严格匹配概念定义",
                    "scoring_principle": "0-3分：全部相关=3分；含1只无关=1分；≥2只无关=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "选股",
                    "dimension": "清晰度",
                    "reference_standard": "明确说明筛选逻辑（如'根据昨日涨停+今日下跌筛选'）",
                    "scoring_principle": "0-2分：清晰说明=2分；部分说明=1分；未说明=0分",
                    "max_score": 2,
                    "is_default": True
                },
                {
                    "level2_category": "选股",
                    "dimension": "合规性",
                    "reference_standard": "附带风险提示（如'股市有风险，决策需谨慎'）",
                    "scoring_principle": "0-2分：有提示=2分；无提示=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 宏观经济分析评估标准
                {
                    "level2_category": "宏观经济分析",
                    "dimension": "准确性",
                    "reference_standard": "数据来源为官方机构（如美联储、统计局），预测需标注依据",
                    "scoring_principle": "0-4分：数据准确+依据明确=4分；数据准确但依据模糊=2分；数据错误=0分",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "宏观经济分析",
                    "dimension": "相关性",
                    "reference_standard": "回答聚焦问题核心（如CPI超预期需分析趋势与动因）",
                    "scoring_principle": "0-3分：完全相关=3分；部分偏离=1分；无关=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "宏观经济分析",
                    "dimension": "完整性",
                    "reference_standard": "包含关键因素（如就业、通胀、政策），预测类需提供多情景分析",
                    "scoring_principle": "0-3分：覆盖所有因素=3分；遗漏1项=2分；遗漏≥2项=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "宏观经济分析",
                    "dimension": "清晰度",
                    "reference_standard": "复杂概念简化说明（如'核心CPI剔除能源价格波动'）",
                    "scoring_principle": "0-2分：通俗易懂=2分；部分晦涩=1分；难以理解=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 大盘行业分析评估标准
                {
                    "level2_category": "大盘行业分析",
                    "dimension": "准确性",
                    "reference_standard": "指数涨跌幅、行业数据与交易所一致",
                    "scoring_principle": "0-4分：数据完全正确=4分；小幅误差（±0.5%）=2分；重大错误=0分",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "大盘行业分析",
                    "dimension": "相关性",
                    "reference_standard": "回答需关联问题范围（如'牛市'需结合经济周期、成交量等）",
                    "scoring_principle": "0-3分：紧密关联=3分；部分关联=1分；无关=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "大盘行业分析",
                    "dimension": "可用性",
                    "reference_standard": "提供关键指标对比（如行业PE分位数、资金流入排名）",
                    "scoring_principle": "0-3分：提供≥3项指标=3分；1-2项=1分；无指标=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "大盘行业分析",
                    "dimension": "合规性",
                    "reference_standard": "避免绝对结论（如'必定进入牛市'）",
                    "scoring_principle": "0-2分：措辞谨慎=2分；存在绝对化表述=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 个股分析评估标准
                {
                    "level2_category": "个股分析",
                    "dimension": "准确性",
                    "reference_standard": "财务数据与财报一致，技术指标计算正确（如阻力位基于K线）",
                    "scoring_principle": "0-4分：全部正确=4分；1处错误=2分；≥2处错误=0分",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "个股分析",
                    "dimension": "完整性",
                    "reference_standard": "综合分析需覆盖≥2个维度（如基本面+资金面），归因分析需列≥2个原因",
                    "scoring_principle": "0-3分：覆盖多维度=3分；单一维度=1分；无分析=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "个股分析",
                    "dimension": "相关性",
                    "reference_standard": "异动归因需结合当日新闻或资金流向（如'大涨因政策利好+主力买入'）",
                    "scoring_principle": "0-3分：紧密关联事件=3分；部分关联=1分；无关=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "个股分析",
                    "dimension": "清晰度",
                    "reference_standard": "术语标准化（如'ROE=净利润/净资产'），避免模糊表述",
                    "scoring_principle": "0-2分：清晰无歧义=2分；部分模糊=1分；难以理解=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 个股决策评估标准
                {
                    "level2_category": "个股决策",
                    "dimension": "合规性",
                    "reference_standard": "严禁直接建议操作（如'应买入'），改用'可关注''需谨慎'",
                    "scoring_principle": "0-4分：完全合规=4分；1处违规=0分（一票否决）",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "个股决策",
                    "dimension": "可用性",
                    "reference_standard": "提供决策依据（如'估值低于行业30%+资金流入'），对比标的需列关键指标",
                    "scoring_principle": "0-3分：依据充分=3分；部分依据=1分；无依据=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "个股决策",
                    "dimension": "完整性",
                    "reference_standard": "股价预测需标注概率区间（如'70%概率在20-25元'），操作建议需提示风险",
                    "scoring_principle": "0-3分：含概率/风险提示=3分；缺1项=1分；全缺=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "个股决策",
                    "dimension": "清晰度",
                    "reference_standard": "明确区分客观数据与主观判断（如'据财报数据...但市场情绪可能波动'）",
                    "scoring_principle": "0-2分：明确区分=2分；混合表述=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 信息查询评估标准
                {
                    "level2_category": "信息查询",
                    "dimension": "准确性",
                    "reference_standard": "百科定义符合权威解释，个股信息与公告一致（如股权登记日）",
                    "scoring_principle": "0-4分：完全正确=4分；部分正确=2分；错误=0分",
                    "max_score": 4,
                    "is_default": True
                },
                {
                    "level2_category": "信息查询",
                    "dimension": "时效性",
                    "reference_standard": "实时信息更新及时（如'今日股东大会'需当日回答）",
                    "scoring_principle": "0-3分：实时更新=3分；延迟≤1小时=2分；延迟>1小时=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "信息查询",
                    "dimension": "相关性",
                    "reference_standard": "直接回答问题，无冗余信息（如'XX公司上市时间：2025年Q1'）",
                    "scoring_principle": "0-3分：精准回答=3分；含部分无关内容=1分；未回答=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "信息查询",
                    "dimension": "可用性",
                    "reference_standard": "操作指引需分步骤（如'绑定银行卡：1.登录APP→2.点击...'）",
                    "scoring_principle": "0-2分：步骤清晰=2分；描述混乱=0分",
                    "max_score": 2,
                    "is_default": True
                },
                
                # 无效问题评估标准
                {
                    "level2_category": "无效问题",
                    "dimension": "相关性",
                    "reference_standard": "识别无效问题（如辱骂、无关内容），不生成投资相关内容",
                    "scoring_principle": "0-3分：正确识别且不回答=3分；错误回答=0分",
                    "max_score": 3,
                    "is_default": True
                },
                {
                    "level2_category": "无效问题",
                    "dimension": "可用性",
                    "reference_standard": "提供引导话术（如'请提问投资相关问题'）",
                    "scoring_principle": "0-2分：有效引导=2分；无引导=0分",
                    "max_score": 2,
                    "is_default": True
                },
                {
                    "level2_category": "无效问题",
                    "dimension": "合规性",
                    "reference_standard": "避免政治/暴力等违规回应",
                    "scoring_principle": "0-3分：完全合规=3分；1处违规=0分（一票否决）",
                    "max_score": 3,
                    "is_default": True
                }
            ]
            
            # 批量创建评估标准
            for standard_data in default_standards:
                standard = EvaluationStandard.from_dict(standard_data)
                db.session.add(standard)
            
            db.session.commit()
            self.logger.info(f"默认评估标准初始化完成，共创建 {len(default_standards)} 条记录")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"初始化默认评估标准失败: {str(e)}")
            return False 