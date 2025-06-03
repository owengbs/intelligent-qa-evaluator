#!/usr/bin/env python3
"""
配置数据导出脚本
将分类标准和评估标准数据导出为JSON文件，用于版本控制和团队同步
"""

import os
import json
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.classification import db, ClassificationStandard, EvaluationStandard


def export_classification_standards():
    """导出分类标准数据"""
    try:
        with app.app_context():
            standards = ClassificationStandard.query.all()
            data = []
            
            for standard in standards:
                # 移除数据库特定字段，保留配置数据
                standard_dict = standard.to_dict()
                # 移除ID和时间戳，这些不应该版本控制
                standard_dict.pop('id', None)
                standard_dict.pop('created_at', None)
                standard_dict.pop('updated_at', None)
                data.append(standard_dict)
            
            return data
    except Exception as e:
        print(f"❌ 导出分类标准失败: {e}")
        return []


def export_evaluation_standards():
    """导出评估标准数据"""
    try:
        with app.app_context():
            standards = EvaluationStandard.query.all()
            data = []
            
            for standard in standards:
                # 移除数据库特定字段，保留配置数据
                standard_dict = standard.to_dict()
                # 移除ID和时间戳，这些不应该版本控制
                standard_dict.pop('id', None)
                standard_dict.pop('created_at', None)
                standard_dict.pop('updated_at', None)
                data.append(standard_dict)
            
            return data
    except Exception as e:
        print(f"❌ 导出评估标准失败: {e}")
        return []


def save_config_data(output_dir='config_data'):
    """保存配置数据到JSON文件"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 导出分类标准
    print("📋 导出分类标准数据...")
    classification_data = export_classification_standards()
    classification_file = os.path.join(output_dir, 'classification_standards.json')
    
    with open(classification_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'description': '分类标准配置数据 - 用于团队同步',
            'count': len(classification_data),
            'data': classification_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分类标准已导出: {classification_file} ({len(classification_data)} 条记录)")
    
    # 导出评估标准
    print("📊 导出评估标准数据...")
    evaluation_data = export_evaluation_standards()
    evaluation_file = os.path.join(output_dir, 'evaluation_standards.json')
    
    with open(evaluation_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'description': '评估标准配置数据 - 用于团队同步',
            'count': len(evaluation_data),
            'data': evaluation_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 评估标准已导出: {evaluation_file} ({len(evaluation_data)} 条记录)")
    
    # 创建导出摘要
    summary_file = os.path.join(output_dir, 'export_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'classification_standards_count': len(classification_data),
            'evaluation_standards_count': len(evaluation_data),
            'total_records': len(classification_data) + len(evaluation_data),
            'files': [
                'classification_standards.json',
                'evaluation_standards.json'
            ],
            'description': 'AI评估系统配置数据导出摘要'
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📝 导出摘要已保存: {summary_file}")
    print(f"\n🎉 配置数据导出完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"📊 总计: {len(classification_data) + len(evaluation_data)} 条配置记录")
    
    return True


def main():
    """主函数"""
    print("🚀 开始导出AI评估系统配置数据...")
    print("=" * 50)
    
    # 检查数据库连接 - 修复API调用
    try:
        with app.app_context():
            # 使用新版SQLAlchemy API进行测试查询
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).fetchone()
            print("✅ 数据库连接正常")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("💡 请确保数据库文件存在并且应用配置正确")
        return False
    
    # 导出数据
    success = save_config_data()
    
    if success:
        print("\n" + "=" * 50)
        print("🎯 下一步操作：")
        print("1. 将 config_data/ 目录添加到Git版本控制")
        print("2. 团队成员可使用 import_config_data.py 导入配置")
        print("3. 配置数据将在团队间保持同步")
        return True
    else:
        print("\n❌ 配置数据导出失败！")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 