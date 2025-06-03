#!/usr/bin/env python3
"""
生产环境数据库初始化脚本
解决生产环境数据库连接和初始化问题
"""

import os
import sys
from pathlib import Path

# 确保设置生产环境
os.environ['APP_ENV'] = 'production'

try:
    from app import app, db
    from models.classification import ClassificationStandard, EvaluationStandard, EvaluationHistory
    from services.classification_service import ClassificationService
    from services.evaluation_standard_service import EvaluationStandardService
    import logging
    
    def init_production_database():
        """初始化生产环境数据库"""
        print("🌐 开始初始化生产环境数据库...")
        
        with app.app_context():
            try:
                # 检查数据库连接
                print("🔍 检查数据库连接...")
                db.engine.execute('SELECT 1').fetchone()
                print("✅ 数据库连接正常")
                
                # 创建所有表
                print("🏗️  创建数据库表...")
                db.create_all()
                print("✅ 数据库表创建完成")
                
                # 检查表是否存在
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                print(f"📋 已创建的表: {', '.join(tables)}")
                
                # 初始化服务
                print("🔧 初始化服务...")
                classification_service = ClassificationService()
                evaluation_service = EvaluationStandardService()
                
                # 初始化分类标准
                print("📁 初始化分类标准...")
                classification_service.init_app(app)
                
                # 初始化评估标准
                print("📊 初始化评估标准...")
                evaluation_service.init_app(app)
                
                # 统计现有数据
                classification_count = ClassificationStandard.query.count()
                evaluation_count = EvaluationStandard.query.count()
                history_count = EvaluationHistory.query.count()
                
                print("📈 数据统计:")
                print(f"   - 分类标准: {classification_count} 条")
                print(f"   - 评估标准: {evaluation_count} 条")
                print(f"   - 历史记录: {history_count} 条")
                
                # 检查是否需要迁移历史数据
                if history_count == 0:
                    print("⚠️  检测到历史记录为空，可能需要数据迁移")
                    print("💡 如果有历史数据，请使用数据迁移脚本")
                
                print("🎉 生产环境数据库初始化完成!")
                return True
                
            except Exception as e:
                print(f"❌ 数据库初始化失败: {str(e)}")
                print("🔧 诊断信息:")
                
                # 打印详细的错误诊断
                from config import config
                print(f"   - 数据库URI: {config.SQLALCHEMY_DATABASE_URI}")
                
                # 检查数据库文件路径
                if 'sqlite' in config.SQLALCHEMY_DATABASE_URI:
                    db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
                    db_dir = os.path.dirname(db_path)
                    print(f"   - 数据库文件: {db_path}")
                    print(f"   - 数据库目录: {db_dir}")
                    print(f"   - 目录存在: {os.path.exists(db_dir)}")
                    print(f"   - 目录可写: {os.access(db_dir, os.W_OK) if os.path.exists(db_dir) else 'N/A'}")
                    print(f"   - 文件存在: {os.path.exists(db_path)}")
                
                return False
    
    def check_database_health():
        """检查数据库健康状态"""
        print("🏥 数据库健康检查...")
        
        with app.app_context():
            try:
                # 测试基本连接
                result = db.engine.execute('SELECT 1').fetchone()
                print("✅ 基本连接: 正常")
                
                # 测试表访问
                count = EvaluationHistory.query.count()
                print(f"✅ 表访问: 正常 (历史记录: {count} 条)")
                
                # 测试写入权限
                test_record = EvaluationHistory(
                    user_input="测试问题",
                    model_answer="测试答案",
                    total_score=5.0
                )
                db.session.add(test_record)
                db.session.commit()
                
                # 删除测试记录
                db.session.delete(test_record)
                db.session.commit()
                print("✅ 写入权限: 正常")
                
                print("🎉 数据库健康状态: 优秀")
                return True
                
            except Exception as e:
                print(f"❌ 健康检查失败: {str(e)}")
                return False

    if __name__ == '__main__':
        print("="*50)
        print("🌐 生产环境数据库初始化工具")
        print("="*50)
        
        # 打印环境信息
        from config import print_config_info
        print_config_info()
        print()
        
        # 执行初始化
        success = init_production_database()
        
        if success:
            print("\n🔍 执行健康检查...")
            check_database_health()
        
        print("\n" + "="*50)
        print("🏁 初始化完成")
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ 导入失败: {str(e)}")
    print("💡 请确保在backend目录下运行，且已安装所有依赖")
    sys.exit(1)
except Exception as e:
    print(f"❌ 意外错误: {str(e)}")
    sys.exit(1) 