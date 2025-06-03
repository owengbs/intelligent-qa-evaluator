#!/usr/bin/env python3
"""
配置数据导出脚本 - 全量版本
将分类标准和评估标准数据完整导出为JSON文件，用于版本控制和团队同步
支持完整的配置数据同步，确保团队间配置一致性
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
    """导出分类标准数据 - 全量导出"""
    try:
        with app.app_context():
            # 导出所有分类标准（包括默认和用户添加的）
            standards = ClassificationStandard.query.order_by(
                ClassificationStandard.level1,
                ClassificationStandard.level2,
                ClassificationStandard.level3
            ).all()
            
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
    """导出评估标准数据 - 全量导出"""
    try:
        with app.app_context():
            # 导出所有评估标准（包括默认和用户添加的）
            standards = EvaluationStandard.query.order_by(
                EvaluationStandard.level2_category,
                EvaluationStandard.dimension
            ).all()
            
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
    """保存配置数据到JSON文件 - 全量保存"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 导出分类标准
    print("📋 导出分类标准数据（全量）...")
    classification_data = export_classification_standards()
    classification_file = os.path.join(output_dir, 'classification_standards.json')
    
    with open(classification_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'description': '分类标准配置数据 - 全量同步用于团队协作',
            'version': '2.3.0',
            'sync_mode': 'full_replace',
            'count': len(classification_data),
            'data': classification_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分类标准已导出: {classification_file} ({len(classification_data)} 条记录)")
    
    # 导出评估标准
    print("📊 导出评估标准数据（全量）...")
    evaluation_data = export_evaluation_standards()
    evaluation_file = os.path.join(output_dir, 'evaluation_standards.json')
    
    with open(evaluation_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'description': '评估标准配置数据 - 全量同步用于团队协作',
            'version': '2.3.0',
            'sync_mode': 'full_replace',
            'count': len(evaluation_data),
            'data': evaluation_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 评估标准已导出: {evaluation_file} ({len(evaluation_data)} 条记录)")
    
    # 创建导出摘要
    summary_file = os.path.join(output_dir, 'export_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'version': '2.3.0',
            'sync_mode': 'full_replace',
            'classification_standards_count': len(classification_data),
            'evaluation_standards_count': len(evaluation_data),
            'total_records': len(classification_data) + len(evaluation_data),
            'files': [
                'classification_standards.json',
                'evaluation_standards.json'
            ],
            'description': 'AI评估系统配置数据全量导出摘要 - 支持完整替换同步',
            'warning': '导入时将完全替换现有配置数据，请确保备份'
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📝 导出摘要已保存: {summary_file}")
    print(f"\n🎉 配置数据全量导出完成！")
    print(f"📁 输出目录: {os.path.abspath(output_dir)}")
    print(f"📊 总计: {len(classification_data) + len(evaluation_data)} 条配置记录")
    print(f"🔄 同步模式: 全量替换")
    
    return True


def test_database_connection():
    """测试数据库连接 - 兼容多个SQLAlchemy版本"""
    try:
        with app.app_context():
            # 尝试新版SQLAlchemy API
            try:
                from sqlalchemy import text
                result = db.session.execute(text('SELECT 1')).fetchone()
                print("✅ 数据库连接正常 (使用新版API)")
                return True
            except Exception as e1:
                # 如果新版API失败，尝试旧版API
                try:
                    result = db.engine.execute('SELECT 1').fetchone()
                    print("✅ 数据库连接正常 (使用旧版API)")
                    return True
                except Exception as e2:
                    print(f"❌ 数据库连接失败:")
                    print(f"  新版API错误: {e1}")
                    print(f"  旧版API错误: {e2}")
                    return False
    except Exception as e:
        print(f"❌ 应用上下文错误: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始导出AI评估系统配置数据（全量模式）...")
    print("=" * 60)
    print("⚠️  注意：此脚本将导出所有配置数据用于全量同步")
    print("⚠️  导入时将完全替换目标环境的配置数据")
    print("=" * 60)
    
    # 检查数据库连接
    if not test_database_connection():
        print("💡 请确保数据库文件存在并且应用配置正确")
        return False
    
    # 导出数据
    success = save_config_data()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 下一步操作：")
        print("1. 检查导出的配置数据是否正确")
        print("2. 将 config_data/ 目录提交到Git版本控制")
        print("3. 团队成员使用 import_config_data.py --full-replace 导入")
        print("4. 全量同步将确保团队间配置完全一致")
        print("\n💡 推荐工作流程：")
        print("  git add backend/config_data/")
        print("  git commit -m 'feat: 更新配置数据（全量）'")
        print("  git push")
        return True
    else:
        print("\n❌ 配置数据导出失败！")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 