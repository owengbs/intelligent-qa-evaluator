"""
数据库初始化脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
sys.path.insert(0, str(backend_dir))

from flask import Flask
from models.classification import db, ClassificationStandard
from config import config
import json

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 使用开发配置
    app.config.from_object(config['development'])
    
    # 初始化数据库
    db.init_app(app)
    
    return app

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在创建数据库表...")
        
        # 创建所有表
        db.create_all()
        
        # 检查是否已有默认数据
        existing_count = ClassificationStandard.query.filter_by(is_default=True).count()
        
        if existing_count > 0:
            print(f"数据库中已存在 {existing_count} 条默认分类标准，跳过初始化")
            return
        
        print("正在插入默认分类标准...")
        
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
                "level3_definition": "基于基本面的分析，也包含股东、高管、机构的增减持情况",
                "examples": "600758股票有什么核心竞争力",
                "is_default": True
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "基本面分析-财务分析",
                "level3_definition": "专门针对公司业绩、财报情况的提问",
                "examples": "瑞可达2025年收入和利润增速预期",
                "is_default": True
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "消息面分析",
                "level3_definition": "询问近期的大事、热点等",
                "examples": "紫光股份的近期热点",
                "is_default": True
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "个股异动及涨跌归因",
                "level3_definition": "明确问涨跌原因或异动原因",
                "examples": "xx大涨是为啥？",
                "is_default": True
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "资金面分析",
                "level3_definition": "主力资金、龙虎榜、两融、大宗等资金相关的分析",
                "examples": "帮我分析下渤海汽车的资金情况和筹码分布情况",
                "is_default": True
            },
            {
                "level1": "分析",
                "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
                "level2": "个股分析",
                "level3": "技术面分析",
                "level3_definition": "包含历史行情（涨跌及成交额）的问询、及技术指标和形态相关的内容",
                "examples": "603993这个股票的最小阻力位是多少",
                "is_default": True
            },
            {
                "level1": "决策",
                "level1_definition": "解决用户买卖时机和价格的问题",
                "level2": "个股决策",
                "level3": "股价预测",
                "level3_definition": "对未来的股价表现、涨跌空间进行问询",
                "examples": "银之杰未来一个月预计会涨到多少",
                "is_default": True
            },
            {
                "level1": "决策",
                "level1_definition": "解决用户买卖时机和价格的问题",
                "level2": "个股决策",
                "level3": "操作建议",
                "level3_definition": "对明确标的（1个或者多个）的投资操作（买、卖、持有）问询，希望得到解答",
                "examples": "600900股票今天可以买入了吗，贵州茅台和五粮液哪个更值得买",
                "is_default": True
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "百科",
                "level3": "百科",
                "level3_definition": "涉及证券基础知识的问询，比如什么是分红？高送转？或者其他基础知识问询",
                "examples": "市盈率是怎么计算的？",
                "is_default": True
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "个股信息",
                "level3": "个股信息（指标）",
                "level3_definition": "个股页面下的对于个股信息的基本查询，比如股权登记日，股东大会召开时间",
                "examples": "今日股东大会几点结束",
                "is_default": True
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "客服帮助",
                "level3": "客服帮助/交易开户",
                "level3_definition": "用户对于客服、功能操作等的需求，比如怎么买港股，怎么查找龙虎榜历史记录",
                "examples": "如何拔打人工服务?新开的户绑定银行卡怎么操作?",
                "is_default": True
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "通用查询",
                "level3": "通用查询",
                "level3_definition": "一些比较泛化和轻量级的问题",
                "examples": "XX公司什么时候上市",
                "is_default": True
            },
            {
                "level1": "信息查询",
                "level1_definition": "通用查询",
                "level2": "无效问题",
                "level3": "无效问题",
                "level3_definition": "无意义问题",
                "examples": "老霉死了没股市",
                "is_default": True
            }
        ]
        
        # 批量插入默认数据
        for standard_data in default_standards:
            standard = ClassificationStandard.from_dict(standard_data)
            db.session.add(standard)
        
        try:
            db.session.commit()
            print(f"成功插入 {len(default_standards)} 条默认分类标准")
        except Exception as e:
            db.session.rollback()
            print(f"插入默认数据失败: {e}")
            raise
        
        print("数据库初始化完成！")

def reset_database():
    """重置数据库（删除所有数据）"""
    app = create_app()
    
    with app.app_context():
        print("正在重置数据库...")
        
        # 删除所有表
        db.drop_all()
        
        # 重新创建表
        db.create_all()
        
        print("数据库重置完成！")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('action', choices=['init', 'reset'], help='操作类型: init=初始化, reset=重置')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        init_database()
    elif args.action == 'reset':
        reset_database() 