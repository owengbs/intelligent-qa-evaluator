#!/usr/bin/env python3
"""
简化的数据库重构脚本 - 为新维度体系清空历史数据

这个脚本将：
1. 清空所有评估历史记录
2. 为新维度体系做准备
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models.classification import db, EvaluationHistory

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 基本配置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/intelligent_qa_evaluator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    return app

def clear_evaluation_history():
    """清空评估历史记录"""
    app = create_app()
    
    with app.app_context():
        try:
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
            print("✅ 数据库已为新维度体系做好准备")
            
            return True
            
        except Exception as e:
            print(f"❌ 清空评估历史记录失败: {str(e)}")
            db.session.rollback()
            return False

def main():
    """主函数"""
    print("🔄 开始数据库重构 - 为新维度体系清空历史数据")
    print("=" * 60)
    
    success = clear_evaluation_history()
    
    if success:
        print("\n✅ 数据库重构完成!")
        print("📝 接下来的步骤:")
        print("   1. 重启后端服务") 
        print("   2. 重启前端服务")
        print("   3. 进行新的评估测试")
        print("\n🎯 新维度体系包括:")
        print("   - 数据准确性 (Data Accuracy)")
        print("   - 数据时效性 (Data Timeliness)")
        print("   - 内容完整性 (Content Completeness)")
        print("   - 用户视角 (User Perspective)")
    else:
        print("\n❌ 数据库重构失败")
    
    return success

if __name__ == '__main__':
    main() 