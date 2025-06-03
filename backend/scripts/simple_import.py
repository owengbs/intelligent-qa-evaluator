#!/usr/bin/env python3
"""
简化版配置数据导入脚本
直接操作SQLite数据库，导入配置数据，适用于环境兼容性问题的情况
"""

import os
import json
import sqlite3
from datetime import datetime


def connect_database():
    """连接SQLite数据库"""
    db_path = '../data/qa_evaluator.db'
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


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


def import_classification_standards(conn, data_list, force_update=False):
    """导入分类标准数据"""
    try:
        cursor = conn.cursor()
        imported_count = 0
        updated_count = 0
        
        for item in data_list:
            # 检查是否已存在相同的标准
            cursor.execute("""
                SELECT id FROM classification_standards 
                WHERE level1=? AND level2=? AND level3=?
            """, (item.get('level1'), item.get('level2'), item.get('level3')))
            
            existing = cursor.fetchone()
            
            if existing:
                if force_update:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE classification_standards 
                        SET level1_definition=?, level3_definition=?, examples=?, 
                            is_default=?, updated_at=?
                        WHERE id=?
                    """, (
                        item.get('level1_definition'),
                        item.get('level3_definition'),
                        item.get('examples'),
                        item.get('is_default', False),
                        datetime.utcnow().isoformat(),
                        existing[0]
                    ))
                    updated_count += 1
                else:
                    print(f"⚠️  跳过已存在的分类标准: {item.get('level1')}-{item.get('level2')}-{item.get('level3')}")
                    continue
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO classification_standards 
                    (level1, level1_definition, level2, level3, level3_definition, 
                     examples, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('level1'),
                    item.get('level1_definition'),
                    item.get('level2'),
                    item.get('level3'),
                    item.get('level3_definition'),
                    item.get('examples'),
                    item.get('is_default', False),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                imported_count += 1
        
        conn.commit()
        print(f"✅ 分类标准导入完成: {imported_count} 新增, {updated_count} 更新")
        return True
        
    except Exception as e:
        print(f"❌ 导入分类标准失败: {e}")
        conn.rollback()
        return False


def import_evaluation_standards(conn, data_list, force_update=False):
    """导入评估标准数据"""
    try:
        cursor = conn.cursor()
        imported_count = 0
        updated_count = 0
        
        for item in data_list:
            # 检查是否已存在相同的标准
            cursor.execute("""
                SELECT id FROM evaluation_standards 
                WHERE level2_category=? AND dimension=?
            """, (item.get('level2_category'), item.get('dimension')))
            
            existing = cursor.fetchone()
            
            if existing:
                if force_update:
                    # 更新现有记录
                    cursor.execute("""
                        UPDATE evaluation_standards 
                        SET reference_standard=?, scoring_principle=?, max_score=?, 
                            is_default=?, updated_at=?
                        WHERE id=?
                    """, (
                        item.get('reference_standard'),
                        item.get('scoring_principle'),
                        item.get('max_score', 5),
                        item.get('is_default', False),
                        datetime.utcnow().isoformat(),
                        existing[0]
                    ))
                    updated_count += 1
                else:
                    print(f"⚠️  跳过已存在的评估标准: {item.get('level2_category')}-{item.get('dimension')}")
                    continue
            else:
                # 创建新记录
                cursor.execute("""
                    INSERT INTO evaluation_standards 
                    (level2_category, dimension, reference_standard, scoring_principle, 
                     max_score, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('level2_category'),
                    item.get('dimension'),
                    item.get('reference_standard'),
                    item.get('scoring_principle'),
                    item.get('max_score', 5),
                    item.get('is_default', False),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                ))
                imported_count += 1
        
        conn.commit()
        print(f"✅ 评估标准导入完成: {imported_count} 新增, {updated_count} 更新")
        return True
        
    except Exception as e:
        print(f"❌ 导入评估标准失败: {e}")
        conn.rollback()
        return False


def import_config_data(config_dir='config_data', force_update=False):
    """从配置目录导入所有数据"""
    print(f"📁 从目录导入配置数据: {config_dir}")
    
    if not os.path.exists(config_dir):
        print(f"❌ 配置目录不存在: {config_dir}")
        return False
    
    # 连接数据库
    conn = connect_database()
    if not conn:
        return False
    
    try:
        success = True
        
        # 导入分类标准
        classification_file = os.path.join(config_dir, 'classification_standards.json')
        if os.path.exists(classification_file):
            print("\n📋 导入分类标准数据...")
            classification_config = load_config_file(classification_file)
            if classification_config and 'data' in classification_config:
                result = import_classification_standards(
                    conn, 
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
                    conn, 
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
        
    except Exception as e:
        print(f"❌ 导入过程发生错误: {e}")
        return False
    
    finally:
        conn.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='简化版配置数据导入脚本')
    parser.add_argument('--config-dir', default='config_data', 
                       help='配置数据目录 (默认: config_data)')
    parser.add_argument('--force-update', action='store_true',
                       help='强制更新已存在的配置数据')
    
    args = parser.parse_args()
    
    print("🚀 开始导入AI评估系统配置数据（简化版）...")
    print("=" * 50)
    print(f"📁 配置目录: {args.config_dir}")
    print(f"🔄 强制更新: {'是' if args.force_update else '否'}")
    print("=" * 50)
    
    # 导入数据
    success = import_config_data(args.config_dir, args.force_update)
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 配置数据导入完成！")
        print("💡 团队配置已同步到本地数据库")
        print("💡 如果应用正在运行，请重启以加载新配置")
    else:
        print("\n❌ 配置数据导入失败！")
        print("💡 可以尝试使用标准版导入脚本: import_config_data.py")
    
    return success


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1) 