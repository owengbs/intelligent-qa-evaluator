#!/usr/bin/env python3
"""
数据库重构脚本 - 为新维度体系清空历史数据

这个脚本将：
1. 清空所有评估历史记录 (evaluation_history表)
2. 重置自增ID
3. 为新维度体系做准备

新维度体系包括：
- 数据准确性 (Data Accuracy)
- 数据时效性 (Data Timeliness) 
- 内容完整性 (Content Completeness)
- 用户视角 (User Perspective)
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.classification import db, EvaluationHistory
from app import app

def backup_database():
    """备份数据库"""
    try:
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
        if not db_path:
            print("❌ 无法获取数据库路径")
            return False
            
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 使用SQLite的备份功能
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path)
        source.backup(backup)
        backup.close()
        source.close()
        
        print(f"✅ 数据库已备份至: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        return False

def clear_evaluation_history():
    """清空评估历史记录"""
    try:
        with app.app_context():
            # 获取记录数量
            count = EvaluationHistory.query.count()
            print(f"📊 当前评估历史记录数量: {count}")
            
            if count == 0:
                print("✅ 评估历史记录已为空，无需清理")
                return True
            
            # 确认操作
            confirm = input(f"⚠️  即将删除所有 {count} 条评估历史记录，是否继续？(输入 'YES' 确认): ")
            if confirm != 'YES':
                print("❌ 操作已取消")
                return False
            
            # 删除所有记录
            EvaluationHistory.query.delete()
            db.session.commit()
            
            print(f"✅ 已成功删除 {count} 条评估历史记录")
            
            # 重置自增ID (SQLite特定)
            db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', '')
            if db_path and os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='evaluation_history'")
                conn.commit()
                conn.close()
                print("✅ 已重置评估历史表的自增ID")
            
            return True
            
    except Exception as e:
        print(f"❌ 清空评估历史记录失败: {str(e)}")
        db.session.rollback()
        return False

def verify_new_dimension_structure():
    """验证新维度体系的配置"""
    try:
        from utils.database_operations import db_ops
        
        # 获取标准配置
        standards_result = db_ops.get_all_category_standards()
        if not standards_result.get('success'):
            print("⚠️  警告: 无法获取标准配置，请确保新维度体系已正确配置")
            return False
            
        standards_data = standards_result.get('data', {})
        new_dimensions = {'数据准确性', '数据时效性', '内容完整性', '用户视角'}
        
        print("\n📋 新维度体系配置验证:")
        for category, dimensions in standards_data.items():
            category_dimensions = {d.get('name') for d in dimensions}
            intersection = new_dimensions.intersection(category_dimensions)
            
            print(f"  📁 {category}:")
            print(f"    - 配置的维度: {sorted(category_dimensions)}")
            print(f"    - 新维度覆盖: {sorted(intersection)} ({len(intersection)}/{len(new_dimensions)})")
            
            if not intersection:
                print(f"    ⚠️  警告: {category} 未配置任何新维度")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证新维度体系配置失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔄 开始数据库重构 - 为新维度体系清空历史数据")
    print("=" * 60)
    
    # 步骤1: 备份数据库
    print("\n📦 步骤1: 备份数据库")
    if not backup_database():
        print("❌ 数据库备份失败，停止操作")
        return False
    
    # 步骤2: 验证新维度体系配置
    print("\n🔍 步骤2: 验证新维度体系配置")
    verify_new_dimension_structure()
    
    # 步骤3: 清空评估历史记录
    print("\n🗑️  步骤3: 清空评估历史记录")
    if not clear_evaluation_history():
        print("❌ 清空评估历史记录失败")
        return False
    
    print("\n✅ 数据库重构完成!")
    print("📝 接下来的步骤:")
    print("   1. 确保新维度体系的标准已正确配置")
    print("   2. 重启后端服务") 
    print("   3. 重启前端服务")
    print("   4. 进行新的评估测试")
    print("\n🎯 新维度体系包括:")
    print("   - 数据准确性 (Data Accuracy)")
    print("   - 数据时效性 (Data Timeliness)")
    print("   - 内容完整性 (Content Completeness)")
    print("   - 用户视角 (User Perspective)")
    
    return True

if __name__ == '__main__':
    main() 