#!/usr/bin/env python3
"""
添加图片字段到evaluation_history表的迁移脚本
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import get_config

def add_images_column():
    """为evaluation_history表添加uploaded_images_json字段"""
    try:
        # 获取配置并创建数据库连接
        config = get_config()
        engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        
        # 添加新列的SQL
        sql = """
        ALTER TABLE evaluation_history 
        ADD COLUMN uploaded_images_json TEXT COMMENT '上传的图片信息(JSON格式)';
        """
        
        # 执行SQL
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
            print("✅ 成功添加 uploaded_images_json 字段到 evaluation_history 表")
            
    except Exception as e:
        # 如果字段已存在，会报错，但这是正常的
        if "Duplicate column name" in str(e) or "already exists" in str(e):
            print("ℹ️  uploaded_images_json 字段已存在，无需重复添加")
        else:
            print(f"❌ 添加字段时出错: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔄 开始为evaluation_history表添加图片字段...")
    if add_images_column():
        print("🎉 数据库更新完成！")
        sys.exit(0)
    else:
        print("💥 数据库更新失败！")
        sys.exit(1) 