#!/usr/bin/env python3
"""
测试分类功能的脚本
用于验证prompt构建和用户输入传递是否正确
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from services.classification_service_sqlite import ClassificationService
from database.init_db import init_database
from utils.logger import get_logger
from models.classification import db

def test_classification():
    """测试分类功能"""
    logger = get_logger(__name__)
    
    # 创建Flask应用实例
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qa_evaluator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        logger.info("初始化数据库...")
        init_database()
        
        # 创建分类服务
        logger.info("创建分类服务...")
        classification_service = ClassificationService(app)
        
        # 测试用例
        test_cases = [
            "请推荐几只优质的股票",
            "中国平安的股价走势如何？",
            "今天可以买入银之杰吗？",
            "什么是市盈率？",
            "AI概念股有哪些？"
        ]
        
        for i, test_input in enumerate(test_cases, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"测试用例 {i}: {test_input}")
            logger.info('='*60)
            
            try:
                result = classification_service.classify_user_input(test_input)
                
                logger.info(f"分类结果:")
                logger.info(f"  一级分类: {result.get('level1')}")
                logger.info(f"  二级分类: {result.get('level2')}")
                logger.info(f"  三级分类: {result.get('level3')}")
                logger.info(f"  置信度: {result.get('confidence')}")
                logger.info(f"  耗时: {result.get('classification_time_seconds')}秒")
                
                if 'error' in result:
                    logger.error(f"  错误: {result['error']}")
                    
            except Exception as e:
                logger.error(f"测试用例 {i} 失败: {str(e)}")

if __name__ == "__main__":
    print("开始测试分类功能...")
    test_classification()
    print("测试完成！") 