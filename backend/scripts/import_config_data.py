#!/usr/bin/env python3
"""
配置数据导入脚本
从JSON文件导入分类标准和评估标准数据，用于团队间同步配置
"""

import os
import json
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.classification import db, ClassificationStandard, EvaluationStandard


def load_config_file(filepath):
    """加载配置文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 文件不存在: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return None


def import_classification_standards(data_list, force_update=False):
    """导入分类标准数据"""
    try:
        with app.app_context():
            imported_count = 0
            updated_count = 0
            
            for item in data_list:
                # 检查是否已存在相同的标准
                existing = ClassificationStandard.query.filter_by(
                    level1=item.get('level1'),
                    level2=item.get('level2'),
                    level3=item.get('level3')
                ).first()
                
                if existing:
                    if force_update:
                        # 更新现有记录
                        existing.level1_definition = item.get('level1_definition')
                        existing.level3_definition = item.get('level3_definition')
                        existing.examples = item.get('examples')
                        existing.is_default = item.get('is_default', False)
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        print(f"⚠️  跳过已存在的分类标准: {item.get('level1')}-{item.get('level2')}-{item.get('level3')}")
                        continue
                else:
                    # 创建新记录 - 使用直接创建而不是from_dict方法
                    new_standard = ClassificationStandard(
                        level1=item.get('level1'),
                        level1_definition=item.get('level1_definition'),
                        level2=item.get('level2'),
                        level3=item.get('level3'),
                        level3_definition=item.get('level3_definition'),
                        examples=item.get('examples'),
                        is_default=item.get('is_default', False)
                    )
                    db.session.add(new_standard)
                    imported_count += 1
            
            db.session.commit()
            print(f"✅ 分类标准导入完成: {imported_count} 新增, {updated_count} 更新")
            return True
            
    except Exception as e:
        print(f"❌ 导入分类标准失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False


def import_evaluation_standards(data_list, force_update=False):
    """导入评估标准数据"""
    try:
        with app.app_context():
            imported_count = 0
            updated_count = 0
            
            for item in data_list:
                # 检查是否已存在相同的标准
                existing = EvaluationStandard.query.filter_by(
                    level2_category=item.get('level2_category'),
                    dimension=item.get('dimension')
                ).first()
                
                if existing:
                    if force_update:
                        # 更新现有记录
                        existing.reference_standard = item.get('reference_standard')
                        existing.scoring_principle = item.get('scoring_principle')
                        existing.max_score = item.get('max_score', 5)
                        existing.is_default = item.get('is_default', False)
                        existing.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        print(f"⚠️  跳过已存在的评估标准: {item.get('level2_category')}-{item.get('dimension')}")
                        continue
                else:
                    # 创建新记录 - 使用直接创建而不是from_dict方法
                    new_standard = EvaluationStandard(
                        level2_category=item.get('level2_category'),
                        dimension=item.get('dimension'),
                        reference_standard=item.get('reference_standard'),
                        scoring_principle=item.get('scoring_principle'),
                        max_score=item.get('max_score', 5),
                        is_default=item.get('is_default', False)
                    )
                    db.session.add(new_standard)
                    imported_count += 1
            
            db.session.commit()
            print(f"✅ 评估标准导入完成: {imported_count} 新增, {updated_count} 更新")
            return True
            
    except Exception as e:
        print(f"❌ 导入评估标准失败: {e}")
        try:
            db.session.rollback()
        except:
            pass
        return False


def import_config_data(config_dir='config_data', force_update=False):
    """从配置目录导入所有数据"""
    print(f"📁 从目录导入配置数据: {config_dir}")
    
    if not os.path.exists(config_dir):
        print(f"❌ 配置目录不存在: {config_dir}")
        return False
    
    success = True
    
    # 导入分类标准
    classification_file = os.path.join(config_dir, 'classification_standards.json')
    if os.path.exists(classification_file):
        print("\n📋 导入分类标准数据...")
        classification_config = load_config_file(classification_file)
        if classification_config and 'data' in classification_config:
            result = import_classification_standards(
                classification_config['data'], 
                force_update
            )
            success = success and result
        else:
            print("❌ 分类标准配置文件格式错误")
            success = False
    else:
        print(f"⚠️  分类标准文件不存在: {classification_file}")
    
    # 导入评估标准
    evaluation_file = os.path.join(config_dir, 'evaluation_standards.json')
    if os.path.exists(evaluation_file):
        print("\n📊 导入评估标准数据...")
        evaluation_config = load_config_file(evaluation_file)
        if evaluation_config and 'data' in evaluation_config:
            result = import_evaluation_standards(
                evaluation_config['data'], 
                force_update
            )
            success = success and result
        else:
            print("❌ 评估标准配置文件格式错误")
            success = False
    else:
        print(f"⚠️  评估标准文件不存在: {evaluation_file}")
    
    return success


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
    import argparse
    
    parser = argparse.ArgumentParser(description='导入AI评估系统配置数据')
    parser.add_argument('--config-dir', default='config_data', 
                       help='配置数据目录 (默认: config_data)')
    parser.add_argument('--force-update', action='store_true',
                       help='强制更新已存在的配置数据')
    
    args = parser.parse_args()
    
    print("🚀 开始导入AI评估系统配置数据...")
    print("=" * 50)
    print(f"📁 配置目录: {args.config_dir}")
    print(f"🔄 强制更新: {'是' if args.force_update else '否'}")
    print("=" * 50)
    
    # 检查数据库连接 - 使用兼容性测试
    if not test_database_connection():
        print("💡 请确保数据库文件存在并且应用配置正确")
        return False
    
    # 导入数据
    success = import_config_data(args.config_dir, args.force_update)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 配置数据导入完成！")
        print("💡 团队配置已同步到本地数据库")
    else:
        print("\n❌ 配置数据导入失败！")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 