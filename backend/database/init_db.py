"""
数据库初始化脚本
"""
import os
import sys

# 添加父目录到Python路径，确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from flask import Flask
    from config import Config
    from models.classification import db, ClassificationStandard, EvaluationStandard
    from utils.logger import get_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

logger = get_logger(__name__)

def create_tables():
    """创建数据库表"""
    try:
        # 创建所有表
        db.create_all()
        logger.info("数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")
        return False

def init_database():
    """初始化数据库"""
    logger.info("开始初始化数据库...")
    
    try:
        # 检查是否已有数据
        existing_standards = ClassificationStandard.query.count()
        if existing_standards > 0:
            logger.info(f"数据库中已存在 {existing_standards} 条分类标准，跳过初始化")
            
            # 检查并初始化评估标准
            init_evaluation_standards()
            return True
        
        # 初始化分类标准数据
        init_classification_standards()
        
        # 初始化评估标准数据  
        init_evaluation_standards()
        
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        db.session.rollback()
        return False

def init_classification_standards():
    """初始化分类标准数据"""
    logger.info("开始初始化分类标准...")
    
    # 默认分类标准数据
    default_standards = [
        {
            "level1": "选股",
            "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求",
            "level2": "选股",
            "level3": "策略选股",
            "level3_definition": "策略条件出发，希望得到满足至少一个条件的股票池",
            "examples": "昨天涨停的票，今天下跌的票，今天主力资金净流入的票，以上条件必须都符合的票是哪支股票",
            "is_default": True
        },
        {
            "level1": "选股",
            "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求", 
            "level2": "选股",
            "level3": "概念板块选股",
            "level3_definition": "主要是问询某个板块/概念下的股票池",
            "examples": "ai智能电力包括哪些股票",
            "is_default": True
        },
        {
            "level1": "选股",
            "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求",
            "level2": "选股",
            "level3": "模糊推荐",
            "level3_definition": "提问很模糊，想知道近期的热门/优秀的公司，未指明范围",
            "examples": "推荐几只股票",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "宏观经济分析",
            "level3": "宏观经济分析",
            "level3_definition": "主要是跟宏观经济数据相关的问题",
            "examples": "美国的CPI会超预期吗？",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "大盘行业分析",
            "level3": "大盘行业分析",
            "level3_definition": "大盘或具体某个/某些指数、板块、行业相关的内容",
            "examples": "今天大盘怎么样？现在是牛市吗？",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "综合分析",
            "level3_definition": "包括纯标的等，及分析多个标的（未指明某一维度）之间的对比",
            "examples": "纯标的输入：000001 或者 中国平安；璞泰来与宝明科技比较",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "基本面分析",
            "level3_definition": "主要是分析公司的基本面信息",
            "examples": "比亚迪的业绩怎么样？宁德时代财务怎么样？",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "技术面分析",
            "level3_definition": "主要是分析股票的技术指标",
            "examples": "中国平安的技术指标怎么样？",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "资金面分析",
            "level3_definition": "主要分析主力资金流入流出",
            "examples": "贵州茅台今天的资金面怎么样？",
            "is_default": True
        },
        {
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "异动归因",
            "level3_definition": "问股票当天为何大涨、大跌或异动",
            "examples": "中国平安今天为何大涨？",
            "is_default": True
        },
        {
            "level1": "决策",
            "level1_definition": "解决用户有明确投资标的时，何时买卖该标的的问题",
            "level2": "个股决策",
            "level3": "买卖决策",
            "level3_definition": "问什么时候买入、卖出股票",
            "examples": "中国平安什么时候可以买入？",
            "is_default": True
        },
        {
            "level1": "决策",
            "level1_definition": "解决用户有明确投资标的时，何时买卖该标的的问题",
            "level2": "个股决策",
            "level3": "持仓决策",
            "level3_definition": "问已有持仓的股票是否继续持有",
            "examples": "中国平安我现在持有，还能继续持有吗？",
            "is_default": True
        },
        {
            "level1": "决策",
            "level1_definition": "解决用户有明确投资标的时，何时买卖该标的的问题",
            "level2": "个股决策",
            "level3": "对比决策",
            "level3_definition": "两个或多个股票进行对比，问哪个更值得投资",
            "examples": "中国平安和中国人寿哪个更好？",
            "is_default": True
        },
        {
            "level1": "决策",
            "level1_definition": "解决用户有明确投资标的时，何时买卖该标的的问题",
            "level2": "个股决策",
            "level3": "价位预测",
            "level3_definition": "问股票未来价格走势或目标价",
            "examples": "中国平安能涨到多少？",
            "is_default": True
        },
        {
            "level1": "信息查询",
            "level1_definition": "解决用户对股票市场信息的查询需求",
            "level2": "信息查询",
            "level3": "基础信息查询",
            "level3_definition": "股票代码、公司信息、财务数据等基础信息查询",
            "examples": "中国平安的股票代码是什么？",
            "is_default": True
        },
        {
            "level1": "信息查询",
            "level1_definition": "解决用户对股票市场信息的查询需求",
            "level2": "信息查询",
            "level3": "实时数据查询",
            "level3_definition": "当前股价、涨跌幅等实时数据查询",
            "examples": "中国平安现在多少钱？",
            "is_default": True
        },
        {
            "level1": "信息查询",
            "level1_definition": "解决用户对股票市场信息的查询需求",
            "level2": "信息查询",
            "level3": "历史数据查询",
            "level3_definition": "历史价格、成交量等历史数据查询",
            "examples": "中国平安去年同期的价格是多少？",
            "is_default": True
        },
        {
            "level1": "信息查询",
            "level1_definition": "解决用户对股票市场信息的查询需求",
            "level2": "信息查询",
            "level3": "通用查询",
            "level3_definition": "一些比较泛化和轻量级的问题",
            "examples": "炒股需要什么条件？",
            "is_default": True
        },
        {
            "level1": "无效",
            "level1_definition": "无关投资或无法回答的问题",
            "level2": "无效问题",
            "level3": "无效问题",
            "level3_definition": "与投资无关或无法理解的问题",
            "examples": "你好；今天天气怎么样？",
            "is_default": True
        }
    ]
    
    try:
        # 批量创建分类标准
        for standard_data in default_standards:
            standard = ClassificationStandard.from_dict(standard_data)
            db.session.add(standard)
        
        db.session.commit()
        logger.info(f"成功插入 {len(default_standards)} 条默认分类标准")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"插入默认数据失败: {e}")
        return False

def init_evaluation_standards():
    """初始化评估标准数据"""
    logger.info("开始初始化评估标准...")
    
    try:
        # 检查是否已有评估标准数据
        existing_eval_standards = EvaluationStandard.query.count()
        if existing_eval_standards > 0:
            logger.info(f"数据库中已存在 {existing_eval_standards} 条评估标准，跳过初始化")
            return True
        
        # 默认评估标准数据
        default_evaluation_standards = [
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
        for eval_data in default_evaluation_standards:
            eval_standard = EvaluationStandard.from_dict(eval_data)
            db.session.add(eval_standard)
        
        db.session.commit()
        logger.info(f"评估标准初始化完成，共创建 {len(default_evaluation_standards)} 条记录")
        return True
        
    except Exception as e:
        logger.error(f"初始化评估标准失败: {str(e)}")
        db.session.rollback()
        return False

def main():
    """主函数"""
    # 创建临时Flask应用用于数据库操作
    app = Flask(__name__)
    app.config.from_object(Config)
    
    with app.app_context():
        # 初始化数据库
        db.init_app(app)
        
        # 创建表
        if not create_tables():
            logger.error("创建数据库表失败")
            return False
        
        # 初始化数据
        if not init_database():
            logger.error("初始化数据库数据失败")
            return False
        
        logger.info("数据库初始化完成！")
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 