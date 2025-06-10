#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除"事实检索"分类人工评估中的"内容完整性"和"投资建议合规性"维度
"""

import sqlite3
import json
import os
from datetime import datetime
import shutil

def backup_database(db_path):
    """备份数据库"""
    backup_path = f"{db_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None

def preview_records(db_path):
    """预览将要更新的记录"""
    print("🔍 正在预览将要更新的记录...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询"事实检索"分类的记录
    cursor.execute("""
        SELECT id, user_input, human_dimensions_json, human_total_score, updated_at
        FROM evaluation_history 
        WHERE classification_level2 = '事实检索'
        AND human_dimensions_json IS NOT NULL 
        AND human_dimensions_json != ''
        ORDER BY id
    """)
    
    records = cursor.fetchall()
    conn.close()
    
    if not records:
        print("📭 没有找到需要更新的记录")
        return []
    
    print(f"📊 找到 {len(records)} 条需要更新的记录:")
    print("-" * 100)
    
    updated_records = []
    
    for record in records:
        record_id, user_input, human_dimensions_json, human_total_score, updated_at = record
        
        try:
            human_dimensions = json.loads(human_dimensions_json)
            
            # 检查是否包含目标维度
            has_completeness = '内容完整性' in human_dimensions
            has_compliance = '投资建议合规性' in human_dimensions
            
            if has_completeness or has_compliance:
                print(f"ID: {record_id}")
                print(f"问题: {user_input[:50]}...")
                print(f"当前人工评估维度: {list(human_dimensions.keys())}")
                print(f"人工总分: {human_total_score}")
                print(f"更新时间: {updated_at}")
                
                # 准备更新后的维度
                new_dimensions = {k: v for k, v in human_dimensions.items() 
                                if k not in ['内容完整性', '投资建议合规性']}
                
                print(f"更新后维度: {list(new_dimensions.keys())}")
                
                # 重新计算总分 (移除被删除维度的分数)
                removed_score = 0
                if has_completeness:
                    removed_score += human_dimensions.get('内容完整性', 0)
                if has_compliance:
                    removed_score += human_dimensions.get('投资建议合规性', 0)
                
                new_total_score = max(0, (human_total_score or 0) - removed_score)
                print(f"移除的分数: {removed_score}, 新总分: {new_total_score}")
                
                updated_records.append({
                    'id': record_id,
                    'old_dimensions': human_dimensions,
                    'new_dimensions': new_dimensions,
                    'old_total_score': human_total_score,
                    'new_total_score': new_total_score,
                    'removed_score': removed_score
                })
                print("-" * 100)
            
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠️  记录 {record_id} 的维度数据解析失败: {e}")
    
    print(f"\n📈 汇总信息:")
    print(f"  - 总记录数: {len(records)}")
    print(f"  - 需要更新的记录数: {len(updated_records)}")
    
    return updated_records

def update_records(db_path, updated_records, dry_run=False):
    """更新记录"""
    if not updated_records:
        print("📭 没有需要更新的记录")
        return
    
    mode = "预演模式" if dry_run else "实际更新"
    print(f"\n🔄 开始{mode}...")
    
    if dry_run:
        print("ℹ️  这是预演模式，不会实际修改数据库")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    updated_count = 0
    
    try:
        for record in updated_records:
            record_id = record['id']
            new_dimensions_json = json.dumps(record['new_dimensions'], ensure_ascii=False)
            new_total_score = record['new_total_score']
            
            # 更新记录
            cursor.execute("""
                UPDATE evaluation_history 
                SET human_dimensions_json = ?, 
                    human_total_score = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_dimensions_json, new_total_score, datetime.now().isoformat(), record_id))
            
            updated_count += 1
            print(f"✅ 已更新记录 {record_id}")
        
        conn.commit()
        print(f"\n🎉 成功更新了 {updated_count} 条记录")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 更新过程中出错: {e}")
        raise
    finally:
        conn.close()

def verify_updates(db_path):
    """验证更新结果"""
    print("\n🔍 验证更新结果...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否还有包含目标维度的记录
    cursor.execute("""
        SELECT COUNT(*) as total_records,
               COUNT(CASE WHEN human_dimensions_json LIKE '%内容完整性%' THEN 1 END) as has_completeness,
               COUNT(CASE WHEN human_dimensions_json LIKE '%投资建议合规性%' THEN 1 END) as has_compliance
        FROM evaluation_history 
        WHERE classification_level2 = '事实检索'
        AND human_dimensions_json IS NOT NULL 
        AND human_dimensions_json != ''
    """)
    
    result = cursor.fetchone()
    total_records, has_completeness, has_compliance = result
    
    print(f"📊 验证结果:")
    print(f"  - 总记录数: {total_records}")
    print(f"  - 仍包含'内容完整性'的记录: {has_completeness}")
    print(f"  - 仍包含'投资建议合规性'的记录: {has_compliance}")
    
    if has_completeness == 0 and has_compliance == 0:
        print("✅ 验证通过！所有目标维度都已成功移除")
    else:
        print("⚠️  仍有记录包含目标维度，可能需要进一步检查")
    
    # 显示更新后的示例记录
    cursor.execute("""
        SELECT id, human_dimensions_json, human_total_score
        FROM evaluation_history 
        WHERE classification_level2 = '事实检索'
        AND human_dimensions_json IS NOT NULL 
        AND human_dimensions_json != ''
        ORDER BY id LIMIT 3
    """)
    
    sample_records = cursor.fetchall()
    if sample_records:
        print(f"\n📋 更新后的示例记录:")
        for record in sample_records:
            record_id, human_dimensions_json, human_total_score = record
            try:
                dimensions = json.loads(human_dimensions_json)
                print(f"  ID {record_id}: 维度={list(dimensions.keys())}, 总分={human_total_score}")
            except:
                print(f"  ID {record_id}: 维度解析失败")
    
    conn.close()

def main():
    """主函数"""
    print("🧹 清除\"事实检索\"分类人工评估中的\"内容完整性\"和\"投资建议合规性\"维度")
    print("=" * 80)
    
    db_path = "database/qa_evaluation.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    # 1. 预览记录
    updated_records = preview_records(db_path)
    
    if not updated_records:
        print("✅ 所有记录都已经是正确的，无需更新")
        return
    
    # 2. 确认是否继续
    print(f"\n❓ 发现 {len(updated_records)} 条记录需要更新，是否继续？")
    print("   输入 'preview' 查看预演模式")
    print("   输入 'yes' 开始实际更新")
    print("   输入其他任何内容取消操作")
    
    choice = input("请选择: ").strip().lower()
    
    if choice == 'preview':
        # 预演模式
        update_records(db_path, updated_records, dry_run=True)
        print("\n预演完成。如需实际更新，请重新运行并选择 'yes'")
        
    elif choice == 'yes':
        # 3. 备份数据库
        backup_path = backup_database(db_path)
        if not backup_path:
            print("❌ 备份失败，取消更新操作")
            return
        
        # 4. 执行更新
        try:
            update_records(db_path, updated_records, dry_run=False)
            
            # 5. 验证结果
            verify_updates(db_path)
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            print(f"💡 可以从备份恢复: {backup_path}")
            
    else:
        print("❌ 操作已取消")

if __name__ == "__main__":
    main() 