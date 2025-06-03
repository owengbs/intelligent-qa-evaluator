#!/usr/bin/env python3
"""
清理修复脚本，避免路由冲突
移除可能导致 save_evaluation_history 函数重复定义的文件
"""

import os
import shutil

def cleanup_fix_scripts():
    """清理修复脚本"""
    print("🧹 清理可能导致路由冲突的修复脚本...")
    
    # 需要清理的文件列表
    files_to_remove = [
        'fix_remote_evaluation_issues.py',
        'fix_remote_issues.py',
        'quick_fix_405.py'
    ]
    
    backup_dir = 'backup_fix_scripts'
    
    # 创建备份目录
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"📁 创建备份目录: {backup_dir}")
    
    removed_count = 0
    
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                # 备份文件
                backup_path = os.path.join(backup_dir, filename)
                shutil.copy2(filename, backup_path)
                print(f"📋 备份文件: {filename} -> {backup_path}")
                
                # 删除原文件
                os.remove(filename)
                print(f"🗑️  删除文件: {filename}")
                
                removed_count += 1
                
            except Exception as e:
                print(f"❌ 处理文件 {filename} 时出错: {e}")
        else:
            print(f"ℹ️  文件不存在: {filename}")
    
    print(f"\n✅ 清理完成！共处理 {removed_count} 个文件")
    print(f"📁 备份位置: {backup_dir}")
    
    return removed_count > 0

def verify_app_routes():
    """验证 app.py 的路由配置"""
    print("\n🔍 验证路由配置...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查评估历史相关路由
        routes = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if "'/api/evaluation-history'" in line and "@app.route" in line:
                # 获取下一行的函数定义
                if i < len(lines):
                    func_line = lines[i]
                    if func_line.startswith('def '):
                        func_name = func_line.split('(')[0].replace('def ', '').strip()
                        routes.append((i, line.strip(), func_name))
        
        print(f"📊 找到 {len(routes)} 个评估历史路由:")
        for line_num, route, func_name in routes:
            print(f"  第{line_num}行: {route}")
            print(f"    函数: {func_name}")
        
        # 检查是否有重复的函数名
        func_names = [func_name for _, _, func_name in routes]
        duplicates = set([name for name in func_names if func_names.count(name) > 1])
        
        if duplicates:
            print(f"⚠️  发现重复函数名: {duplicates}")
            return False
        else:
            print("✅ 没有发现重复函数名")
            return True
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 Flask 路由冲突清理工具")
    print("=" * 50)
    
    # 1. 清理修复脚本
    cleanup_success = cleanup_fix_scripts()
    
    # 2. 验证路由配置
    routes_ok = verify_app_routes()
    
    print("\n" + "=" * 50)
    
    if cleanup_success and routes_ok:
        print("🎉 清理完成！")
        print("\n📋 接下来的步骤:")
        print("1. 重启 Flask 应用")
        print("2. 测试 POST /api/evaluation-history 接口")
        print("3. 确认不再有路由冲突错误")
    else:
        print("⚠️  请检查上述问题后再重启应用")

if __name__ == '__main__':
    main() 