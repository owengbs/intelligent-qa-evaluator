#!/usr/bin/env python3
"""
数据库连接测试脚本
验证SQLAlchemy兼容性修复是否生效
"""

import os
import sys

def test_local_connection():
    """测试本地环境连接"""
    print("🏠 测试本地环境数据库连接...")
    os.environ['APP_ENV'] = 'local'
    
    try:
        from app import app, db
        from sqlalchemy import text
        import sqlalchemy
        
        print(f"   SQLAlchemy版本: {sqlalchemy.__version__}")
        
        with app.app_context():
            # 新版SQLAlchemy方式
            with db.engine.connect() as connection:
                result = connection.execute(text('SELECT 1'))
                result.fetchone()
            print("✅ 本地环境连接成功")
            return True
            
    except Exception as e:
        print(f"❌ 本地环境连接失败: {str(e)}")
        return False

def test_production_connection():
    """测试生产环境连接"""
    print("🌐 测试生产环境数据库连接...")
    os.environ['APP_ENV'] = 'production'
    
    try:
        # 重新导入以应用新的环境配置
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        if 'app' in sys.modules:
            importlib.reload(sys.modules['app'])
            
        from app import app, db
        from sqlalchemy import text
        import sqlalchemy
        
        print(f"   SQLAlchemy版本: {sqlalchemy.__version__}")
        
        with app.app_context():
            # 新版SQLAlchemy方式
            with db.engine.connect() as connection:
                result = connection.execute(text('SELECT 1'))
                result.fetchone()
            print("✅ 生产环境连接成功")
            return True
            
    except Exception as e:
        print(f"❌ 生产环境连接失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("="*50)
    print("🔍 SQLAlchemy兼容性测试")
    print("="*50)
    
    # 测试本地环境
    local_success = test_local_connection()
    print()
    
    # 测试生产环境
    production_success = test_production_connection()
    print()
    
    # 总结结果
    print("="*50)
    print("📊 测试结果:")
    print(f"   🏠 本地环境: {'✅ 成功' if local_success else '❌ 失败'}")
    print(f"   🌐 生产环境: {'✅ 成功' if production_success else '❌ 失败'}")
    
    if local_success and production_success:
        print("\n🎉 所有测试通过！SQLAlchemy兼容性修复成功")
        return True
    else:
        print("\n❌ 部分测试失败，需要进一步检查")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 