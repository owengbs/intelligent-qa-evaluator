#!/usr/bin/env python3
"""
快速数据库初始化脚本
专门用于远端部署环境的数据库初始化，确保评估系统能正常工作
"""

import os
import sys
import sqlite3
from datetime import datetime

def create_database_if_not_exists():
    """创建数据库文件（如果不存在）"""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"✅ 创建数据目录: {data_dir}")
    
    db_path = os.path.join(data_dir, 'qa_evaluator.db')
    if not os.path.exists(db_path):
        # 创建空数据库文件
        conn = sqlite3.connect(db_path)
        conn.close()
        print(f"✅ 创建数据库文件: {db_path}")
    
    return db_path

def init_with_flask_app():
    """使用Flask应用初始化数据库"""
    try:
        print("🚀 开始使用Flask应用初始化数据库...")
        
        # 导入Flask应用相关模块
        from app import app
        from models.classification import db, ClassificationStandard, EvaluationStandard
        from database.init_db import init_database
        
        with app.app_context():
            # 创建所有表
            db.create_all()
            print("✅ 数据库表创建成功")
            
            # 检查是否需要初始化默认数据
            cs_count = ClassificationStandard.query.count()
            es_count = EvaluationStandard.query.count()
            
            if cs_count == 0 or es_count == 0:
                print("🔄 检测到数据库为空，开始初始化默认数据...")
                init_database()
                print("✅ 默认数据初始化完成")
            else:
                print(f"✅ 数据库已包含数据: {cs_count} 分类标准, {es_count} 评估标准")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask应用初始化失败: {e}")
        return False

def init_with_direct_sql():
    """直接使用SQL初始化数据库"""
    try:
        print("🚀 开始使用直接SQL初始化数据库...")
        
        db_path = create_database_if_not_exists()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建分类标准表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classification_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level1 VARCHAR(100) NOT NULL,
                level1_definition TEXT,
                level2 VARCHAR(100) NOT NULL,
                level3 VARCHAR(100) NOT NULL,
                level3_definition TEXT,
                examples TEXT,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建评估标准表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level2_category VARCHAR(100) NOT NULL,
                dimension VARCHAR(100) NOT NULL,
                reference_standard TEXT NOT NULL,
                scoring_principle TEXT NOT NULL,
                max_score INTEGER DEFAULT 5,
                is_default BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建评估历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                model_answer TEXT NOT NULL,
                reference_answer TEXT,
                question_time DATETIME,
                evaluation_criteria TEXT,
                total_score REAL NOT NULL,
                dimensions_json TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                classification_level1 VARCHAR(100),
                classification_level2 VARCHAR(100),
                classification_level3 VARCHAR(100),
                evaluation_time_seconds REAL,
                model_used VARCHAR(100) DEFAULT 'deepseek-chat',
                raw_response TEXT,
                human_total_score REAL,
                human_dimensions_json TEXT,
                human_reasoning TEXT,
                human_evaluation_by VARCHAR(100),
                human_evaluation_time DATETIME,
                is_human_modified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✅ 数据库表创建成功")
        
        # 检查是否需要插入默认数据
        cursor.execute("SELECT COUNT(*) FROM classification_standards WHERE is_default = 1")
        cs_count = cursor.fetchone()[0]
        
        if cs_count == 0:
            print("🔄 插入默认分类标准...")
            
            # 插入默认分类标准
            default_standards = [
                ("选股", "解决用户没有明确标的时，筛选投资标的的需求", "选股", "策略选股", "策略条件出发，希望得到满足至少一个条件的股票池", "昨天涨停的票，今天下跌的票，今天主力资金净流入的票", 1),
                ("选股", "解决用户没有明确标的时，筛选投资标的的需求", "选股", "概念板块选股", "主要是问询某个板块/概念下的股票池", "ai智能电力包括哪些股票", 1),
                ("分析", "解决用户有明确投资标的时，该标的是否值得买的问题", "个股分析", "综合分析", "包括纯标的等，及分析多个标的之间的对比", "纯标的输入：000001 或者 中国平安", 1),
                ("决策", "解决用户买卖时机和价格的问题", "个股决策", "操作建议", "对明确标的的投资操作问询", "600900股票今天可以买入了吗", 1),
                ("信息查询", "通用查询", "通用查询", "通用查询", "一些比较泛化和轻量级的问题", "XX公司什么时候上市", 1)
            ]
            
            for standard in default_standards:
                cursor.execute("""
                    INSERT INTO classification_standards 
                    (level1, level1_definition, level2, level3, level3_definition, examples, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, standard)
            
            print(f"✅ 插入了 {len(default_standards)} 条默认分类标准")
        
        # 检查评估标准
        cursor.execute("SELECT COUNT(*) FROM evaluation_standards WHERE is_default = 1")
        es_count = cursor.fetchone()[0]
        
        if es_count == 0:
            print("🔄 插入默认评估标准...")
            
            # 插入默认评估标准
            default_eval_standards = [
                ("选股", "准确性", "推荐股票信息准确，代码、名称、基本数据无误", "0-4分：信息完全准确=4分；轻微错误=2分；重大错误=0分", 4, 1),
                ("选股", "策略性", "选股策略清晰合理，逻辑完整", "0-3分：策略完整合理=3分；基本合理=2分；策略不清=0分", 3, 1),
                ("选股", "风险提示", "充分说明投资风险", "0-2分：风险提示充分=2分；基本提示=1分；无风险提示=0分", 2, 1),
                ("选股", "实用性", "推荐结果有实际参考价值", "0-1分：实用性强=1分；实用性差=0分", 1, 1),
                ("个股分析", "准确性", "财务数据、行业信息、公司情况等准确无误", "0-4分：数据完全准确=4分；轻微误差=2分；重大错误=0分", 4, 1),
                ("个股分析", "深度", "分析深入全面，涵盖多个方面", "0-3分：分析深入全面=3分；基本到位=2分；浅显=1分；无分析=0分", 3, 1),
                ("个股分析", "逻辑性", "分析逻辑清晰，结论有据", "0-2分：逻辑清晰=2分；基本合理=1分；逻辑混乱=0分", 2, 1),
                ("个股分析", "客观性", "分析客观中立", "0-1分：客观中立=1分；主观偏向=0分", 1, 1),
                ("个股决策", "准确性", "决策建议基于准确的数据和分析", "0-4分：依据完全准确=4分；基本准确=2分；依据错误=0分", 4, 1),
                ("个股决策", "合理性", "投资建议合理可行", "0-3分：建议非常合理=3分；基本合理=2分；不够合理=1分；不合理=0分", 3, 1),
                ("个股决策", "风险控制", "提供明确的风险控制措施", "0-2分：风险控制完善=2分；基本控制=1分；无风险控制=0分", 2, 1),
                ("个股决策", "可操作性", "建议具体明确，可直接指导操作", "0-1分：建议具体可操作=1分；建议模糊=0分", 1, 1),
                ("通用查询", "准确性", "查询信息准确无误", "0-4分：信息完全准确=4分；轻微误差=2分；重大错误=0分", 4, 1),
                ("通用查询", "完整性", "回答涵盖问题的所有要点", "0-3分：回答完整=3分；基本完整=2分；不够完整=1分；不完整=0分", 3, 1),
                ("通用查询", "清晰度", "表达清楚易懂，条理清晰", "0-2分：表达清晰=2分；基本清晰=1分；表达混乱=0分", 2, 1),
                ("通用查询", "相关性", "回答与问题高度相关", "0-1分：高度相关=1分；相关性差=0分", 1, 1)
            ]
            
            for standard in default_eval_standards:
                cursor.execute("""
                    INSERT INTO evaluation_standards 
                    (level2_category, dimension, reference_standard, scoring_principle, max_score, is_default)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, standard)
            
            print(f"✅ 插入了 {len(default_eval_standards)} 条默认评估标准")
        
        conn.commit()
        conn.close()
        print("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 直接SQL初始化失败: {e}")
        return False

def verify_database():
    """验证数据库状态"""
    try:
        print("🔍 验证数据库状态...")
        
        from app import app
        from models.classification import ClassificationStandard, EvaluationStandard, EvaluationHistory
        
        with app.app_context():
            cs_count = ClassificationStandard.query.count()
            es_count = EvaluationStandard.query.count()
            eh_count = EvaluationHistory.query.count()
            
            print(f"📊 数据库状态:")
            print(f"  分类标准: {cs_count} 条")
            print(f"  评估标准: {es_count} 条")
            print(f"  评估历史: {eh_count} 条")
            
            if cs_count > 0 and es_count > 0:
                print("✅ 数据库初始化成功，系统可以正常使用")
                return True
            else:
                print("❌ 数据库初始化不完整")
                return False
                
    except Exception as e:
        print(f"❌ 验证数据库状态失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 智能Q&A评估系统 - 快速数据库初始化")
    print("=" * 60)
    
    # 方法1：尝试使用Flask应用初始化
    if init_with_flask_app():
        if verify_database():
            print("\n🎉 数据库初始化成功！系统可以正常使用。")
            return
    
    print("\n⚠️  Flask应用初始化失败，尝试直接SQL初始化...")
    
    # 方法2：使用直接SQL初始化
    if init_with_direct_sql():
        # 再次验证
        if verify_database():
            print("\n🎉 数据库初始化成功！系统可以正常使用。")
            return
    
    # 如果都失败了
    print("\n❌ 数据库初始化失败！")
    print("请检查以下项目：")
    print("1. Python环境和依赖是否正确安装")
    print("2. 数据目录权限是否正确")
    print("3. 是否在正确的目录下运行脚本")
    print("\n建议手动运行: python database/init_db.py")

if __name__ == '__main__':
    main() 