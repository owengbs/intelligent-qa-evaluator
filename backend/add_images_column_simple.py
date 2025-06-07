#!/usr/bin/env python3
"""
简单的数据库迁移脚本 - 添加图片字段
"""

import os
import sqlite3

def add_images_column():
    """为evaluation_history表添加uploaded_images_json字段"""
    # 获取数据库路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database/qa_evaluation.db')
    
    print(f"🔄 数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在！")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(evaluation_history)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'uploaded_images_json' in columns:
            print("ℹ️  uploaded_images_json 字段已存在，无需重复添加")
            conn.close()
            return True
        
        # 添加新字段
        cursor.execute("""
            ALTER TABLE evaluation_history 
            ADD COLUMN uploaded_images_json TEXT
        """)
        
        conn.commit()
        print("✅ 成功添加 uploaded_images_json 字段到 evaluation_history 表")
        
        # 验证字段已添加
        cursor.execute("PRAGMA table_info(evaluation_history)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'uploaded_images_json' in columns:
            print("✅ 字段添加验证成功")
        else:
            print("❌ 字段添加验证失败")
            return False
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔄 开始为evaluation_history表添加图片字段...")
    if add_images_column():
        print("🎉 数据库更新完成！")
    else:
        print("💥 数据库更新失败！") 