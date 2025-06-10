#!/usr/bin/env python3
"""
更新"事实检索"类型问题的维度评分
删除"内容完整性"和"投资建议合规性"这两个维度的评分
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

def connect_database():
    """连接数据库"""
    db_path = 'database/qa_evaluation.db'
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        print(f"✅ 成功连接数据库: {db_path}")
        return conn
    except Exception as e:
        print(f"❌ 连接数据库失败: {str(e)}")
        return None

def check_fact_retrieval_records(conn):
    """检查事实检索类型的记录"""
    try:
        cursor = conn.cursor()
        
        # 查询事实检索分类的记录
        cursor.execute("""
            SELECT id, classification_level2, dimensions_json, total_score, created_at
            FROM evaluation_history 
            WHERE classification_level2 = '事实检索' 
            OR classification_level2 LIKE '%事实%检索%'
            ORDER BY created_at DESC
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("📭 未找到事实检索类型的记录")
            
            # 查看所有可能相关的分类
            cursor.execute("""
                SELECT DISTINCT classification_level2, COUNT(*) as count
                FROM evaluation_history 
                WHERE classification_level2 LIKE '%事实%' 
                OR classification_level2 LIKE '%检索%'
                OR classification_level2 LIKE '%指标%'
                GROUP BY classification_level2
                ORDER BY count DESC
            """)
            
            similar_records = cursor.fetchall()
            if similar_records:
                print("🔍 找到类似的分类:")
                for cat, count in similar_records:
                    print(f"   - {cat}: {count}条记录")
            
            return []
        
        print(f"📊 找到 {len(records)} 条事实检索记录:")
        
        # 分析维度信息
        dimension_stats = {}
        for i, (record_id, classification, dimensions_json, total_score, created_at) in enumerate(records[:10]):
            print(f"\n📋 记录 #{record_id}:")
            print(f"   - 分类: {classification}")
            print(f"   - 总分: {total_score}")
            print(f"   - 创建时间: {created_at}")
            
            if dimensions_json:
                try:
                    dimensions = json.loads(dimensions_json)
                    print(f"   - 维度评分:")
                    for dim_key, dim_score in dimensions.items():
                        print(f"     * {dim_key}: {dim_score}")
                        dimension_stats[dim_key] = dimension_stats.get(dim_key, 0) + 1
                except json.JSONDecodeError:
                    print(f"   - 维度数据格式错误")
            else:
                print(f"   - 无维度数据")
        
        if len(records) > 10:
            print(f"\n... (还有 {len(records) - 10} 条记录)")
        
        # 统计维度使用情况
        if dimension_stats:
            print(f"\n📈 维度使用统计:")
            for dim_name, count in sorted(dimension_stats.items(), key=lambda x: x[1], reverse=True):
                print(f"   - {dim_name}: {count}次")
        
        return records
        
    except Exception as e:
        print(f"❌ 检查记录失败: {str(e)}")
        return []

def update_fact_retrieval_scores(conn, dry_run=True):
    """更新事实检索记录的维度评分"""
    try:
        cursor = conn.cursor()
        
        # 要删除的维度
        dimensions_to_remove = ['内容完整性', '投资建议合规性']
        
        # 查询需要更新的记录
        cursor.execute("""
            SELECT id, dimensions_json, total_score
            FROM evaluation_history 
            WHERE classification_level2 = '事实检索' 
            OR classification_level2 LIKE '%事实%检索%'
        """)
        
        records = cursor.fetchall()
        
        if not records:
            print("📭 没有需要更新的记录")
            return
        
        print(f"🔄 准备更新 {len(records)} 条记录")
        
        updated_count = 0
        skipped_count = 0
        
        for record_id, dimensions_json, current_total_score in records:
            if not dimensions_json:
                print(f"⏭️  跳过记录 #{record_id}: 无维度数据")
                skipped_count += 1
                continue
            
            try:
                dimensions = json.loads(dimensions_json)
                original_dimensions = dimensions.copy()
                
                # 检查是否包含要删除的维度
                has_target_dimensions = any(dim in dimensions for dim in dimensions_to_remove)
                
                if not has_target_dimensions:
                    print(f"⏭️  跳过记录 #{record_id}: 不包含目标维度")
                    skipped_count += 1
                    continue
                
                # 删除指定维度
                removed_dimensions = []
                for dim_name in dimensions_to_remove:
                    if dim_name in dimensions:
                        removed_score = dimensions.pop(dim_name)
                        removed_dimensions.append(f"{dim_name}({removed_score}分)")
                
                if not removed_dimensions:
                    print(f"⏭️  跳过记录 #{record_id}: 无需删除的维度")
                    skipped_count += 1
                    continue
                
                # 重新计算总分
                new_total_score = sum(dimensions.values()) if dimensions else 0.0
                
                print(f"🔧 更新记录 #{record_id}:")
                print(f"   - 删除维度: {', '.join(removed_dimensions)}")
                print(f"   - 原总分: {current_total_score} → 新总分: {new_total_score}")
                print(f"   - 剩余维度: {list(dimensions.keys())}")
                
                if not dry_run:
                    # 更新数据库
                    new_dimensions_json = json.dumps(dimensions, ensure_ascii=False)
                    cursor.execute("""
                        UPDATE evaluation_history 
                        SET dimensions_json = ?, total_score = ?, updated_at = ?
                        WHERE id = ?
                    """, (new_dimensions_json, new_total_score, datetime.utcnow(), record_id))
                    
                    print(f"✅ 记录 #{record_id} 更新完成")
                else:
                    print(f"🔍 [预览模式] 记录 #{record_id} 将被更新")
                
                updated_count += 1
                
            except json.JSONDecodeError as e:
                print(f"❌ 记录 #{record_id} JSON解析失败: {str(e)}")
                skipped_count += 1
                continue
        
        if not dry_run:
            conn.commit()
            print(f"\n✅ 批量更新完成!")
        else:
            print(f"\n🔍 预览模式完成!")
        
        print(f"📊 统计结果:")
        print(f"   - 更新记录数: {updated_count}")
        print(f"   - 跳过记录数: {skipped_count}")
        print(f"   - 总记录数: {len(records)}")
        
    except Exception as e:
        print(f"❌ 更新过程发生错误: {str(e)}")
        conn.rollback()

def backup_database():
    """备份数据库"""
    try:
        import shutil
        source = 'database/qa_evaluation.db'
        backup_name = f'database/qa_evaluation_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        
        shutil.copy2(source, backup_name)
        print(f"✅ 数据库已备份到: {backup_name}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔧 事实检索维度评分更新工具")
    print("=" * 50)
    
    # 连接数据库
    conn = connect_database()
    if not conn:
        return
    
    try:
        # 检查现有记录
        print("\n📋 第一步: 检查现有记录")
        records = check_fact_retrieval_records(conn)
        
        if not records:
            print("没有需要处理的记录")
            return
        
        # 询问是否继续
        print(f"\n❓ 发现 {len(records)} 条事实检索记录")
        print("将删除以下维度的评分:")
        print("   - 内容完整性")
        print("   - 投资建议合规性")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--execute':
            execute = True
            print("🚀 执行模式: 将直接进行更新")
        else:
            print("\n🔍 预览模式: 不会实际修改数据库")
            print("💡 如需实际执行，请使用: python update_fact_retrieval_scores.py --execute")
            execute = False
        
        # 如果是执行模式，先备份
        if execute:
            print("\n💾 第二步: 备份数据库")
            if not backup_database():
                print("❌ 备份失败，终止操作")
                return
        
        # 执行更新
        print(f"\n🔄 第三步: {'执行更新' if execute else '预览更新'}")
        update_fact_retrieval_scores(conn, dry_run=not execute)
        
    finally:
        conn.close()
        print("\n🔐 数据库连接已关闭")

if __name__ == '__main__':
    main() 