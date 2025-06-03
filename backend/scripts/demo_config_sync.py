#!/usr/bin/env python3
"""
配置同步演示脚本
演示全量同步vs增量同步的区别
"""

import json
import subprocess
import os

def demo_config_changes():
    """演示配置变更场景"""
    print("🎯 配置同步演示：全量同步 vs 增量同步")
    print("=" * 60)
    
    # 1. 读取原始配置
    with open('config_data/classification_standards.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"📊 原始配置: {original_data['count']} 条分类标准")
    
    # 2. 创建变更后的配置（删除了一些配置项）
    demo_data = original_data.copy()
    demo_data['data'] = demo_data['data'][:10]  # 只保留前10条
    demo_data['count'] = 10
    demo_data['description'] = '演示配置变更 - 模拟删除了部分配置标准'
    demo_data['export_time'] = '2025-06-03T10:30:00'
    
    # 保存演示配置
    os.makedirs('demo_config', exist_ok=True)
    with open('demo_config/classification_standards.json', 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    # 复制评估标准（保持不变）  
    with open('config_data/evaluation_standards.json', 'r', encoding='utf-8') as f:
        eval_data = json.load(f)
    with open('demo_config/evaluation_standards.json', 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, ensure_ascii=False, indent=2)
    
    print(f"📉 变更后配置: {demo_data['count']} 条分类标准 (删除了 {original_data['count'] - demo_data['count']} 条)")
    print("📁 演示配置已保存到 demo_config/ 目录")
    
    print("\n🔍 现在我们来比较两种同步方式的区别:")
    print("1️⃣  增量导入: 不会删除现有的9条配置项")
    print("2️⃣  全量替换: 会删除多余的9条配置项，确保完全一致")
    
    return True

if __name__ == '__main__':
    demo_config_changes() 