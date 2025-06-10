#!/usr/bin/env python3
"""
实时监控AI总结相关的日志
专门用于查看智能分析功能的详细执行过程
"""

import os
import time
import re
from datetime import datetime

def watch_ai_summary_logs():
    """监控AI总结相关的日志"""
    
    # 可能的日志文件位置
    log_files = [
        'app.log',
        'production.log',
        'logs/app.log'
    ]
    
    # 找到存在的日志文件
    target_log_file = None
    for log_file in log_files:
        if os.path.exists(log_file):
            target_log_file = log_file
            break
    
    if not target_log_file:
        print("❌ 未找到日志文件")
        print("💡 请确保后端服务正在运行，或手动指定日志文件路径")
        return
    
    print(f"📋 监控日志文件: {target_log_file}")
    print(f"🔍 过滤关键词: [智能分析], AI总结, Prompt, 大模型")
    print("=" * 60)
    
    # AI总结相关的关键词
    ai_keywords = [
        '智能分析',
        'AI总结',
        'badcase-summary',
        'ai_summary_service',
        'Prompt',
        '大模型',
        'LLM',
        'deepseek',
        'summarize_badcase_reasons'
    ]
    
    try:
        # 获取文件当前大小
        with open(target_log_file, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # 移动到文件末尾
            
            print(f"⏰ 开始监控... (按 Ctrl+C 停止)")
            print()
            
            while True:
                line = f.readline()
                if line:
                    # 检查是否包含AI总结相关关键词
                    if any(keyword in line for keyword in ai_keywords):
                        # 添加颜色和时间戳
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        print(f"[{timestamp}] {line.rstrip()}")
                    
                else:
                    time.sleep(0.1)  # 短暂休眠，避免过度占用CPU
                    
    except FileNotFoundError:
        print(f"❌ 日志文件 {target_log_file} 不存在")
    except KeyboardInterrupt:
        print("\n⏹️  停止监控")
    except Exception as e:
        print(f"❌ 监控过程中发生错误: {str(e)}")

def show_recent_ai_logs(lines=50):
    """显示最近的AI总结相关日志"""
    log_files = ['app.log', 'production.log', 'logs/app.log']
    
    target_log_file = None
    for log_file in log_files:
        if os.path.exists(log_file):
            target_log_file = log_file
            break
    
    if not target_log_file:
        print("❌ 未找到日志文件")
        return
    
    ai_keywords = [
        '智能分析',
        'AI总结',
        'badcase-summary',
        'ai_summary_service',
        'Prompt',
        '大模型',
        'LLM',
        'deepseek',
        'summarize_badcase_reasons'
    ]
    
    try:
        with open(target_log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            
        # 过滤AI相关日志
        ai_lines = []
        for line in all_lines:
            if any(keyword in line for keyword in ai_keywords):
                ai_lines.append(line.rstrip())
        
        # 显示最近的几行
        recent_lines = ai_lines[-lines:] if len(ai_lines) > lines else ai_lines
        
        print(f"📋 最近的AI总结相关日志 (最多{lines}行):")
        print("=" * 60)
        
        if not recent_lines:
            print("📭 暂无AI总结相关日志")
        else:
            for line in recent_lines:
                print(line)
                
        print("=" * 60)
        print(f"📊 共找到 {len(recent_lines)} 条相关日志")
        
    except Exception as e:
        print(f"❌ 读取日志失败: {str(e)}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'recent':
        # 显示最近的日志
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        show_recent_ai_logs(lines)
    else:
        # 实时监控
        watch_ai_summary_logs() 