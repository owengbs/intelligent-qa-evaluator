#!/usr/bin/env python3
"""
简化版配置数据导出脚本
直接连接SQLite数据库，导出配置数据为JSON文件
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
        conn.row_factory = sqlite3.Row  # 返回字典格式的行
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


def export_classification_standards(conn):
    """导出分类标准数据"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT level1, level1_definition, level2, level3, 
                   level3_definition, examples, is_default
            FROM classification_standards
            ORDER BY level1, level2, level3
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'level1': row['level1'],
                'level1_definition': row['level1_definition'],
                'level2': row['level2'], 
                'level3': row['level3'],
                'level3_definition': row['level3_definition'],
                'examples': row['examples'],
                'is_default': bool(row['is_default'])
            })
        
        return data
    except Exception as e:
        print(f"❌ 导出分类标准失败: {e}")
        return []


def export_evaluation_standards(conn):
    """导出评估标准数据"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT level2_category, dimension, reference_standard,
                   scoring_principle, max_score, is_default
            FROM evaluation_standards
            ORDER BY level2_category, dimension
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'level2_category': row['level2_category'],
                'dimension': row['dimension'],
                'reference_standard': row['reference_standard'],
                'scoring_principle': row['scoring_principle'],
                'max_score': row['max_score'],
                'is_default': bool(row['is_default'])
            })
        
        return data
    except Exception as e:
        print(f"❌ 导出评估标准失败: {e}")
        return []


def save_config_data(classification_data, evaluation_data, output_dir='config_data'):
    """保存配置数据到JSON文件"""
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存分类标准
    classification_file = os.path.join(output_dir, 'classification_standards.json')
    with open(classification_file, 'w', encoding='utf-8') as f:
        json.dump({
            'export_time': datetime.now().isoformat(),
            'description': '分类标准配置数据 - 用于团队同步',
            'count': len(classification_data),
            'data': classification_data
        }, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 分类标准已导出: {classification_file} ({len(classification_data)} 条记录)")
    
    # 保存评估标准
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
    return True


def main():
    """主函数"""
    print("🚀 开始导出AI评估系统配置数据...")
    print("=" * 50)
    
    # 连接数据库
    conn = connect_database()
    if not conn:
        return False
    
    try:
        # 导出数据
        print("📋 导出分类标准数据...")
        classification_data = export_classification_standards(conn)
        
        print("📊 导出评估标准数据...")
        evaluation_data = export_evaluation_standards(conn)
        
        # 保存到文件
        success = save_config_data(classification_data, evaluation_data)
        
        if success:
            print(f"\n🎉 配置数据导出完成！")
            print(f"📁 输出目录: {os.path.abspath('config_data')}")
            print(f"📊 总计: {len(classification_data) + len(evaluation_data)} 条配置记录")
            print("\n" + "=" * 50)
            print("🎯 下一步操作：")
            print("1. 将 config_data/ 目录添加到Git版本控制")
            print("2. 团队成员可使用 import_config_data.py 导入配置")
            print("3. 配置数据将在团队间保持同步")
            return True
        
    except Exception as e:
        print(f"❌ 导出过程发生错误: {e}")
        return False
    
    finally:
        conn.close()
    
    return False


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1) 