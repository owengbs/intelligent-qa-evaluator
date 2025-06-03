#!/usr/bin/env python3
"""
生产环境数据迁移脚本
专门处理生产环境中的数据库迁移问题
"""

import os
import sqlite3
import shutil
from datetime import datetime

# 设置生产环境
os.environ['APP_ENV'] = 'production'

def find_database_files():
    """查找可能的数据库文件"""
    print("🔍 搜索可能的数据库文件...")
    
    possible_paths = [
        './data/qa_evaluator.db',           # 旧数据库路径1
        './instance/qa_evaluator.db',      # 旧数据库路径2
        './qa_evaluator.db',               # 根目录
        '../data/qa_evaluator.db',         # 上级目录
        './database/qa_evaluation.db',     # 新数据库路径
        '/tmp/qa_evaluator_db/qa_evaluation.db',  # 临时目录
    ]
    
    found_files = []
    for path in possible_paths:
        if os.path.exists(path):
            size = os.path.getsize(path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            found_files.append({
                'path': path,
                'size': size,
                'modified': mtime,
                'size_mb': round(size / 1024 / 1024, 2)
            })
            print(f"  📁 发现: {path} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    return found_files

def check_database_content(db_path):
    """检查数据库内容"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查evaluation_history表
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        history_count = cursor.fetchone()[0]
        
        # 检查最新记录
        cursor.execute("SELECT created_at FROM evaluation_history ORDER BY created_at DESC LIMIT 1")
        latest = cursor.fetchone()
        latest_date = latest[0] if latest else "无记录"
        
        conn.close()
        
        return {
            'history_count': history_count,
            'latest_record': latest_date
        }
    except Exception as e:
        return {'error': str(e)}

def migrate_production_data():
    """执行生产环境数据迁移"""
    print("🌐 开始生产环境数据迁移...")
    
    # 查找数据库文件
    found_files = find_database_files()
    
    if not found_files:
        print("❌ 未找到任何数据库文件")
        return False
    
    # 分析每个数据库文件
    candidates = []
    for file_info in found_files:
        print(f"\n📊 分析 {file_info['path']}:")
        content = check_database_content(file_info['path'])
        
        if 'error' in content:
            print(f"  ❌ 无法读取: {content['error']}")
        else:
            print(f"  📈 历史记录: {content['history_count']} 条")
            print(f"  📅 最新记录: {content['latest_record']}")
            
            if content['history_count'] > 0:
                candidates.append({
                    'file': file_info,
                    'content': content
                })
    
    # 选择最佳的源数据库
    if not candidates:
        print("❌ 没有找到包含数据的数据库文件")
        return False
    
    # 按记录数量排序，选择最大的
    source = max(candidates, key=lambda x: x['content']['history_count'])
    source_path = source['file']['path']
    
    print(f"\n✅ 选择源数据库: {source_path}")
    print(f"   包含 {source['content']['history_count']} 条历史记录")
    
    # 确定目标数据库路径
    from config import config
    if hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
        target_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
    else:
        target_path = './database/qa_evaluation.db'
    
    print(f"🎯 目标数据库: {target_path}")
    
    # 确保目标目录存在
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    # 备份现有目标数据库（如果存在）
    if os.path.exists(target_path):
        backup_path = f"{target_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(target_path, backup_path)
        print(f"💾 备份现有数据库到: {backup_path}")
    
    # 执行迁移
    try:
        print("🔄 开始数据迁移...")
        
        # 如果源和目标是同一个文件，跳过迁移
        if os.path.abspath(source_path) == os.path.abspath(target_path):
            print("✅ 源数据库和目标数据库相同，无需迁移")
            return True
        
        # 复制数据库文件
        shutil.copy2(source_path, target_path)
        print(f"✅ 数据库文件复制完成")
        
        # 验证迁移结果
        target_content = check_database_content(target_path)
        if 'error' in target_content:
            print(f"❌ 迁移后验证失败: {target_content['error']}")
            return False
        
        print(f"✅ 迁移验证成功:")
        print(f"   - 历史记录: {target_content['history_count']} 条")
        print(f"   - 最新记录: {target_content['latest_record']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        return False

def setup_production_permissions():
    """设置生产环境文件权限"""
    print("🔐 设置生产环境权限...")
    
    try:
        from config import config
        if hasattr(config, 'SQLALCHEMY_DATABASE_URI'):
            db_path = config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            
            # 设置目录权限
            os.chmod(db_dir, 0o755)
            print(f"✅ 目录权限设置: {db_dir}")
            
            # 设置文件权限
            if os.path.exists(db_path):
                os.chmod(db_path, 0o644)
                print(f"✅ 文件权限设置: {db_path}")
            
        return True
    except Exception as e:
        print(f"⚠️  权限设置失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("🌐 生产环境数据迁移工具")
    print("="*60)
    
    # 打印环境信息
    try:
        from config import print_config_info
        print_config_info()
        print()
    except Exception as e:
        print(f"⚠️  配置信息获取失败: {str(e)}")
    
    # 执行迁移
    success = migrate_production_data()
    
    if success:
        print("\n🔐 设置权限...")
        setup_production_permissions()
        
        print("\n🎉 生产环境数据迁移完成!")
        print("💡 现在可以启动应用服务")
    else:
        print("\n❌ 数据迁移失败")
        print("💡 请检查错误信息并手动处理")
    
    print("\n" + "="*60) 