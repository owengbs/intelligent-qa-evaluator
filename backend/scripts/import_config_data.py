#!/usr/bin/env python3
"""
配置数据导入脚本 - 支持全量替换
从JSON文件导入分类标准和评估标准数据到数据库
支持增量导入和全量替换两种模式，确保团队间配置一致性
"""

import os
import json
import sys
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.classification import db, ClassificationStandard, EvaluationStandard


def test_database_connection():
    """测试数据库连接"""
    try:
        from sqlalchemy import text
        
        with app.app_context():
            # 兼容SQLAlchemy 2.0+
            try:
                # 新版SQLAlchemy方式
                with db.engine.connect() as connection:
                    result = connection.execute(text('SELECT 1'))
                    result.fetchone()
            except AttributeError:
                # 旧版SQLAlchemy方式（备选）
                result = db.engine.execute('SELECT 1')
                result.fetchone()
            return True
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {str(e)}")
        return False


def backup_existing_data():
    """备份现有配置数据"""
    try:
        with app.app_context():
            # 备份分类标准
            classification_standards = ClassificationStandard.query.all()
            evaluation_standards = EvaluationStandard.query.all()
            
            backup_data = {
                'backup_time': datetime.now().isoformat(),
                'classification_standards': [std.to_dict() for std in classification_standards],
                'evaluation_standards': [std.to_dict() for std in evaluation_standards],
                'count': len(classification_standards) + len(evaluation_standards)
            }
            
            # 保存备份文件
            backup_file = f"config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 配置数据已备份到: {backup_file}")
            return backup_file
    except Exception as e:
        print(f"⚠️  备份失败: {e}")
        return None


def clear_existing_config_data():
    """清除现有配置数据（仅配置数据，不影响用户评估历史）"""
    try:
        with app.app_context():
            # 清除所有分类标准
            classification_count = ClassificationStandard.query.count()
            ClassificationStandard.query.delete()
            
            # 清除所有评估标准
            evaluation_count = EvaluationStandard.query.count()
            EvaluationStandard.query.delete()
            
            # 提交清除操作
            db.session.commit()
            
            print(f"🧹 已清除现有配置数据:")
            print(f"  - 分类标准: {classification_count} 条")
            print(f"  - 评估标准: {evaluation_count} 条")
            
            return True
    except Exception as e:
        print(f"❌ 清除配置数据失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False


def import_classification_standards(data, full_replace=False):
    """导入分类标准数据"""
    if not data:
        print("⚠️  没有分类标准数据需要导入")
        return 0
    
    try:
        with app.app_context():
            imported_count = 0
            skipped_count = 0
            
            for item in data:
                # 检查是否已存在
                existing = ClassificationStandard.query.filter_by(
                    level1=item.get('level1'),
                    level2=item.get('level2'),
                    level3=item.get('level3')
                ).first()
                
                if existing and not full_replace:
                    print(f"⏭️  跳过已存在的分类标准: {item.get('level1')} > {item.get('level2')} > {item.get('level3')}")
                    skipped_count += 1
                    continue
                
                # 创建新的分类标准实例
                standard = ClassificationStandard(
                    level1=item.get('level1'),
                    level1_definition=item.get('level1_definition'),
                    level2=item.get('level2'),
                    level3=item.get('level3'),
                    level3_definition=item.get('level3_definition'),
                    examples=item.get('examples'),
                    is_default=item.get('is_default', True)
                )
                
                db.session.add(standard)
                imported_count += 1
                print(f"✅ 导入分类标准: {item.get('level1')} > {item.get('level2')} > {item.get('level3')}")
            
            db.session.commit()
            print(f"📋 分类标准导入完成: {imported_count} 条新增, {skipped_count} 条跳过")
            return imported_count
            
    except Exception as e:
        print(f"❌ 导入分类标准失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return 0


def import_evaluation_standards(data, full_replace=False):
    """导入评估标准数据"""
    if not data:
        print("⚠️  没有评估标准数据需要导入")
        return 0
    
    try:
        with app.app_context():
            imported_count = 0
            skipped_count = 0
            
            for item in data:
                # 检查是否已存在
                existing = EvaluationStandard.query.filter_by(
                    level2_category=item.get('level2_category'),
                    dimension=item.get('dimension')
                ).first()
                
                if existing and not full_replace:
                    print(f"⏭️  跳过已存在的评估标准: {item.get('level2_category')} - {item.get('dimension')}")
                    skipped_count += 1
                    continue
                
                # 创建新的评估标准实例
                standard = EvaluationStandard(
                    level2_category=item.get('level2_category'),
                    dimension=item.get('dimension'),
                    reference_standard=item.get('reference_standard'),
                    scoring_principle=item.get('scoring_principle'),
                    max_score=item.get('max_score'),
                    is_default=item.get('is_default', True)
                )
                
                db.session.add(standard)
                imported_count += 1
                print(f"✅ 导入评估标准: {item.get('level2_category')} - {item.get('dimension')}")
            
            db.session.commit()
            print(f"📊 评估标准导入完成: {imported_count} 条新增, {skipped_count} 条跳过")
            return imported_count
            
    except Exception as e:
        print(f"❌ 导入评估标准失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return 0


def load_config_file(file_path):
    """加载配置文件"""
    try:
        if not os.path.exists(file_path):
            print(f"⚠️  配置文件不存在: {file_path}")
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"📁 加载配置文件: {file_path}")
        print(f"   - 导出时间: {config.get('export_time', 'Unknown')}")
        print(f"   - 数据条数: {config.get('count', 0)}")
        print(f"   - 同步模式: {config.get('sync_mode', 'unknown')}")
        
        return config
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='配置数据导入脚本 - 支持增量和全量替换',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 增量导入（默认模式）
  python import_config_data.py
  
  # 全量替换导入
  python import_config_data.py --full-replace
  
  # 指定配置目录
  python import_config_data.py --config-dir ../config_data --full-replace
  
  # 跳过备份（不推荐）
  python import_config_data.py --full-replace --no-backup
        """
    )
    
    parser.add_argument(
        '--config-dir',
        default='../config_data',
        help='配置数据目录路径 (默认: ../config_data)'
    )
    
    parser.add_argument(
        '--full-replace',
        action='store_true',
        help='启用全量替换模式：清除现有配置数据并导入新配置'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='跳过备份步骤（不推荐，仅在确定安全时使用）'
    )
    
    args = parser.parse_args()
    
    # 显示操作模式
    print("🚀 AI评估系统配置数据导入工具")
    print("=" * 60)
    if args.full_replace:
        print("🔄 模式: 全量替换 - 将完全替换现有配置数据")
        print("⚠️  警告: 此操作将删除所有现有配置数据")
    else:
        print("📥 模式: 增量导入 - 只导入不存在的配置数据")
        print("💡 提示: 使用 --full-replace 启用全量替换模式")
    print("=" * 60)
    
    # 检查数据库连接
    if not test_database_connection():
        print("💡 请确保数据库文件存在并且应用配置正确")
        return False
    
    # 确定配置目录
    config_dir = os.path.abspath(args.config_dir)
    if not os.path.exists(config_dir):
        print(f"❌ 配置目录不存在: {config_dir}")
        print("💡 请先运行导出脚本生成配置数据")
        return False
    
    print(f"📁 配置数据目录: {config_dir}")
    
    # 全量替换模式需要备份
    if args.full_replace and not args.no_backup:
        print("\n📋 执行全量替换前备份现有配置...")
        backup_file = backup_existing_data()
        if not backup_file:
            print("❌ 备份失败，取消导入操作")
            return False
    
    # 加载配置文件
    classification_file = os.path.join(config_dir, 'classification_standards.json')
    evaluation_file = os.path.join(config_dir, 'evaluation_standards.json')
    
    classification_config = load_config_file(classification_file)
    evaluation_config = load_config_file(evaluation_file)
    
    if not classification_config and not evaluation_config:
        print("❌ 没有找到有效的配置文件")
        return False
    
    # 全量替换模式：清除现有数据
    if args.full_replace:
        print("\n🧹 清除现有配置数据...")
        if not clear_existing_config_data():
            print("❌ 清除现有配置失败，取消导入操作")
            return False
    
    # 导入配置数据
    print(f"\n📥 开始导入配置数据...")
    total_imported = 0
    
    if classification_config:
        count = import_classification_standards(
            classification_config.get('data', []), 
            args.full_replace
        )
        total_imported += count
    
    if evaluation_config:
        count = import_evaluation_standards(
            evaluation_config.get('data', []), 
            args.full_replace
        )
        total_imported += count
    
    # 显示结果
    print("\n" + "=" * 60)
    if total_imported > 0:
        print(f"🎉 配置数据导入成功！")
        print(f"📊 总计导入: {total_imported} 条配置记录")
        print(f"🔄 同步模式: {'全量替换' if args.full_replace else '增量导入'}")
        
        if args.full_replace:
            print("\n✅ 团队配置已完全同步")
            print("💡 所有团队成员现在拥有相同的配置数据")
        else:
            print("\n💡 增量导入完成")
            print("💡 如需完全同步，请使用 --full-replace 参数")
        
        return True
    else:
        print("⚠️  没有导入任何配置数据")
        if not args.full_replace:
            print("💡 可能所有配置都已存在，使用 --full-replace 强制更新")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 