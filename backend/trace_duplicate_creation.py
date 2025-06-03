#!/usr/bin/env python3
"""
追踪重复记录创建的调试工具
实时监控API调用来找出重复记录的创建时机
"""

import json
import time
from datetime import datetime
from flask import Flask
from app import app
from models.classification import EvaluationHistory, db

def get_current_records():
    """获取当前所有记录的快照"""
    records = []
    with app.app_context():
        all_records = EvaluationHistory.query.order_by(EvaluationHistory.id.desc()).all()
        for record in all_records:
            records.append({
                'id': record.id,
                'user_input': record.user_input[:50] + "..." if len(record.user_input) > 50 else record.user_input,
                'is_human_modified': record.is_human_modified,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat() if record.updated_at else None
            })
    return records

def compare_records(before, after):
    """比较前后记录的差异"""
    before_ids = {r['id'] for r in before}
    after_ids = {r['id'] for r in after}
    
    new_records = [r for r in after if r['id'] not in before_ids]
    modified_records = []
    
    for after_record in after:
        if after_record['id'] in before_ids:
            before_record = next(r for r in before if r['id'] == after_record['id'])
            if after_record['updated_at'] != before_record['updated_at']:
                modified_records.append({
                    'id': after_record['id'],
                    'changes': {
                        'before': before_record,
                        'after': after_record
                    }
                })
    
    return new_records, modified_records

def find_duplicates(records):
    """查找可能的重复记录"""
    duplicates = []
    for i, record1 in enumerate(records):
        for j, record2 in enumerate(records[i+1:], i+1):
            # 简单的重复检测：相同的用户输入
            if record1['user_input'] == record2['user_input']:
                duplicates.append({
                    'record1': record1,
                    'record2': record2,
                    'time_diff_seconds': abs(
                        datetime.fromisoformat(record1['created_at'].replace('Z', '+00:00')).timestamp() -
                        datetime.fromisoformat(record2['created_at'].replace('Z', '+00:00')).timestamp()
                    )
                })
    return duplicates

def monitor_api_calls():
    """监控API调用（通过日志文件或实时监听）"""
    print("📡 开始监控API调用...")
    print("注意：此功能需要配合实际的API调用来使用")
    print("请在另一个终端进行评估操作，本工具会检测数据库变化")
    
    before_records = get_current_records()
    print(f"📊 当前记录数: {len(before_records)}")
    
    # 显示最近的几条记录
    if before_records:
        print("🔍 最近的记录:")
        for record in before_records[:5]:
            human_flag = "👨‍💼" if record['is_human_modified'] else "🤖"
            print(f"  ID {record['id']}: {human_flag} {record['user_input']}")
    
    print("\n⏳ 开始监控变化（每5秒检查一次，按Ctrl+C停止）...")
    
    try:
        while True:
            time.sleep(5)
            
            current_records = get_current_records()
            new_records, modified_records = compare_records(before_records, current_records)
            
            if new_records or modified_records:
                print(f"\n🔔 检测到变化 - {datetime.now().strftime('%H:%M:%S')}")
                
                if new_records:
                    print(f"📝 新增记录 ({len(new_records)}条):")
                    for record in new_records:
                        human_flag = "👨‍💼" if record['is_human_modified'] else "🤖"
                        print(f"  ➕ ID {record['id']}: {human_flag} {record['user_input']}")
                
                if modified_records:
                    print(f"✏️  修改记录 ({len(modified_records)}条):")
                    for mod in modified_records:
                        before_human = "👨‍💼" if mod['changes']['before']['is_human_modified'] else "🤖"
                        after_human = "👨‍💼" if mod['changes']['after']['is_human_modified'] else "🤖"
                        print(f"  ✏️  ID {mod['id']}: {before_human} → {after_human}")
                
                # 检查是否产生了新的重复
                duplicates = find_duplicates(current_records)
                if duplicates:
                    print(f"⚠️  发现重复记录 ({len(duplicates)}组):")
                    for dup in duplicates:
                        time_diff = dup['time_diff_seconds']
                        print(f"    🔁 ID {dup['record1']['id']} ↔ ID {dup['record2']['id']} (间隔{time_diff:.1f}秒)")
                        print(f"       问题: {dup['record1']['user_input']}")
                
                before_records = current_records
                
    except KeyboardInterrupt:
        print("\n\n🛑 监控已停止")
        
        # 最终统计
        final_records = get_current_records()
        final_duplicates = find_duplicates(final_records)
        
        print(f"\n📊 最终统计:")
        print(f"   总记录数: {len(final_records)}")
        print(f"   重复记录组: {len(final_duplicates)}")
        
        if final_duplicates:
            print(f"\n🔍 重复记录详情:")
            for i, dup in enumerate(final_duplicates, 1):
                print(f"   组 {i}: ID {dup['record1']['id']} ↔ ID {dup['record2']['id']}")
                print(f"      问题: {dup['record1']['user_input']}")
                print(f"      时间间隔: {dup['time_diff_seconds']:.1f}秒")

def analyze_recent_duplicates():
    """分析最近创建的重复记录"""
    print("🔍 分析最近的重复记录...")
    
    with app.app_context():
        # 获取最近24小时的记录
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(hours=24)
        
        recent_records = EvaluationHistory.query.filter(
            EvaluationHistory.created_at >= yesterday
        ).order_by(EvaluationHistory.created_at.desc()).all()
        
        print(f"📊 最近24小时记录数: {len(recent_records)}")
        
        # 按内容分组查找重复
        content_groups = {}
        for record in recent_records:
            key = f"{record.user_input}|||{record.model_answer}"
            if key not in content_groups:
                content_groups[key] = []
            content_groups[key].append(record)
        
        # 找出重复组
        duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
        
        if duplicate_groups:
            print(f"\n⚠️  发现 {len(duplicate_groups)} 组重复记录:")
            
            for i, (key, records) in enumerate(duplicate_groups.items(), 1):
                question = records[0].user_input[:30] + "..." if len(records[0].user_input) > 30 else records[0].user_input
                print(f"\n组 {i}: {question}")
                print(f"   记录数: {len(records)}")
                
                for j, record in enumerate(records):
                    human_flag = "👨‍💼" if record.is_human_modified else "🤖"
                    time_str = record.created_at.strftime('%H:%M:%S')
                    update_str = record.updated_at.strftime('%H:%M:%S') if record.updated_at else "无"
                    print(f"   记录 {j+1}: ID {record.id} {human_flag} 创建:{time_str} 更新:{update_str}")
                
                # 分析时间间隔
                if len(records) >= 2:
                    time_diffs = []
                    for j in range(len(records) - 1):
                        diff = abs((records[j].created_at - records[j+1].created_at).total_seconds())
                        time_diffs.append(diff)
                    
                    avg_diff = sum(time_diffs) / len(time_diffs)
                    print(f"   平均时间间隔: {avg_diff:.1f}秒")
                    
                    if avg_diff < 10:
                        print(f"   🚨 疑似快速重复提交（间隔<10秒）")
                    elif avg_diff < 60:
                        print(f"   ⚠️  疑似重复操作（间隔<1分钟）")
        else:
            print("✅ 最近24小时无重复记录")

def main():
    """主函数"""
    print("🔍 重复记录创建追踪工具")
    print("=" * 50)
    
    print("\n1. 分析现有重复记录")
    analyze_recent_duplicates()
    
    print("\n" + "=" * 50)
    print("2. 实时监控数据库变化")
    print("💡 提示：请在另一个终端进行评估操作来触发重复记录创建")
    print("   然后观察本工具的输出来找出问题所在")
    
    try:
        input("\n按回车键开始实时监控，或Ctrl+C退出...")
        monitor_api_calls()
    except KeyboardInterrupt:
        print("\n👋 已退出")

if __name__ == '__main__':
    main() 