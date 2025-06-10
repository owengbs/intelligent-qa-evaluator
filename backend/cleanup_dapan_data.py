#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def cleanup_dapan_data():
    """删除数据库中大盘行业分析和宏观经济分析的记录"""
    conn = sqlite3.connect('database/qa_evaluation.db')
    cursor = conn.cursor()
    
    # 获取删除前的统计
    print("删除前统计:")
    cursor.execute("SELECT COUNT(*) FROM evaluation_history")
    total_before = cursor.fetchone()[0]
    print(f"  总记录数: {total_before}")
    
    cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE classification_level1 = '大盘行业分析'")
    dapan_before = cursor.fetchone()[0]
    print(f"  大盘行业分析记录: {dapan_before}")
    
    cursor.execute("SELECT COUNT(*) FROM evaluation_history WHERE classification_level2 = '宏观经济分析'")
    hongkuan_before = cursor.fetchone()[0]
    print(f"  宏观经济分析记录: {hongkuan_before}")
    
    # 执行删除操作
    try:
        # 删除大盘行业分析的所有记录
        cursor.execute("DELETE FROM evaluation_history WHERE classification_level1 = '大盘行业分析'")
        deleted_dapan = cursor.rowcount
        
        # 删除可能的宏观经济分析记录
        cursor.execute("DELETE FROM evaluation_history WHERE classification_level2 = '宏观经济分析'")
        deleted_hongkuan = cursor.rowcount
        
        conn.commit()
        print(f"\n删除操作完成:")
        print(f"  删除大盘行业分析记录: {deleted_dapan} 条")
        print(f"  删除宏观经济分析记录: {deleted_hongkuan} 条")
        
        # 获取删除后的统计
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        total_after = cursor.fetchone()[0]
        print(f"\n删除后统计:")
        print(f"  总记录数: {total_after}")
        print(f"  实际删除: {total_before - total_after} 条记录")
        
        return True
        
    except Exception as e:
        print(f"删除操作失败: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始清理大盘行业分析和宏观经济分析数据...")
    if cleanup_dapan_data():
        print("\n✅ 数据清理完成！")
    else:
        print("\n❌ 数据清理失败！") 