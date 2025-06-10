#!/usr/bin/env python3
import sqlite3
import json
from datetime import datetime

def clear_ai_evaluations():
    """清零所有历史记录的AI评估结果"""
    
    database_path = 'database/qa_evaluation.db'
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        print("开始清零AI评估结果...")
        
        # 先查询当前的记录数量
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        total_records = cursor.fetchone()[0]
        print(f"数据库中共有 {total_records} 条记录")
        
        # 查询有AI评估结果的记录数量
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE total_score > 0 OR ai_is_badcase = 1")
        ai_evaluated_records = cursor.fetchone()[0]
        print(f"其中有 {ai_evaluated_records} 条记录包含AI评估结果")
        
        if ai_evaluated_records == 0:
            print("没有找到需要清零的AI评估记录")
            return
        
        # 确认操作
        print("\n即将执行以下操作:")
        print("1. 将所有记录的 total_score 设置为 0")
        print("2. 将所有记录的 ai_is_badcase 设置为 0 (否)")
        print("3. 清空所有记录的 dimensions_json 中的AI评分")
        print("4. 重新计算 is_badcase 状态（基于 human_is_badcase）")
        print("5. 清空 reasoning 和 badcase_reason（AI生成的内容）")
        
        confirm = input("\n确认执行以上操作吗？(输入 'YES' 确认): ")
        if confirm != 'YES':
            print("操作已取消")
            return
        
        print("\n开始执行清零操作...")
        
        # 1. 清零AI总分
        cursor.execute("""
            UPDATE evaluation_history 
            SET total_score = 0
        """)
        print("✓ 已清零所有AI总分")
        
        # 2. 清零AI badcase判断
        cursor.execute("""
            UPDATE evaluation_history 
            SET ai_is_badcase = 0
        """)
        print("✓ 已清零所有AI badcase判断")
        
        # 3. 清空AI生成的reasoning和badcase_reason
        cursor.execute("""
            UPDATE evaluation_history 
            SET reasoning = '',
                badcase_reason = CASE 
                    WHEN human_is_badcase = 1 AND human_reasoning IS NOT NULL AND human_reasoning != '' 
                    THEN human_reasoning 
                    ELSE NULL 
                END
        """)
        print("✓ 已清空AI生成的推理内容")
        
        # 4. 清零dimensions_json中的AI评分
        cursor.execute("SELECT id, dimensions_json FROM evaluation_history WHERE dimensions_json IS NOT NULL")
        records_to_update = cursor.fetchall()
        
        updated_count = 0
        for record_id, dimensions_json_str in records_to_update:
            try:
                if dimensions_json_str:
                    dimensions = json.loads(dimensions_json_str)
                    # 将所有维度评分设置为0
                    for key in dimensions:
                        dimensions[key] = 0.0
                    
                    new_dimensions_json = json.dumps(dimensions, ensure_ascii=False)
                    cursor.execute("""
                        UPDATE evaluation_history 
                        SET dimensions_json = ? 
                        WHERE id = ?
                    """, (new_dimensions_json, record_id))
                    updated_count += 1
            except json.JSONDecodeError:
                print(f"警告: 记录 {record_id} 的dimensions_json格式异常，跳过")
                continue
        
        print(f"✓ 已更新 {updated_count} 条记录的维度评分")
        
        # 5. 重新计算综合badcase状态（基于人工评估）
        cursor.execute("""
            UPDATE evaluation_history 
            SET is_badcase = CASE 
                WHEN human_is_badcase = 1 THEN 1 
                ELSE 0 
            END
        """)
        print("✓ 已重新计算综合badcase状态（基于人工评估）")
        
        # 6. 清零model_used等AI相关字段
        cursor.execute("""
            UPDATE evaluation_history 
            SET model_used = 'deepseek-chat',
                evaluation_time_seconds = 0.0,
                raw_response = ''
        """)
        print("✓ 已重置AI相关元数据")
        
        # 提交更改
        conn.commit()
        print("\n✅ 所有更改已提交到数据库")
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE total_score > 0")
        remaining_ai_scores = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE ai_is_badcase = 1")
        remaining_ai_badcases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE is_badcase = 1")
        total_badcases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE human_is_badcase = 1")
        human_badcases = cursor.fetchone()[0]
        
        print(f"\n📊 清零后的统计:")
        print(f"- 剩余AI评分 > 0的记录: {remaining_ai_scores} 条")
        print(f"- 剩余AI badcase: {remaining_ai_badcases} 条") 
        print(f"- 总badcase数量: {total_badcases} 条")
        print(f"- 人工badcase数量: {human_badcases} 条")
        
        if remaining_ai_scores == 0 and remaining_ai_badcases == 0:
            print("✅ AI评估结果已完全清零")
        else:
            print("⚠️  部分AI评估结果可能未完全清零")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def show_statistics():
    """显示当前数据库统计"""
    database_path = 'database/qa_evaluation.db'
    
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        print("当前数据库统计:")
        print("-" * 50)
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        total = cursor.fetchone()[0]
        print(f"总记录数: {total}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE total_score > 0")
        ai_scored = cursor.fetchone()[0]
        print(f"有AI评分的记录: {ai_scored}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE ai_is_badcase = 1")
        ai_badcase = cursor.fetchone()[0]
        print(f"AI判断的badcase: {ai_badcase}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE human_is_badcase = 1")
        human_badcase = cursor.fetchone()[0]
        print(f"人工标记的badcase: {human_badcase}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE is_badcase = 1")
        total_badcase = cursor.fetchone()[0]
        print(f"总badcase数量: {total_badcase}")
        
        # 按分类统计
        cursor.execute("""
            SELECT classification_level2, COUNT(*) 
            FROM evaluation_history 
            GROUP BY classification_level2 
            ORDER BY COUNT(*) DESC
        """)
        categories = cursor.fetchall()
        print(f"\n按分类统计:")
        for category, count in categories:
            print(f"  {category or '未分类'}: {count} 条")
        
        conn.close()
        
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")

def main():
    print("=" * 60)
    print("AI评估结果清零工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看当前数据库统计")
        print("2. 清零所有AI评估结果")
        print("3. 退出")
        
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == '1':
            show_statistics()
        elif choice == '2':
            clear_ai_evaluations()
        elif choice == '3':
            print("退出程序")
            break
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main() 