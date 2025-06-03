#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import os
import sys
import sqlite3
import json
from datetime import datetime
import logging

# 添加父目录到Python路径，确保可以导入模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from flask import Flask
    from config import Config
    from models.classification import db, ClassificationStandard, EvaluationStandard, EvaluationHistory
    from utils.logger import get_logger
    from sqlalchemy import text
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 数据库配置
    database_path = os.path.join(parent_dir, 'data', 'qa_evaluator.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    
    db.init_app(app)
    return app

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
    
    # 创建所有表
    db.create_all()
    logger.info("数据库表创建完成")
    
    # 检查并添加人工评估字段
    check_and_add_human_evaluation_columns()
    
    # 检查是否已有默认数据
    existing_standards = ClassificationStandard.query.filter_by(is_default=True).count()
    if existing_standards > 0:
        logger.info(f"发现 {existing_standards} 条默认分类标准，跳过初始化")
        return
    
    logger.info("开始插入默认分类标准...")
    
    # 默认分类标准数据
    default_standards = [
        {
            "level1": "选股",
            "level1_definition": "解决用户没有明确标的时，筛选投资标的的需求",
            "level2": "选股",
            "level3": "策略选股",
            "level3_definition": "策略条件出发，希望得到满足至少一个条件的股票池",
            "examples": "昨天涨停的票，今天下跌的票，今天主力资金净流入的票",
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
            "level1": "分析",
            "level1_definition": "解决用户有明确投资标的时，该标的是否值得买的问题",
            "level2": "个股分析",
            "level3": "综合分析",
            "level3_definition": "包括纯标的等，及分析多个标的之间的对比",
            "examples": "纯标的输入：000001 或者 中国平安",
            "is_default": True
        },
        {
            "level1": "决策",
            "level1_definition": "解决用户买卖时机和价格的问题", 
            "level2": "个股决策",
            "level3": "操作建议",
            "level3_definition": "对明确标的的投资操作问询",
            "examples": "600900股票今天可以买入了吗",
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
        }
    ]
    
    # 插入默认分类标准
    for standard_data in default_standards:
        standard = ClassificationStandard.from_dict(standard_data)
        db.session.add(standard)
    
    logger.info("开始插入默认评估标准...")
    
    # 默认评估标准数据
    default_evaluation_standards = [
        # 选股类评估标准
        {"level2_category": "选股", "dimension": "准确性", "reference_standard": "推荐股票信息准确，代码、名称、基本数据无误", "scoring_principle": "0-4分：信息完全准确=4分；轻微错误=2分；重大错误=0分", "max_score": 4, "is_default": True},
        {"level2_category": "选股", "dimension": "策略性", "reference_standard": "选股策略清晰合理，逻辑完整", "scoring_principle": "0-3分：策略完整合理=3分；基本合理=2分；策略不清=0分", "max_score": 3, "is_default": True},
        {"level2_category": "选股", "dimension": "风险提示", "reference_standard": "充分说明投资风险", "scoring_principle": "0-2分：风险提示充分=2分；基本提示=1分；无风险提示=0分", "max_score": 2, "is_default": True},
        {"level2_category": "选股", "dimension": "实用性", "reference_standard": "推荐结果有实际参考价值", "scoring_principle": "0-1分：实用性强=1分；实用性差=0分", "max_score": 1, "is_default": True},
        
        # 个股分析类评估标准
        {"level2_category": "个股分析", "dimension": "准确性", "reference_standard": "财务数据、行业信息、公司情况等准确无误", "scoring_principle": "0-4分：数据完全准确=4分；轻微误差=2分；重大错误=0分", "max_score": 4, "is_default": True},
        {"level2_category": "个股分析", "dimension": "深度", "reference_standard": "分析深入全面，涵盖多个方面", "scoring_principle": "0-3分：分析深入全面=3分；基本到位=2分；浅显=1分；无分析=0分", "max_score": 3, "is_default": True},
        {"level2_category": "个股分析", "dimension": "逻辑性", "reference_standard": "分析逻辑清晰，结论有据", "scoring_principle": "0-2分：逻辑清晰=2分；基本合理=1分；逻辑混乱=0分", "max_score": 2, "is_default": True},
        {"level2_category": "个股分析", "dimension": "客观性", "reference_standard": "分析客观中立", "scoring_principle": "0-1分：客观中立=1分；主观偏向=0分", "max_score": 1, "is_default": True},
        
        # 个股决策类评估标准  
        {"level2_category": "个股决策", "dimension": "准确性", "reference_standard": "决策建议基于准确的数据和分析", "scoring_principle": "0-4分：依据完全准确=4分；基本准确=2分；依据错误=0分", "max_score": 4, "is_default": True},
        {"level2_category": "个股决策", "dimension": "合理性", "reference_standard": "投资建议合理可行", "scoring_principle": "0-3分：建议非常合理=3分；基本合理=2分；不够合理=1分；不合理=0分", "max_score": 3, "is_default": True},
        {"level2_category": "个股决策", "dimension": "风险控制", "reference_standard": "提供明确的风险控制措施", "scoring_principle": "0-2分：风险控制完善=2分；基本控制=1分；无风险控制=0分", "max_score": 2, "is_default": True},
        {"level2_category": "个股决策", "dimension": "可操作性", "reference_standard": "建议具体明确，可直接指导操作", "scoring_principle": "0-1分：建议具体可操作=1分；建议模糊=0分", "max_score": 1, "is_default": True},
        
        # 通用查询类评估标准
        {"level2_category": "通用查询", "dimension": "准确性", "reference_standard": "查询信息准确无误", "scoring_principle": "0-4分：信息完全准确=4分；轻微误差=2分；重大错误=0分", "max_score": 4, "is_default": True},
        {"level2_category": "通用查询", "dimension": "完整性", "reference_standard": "回答涵盖问题的所有要点", "scoring_principle": "0-3分：回答完整=3分；基本完整=2分；不够完整=1分；不完整=0分", "max_score": 3, "is_default": True},
        {"level2_category": "通用查询", "dimension": "清晰度", "reference_standard": "表达清楚易懂，条理清晰", "scoring_principle": "0-2分：表达清晰=2分；基本清晰=1分；表达混乱=0分", "max_score": 2, "is_default": True},
        {"level2_category": "通用查询", "dimension": "相关性", "reference_standard": "回答与问题高度相关", "scoring_principle": "0-1分：高度相关=1分；相关性差=0分", "max_score": 1, "is_default": True}
    ]
    
    # 插入默认评估标准
    for standard_data in default_evaluation_standards:
        standard = EvaluationStandard.from_dict(standard_data)
        db.session.add(standard)
    
    # 提交所有更改
    db.session.commit()
    logger.info("数据库初始化完成")

def check_and_add_human_evaluation_columns():
    """检查并添加人工评估相关字段"""
    try:
        # 检查是否存在人工评估字段
        result = db.session.execute(text("PRAGMA table_info(evaluation_history)"))
        columns = [row[1] for row in result.fetchall()]
        
        human_columns = [
            'human_total_score',
            'human_dimensions_json',
            'human_reasoning',
            'human_evaluation_by',
            'human_evaluation_time',
            'is_human_modified'
        ]
        
        missing_columns = [col for col in human_columns if col not in columns]
        
        if missing_columns:
            logger.info(f"需要添加的人工评估字段: {missing_columns}")
            
            # 添加缺失的字段
            column_definitions = {
                'human_total_score': 'REAL',
                'human_dimensions_json': 'TEXT',
                'human_reasoning': 'TEXT',
                'human_evaluation_by': 'VARCHAR(100)',
                'human_evaluation_time': 'DATETIME',
                'is_human_modified': 'BOOLEAN DEFAULT 0'
            }
            
            for column in missing_columns:
                sql = f"ALTER TABLE evaluation_history ADD COLUMN {column} {column_definitions[column]}"
                logger.info(f"执行SQL: {sql}")
                db.session.execute(text(sql))
            
            db.session.commit()
            logger.info("人工评估字段添加成功")
        else:
            logger.info("人工评估字段已存在，无需添加")
            
    except Exception as e:
        logger.error(f"添加人工评估字段时发生错误: {str(e)}")
        db.session.rollback()
        raise

def clear_database():
    """清空数据库（谨慎使用）"""
    try:
        logger.warning("开始清空数据库...")
        
        # 删除所有表
        db.drop_all()
        logger.info("数据库表已清空")
        
        # 重新创建表
        db.create_all()
        logger.info("数据库表已重新创建")
        
        return True
        
    except Exception as e:
        logger.error(f"清空数据库失败: {str(e)}")
        return False

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        try:
            init_database()
            logger.info("数据库初始化成功完成")
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main() 