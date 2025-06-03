#!/usr/bin/env python3
# 重复记录监控仪表板

from app import app
from models.classification import EvaluationHistory
from datetime import datetime, timedelta
from collections import defaultdict

def show_duplicate_dashboard():
    with app.app_context():
        print("📊 重复记录监控仪表板")
        print("=" * 50)
        
        # 总体统计
        total_records = EvaluationHistory.query.count()
        human_modified = EvaluationHistory.query.filter(EvaluationHistory.is_human_modified == True).count()
        
        print(f"📈 总体统计:")
        print(f"   总记录数: {total_records}")
        print(f"   人工修改记录: {human_modified}")
        print(f"   纯AI记录: {total_records - human_modified}")
        
        # 最近24小时的记录
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recent_records = EvaluationHistory.query.filter(
            EvaluationHistory.created_at >= last_24h
        ).all()
        
        print(f"\n⏰ 最近24小时:")
        print(f"   新增记录: {len(recent_records)}")
        
        # 检查最近的重复
        recent_groups = defaultdict(list)
        for record in recent_records:
            key = f"{record.user_input}|||{record.model_answer}"
            recent_groups[key].append(record)
        
        recent_duplicates = {k: v for k, v in recent_groups.items() if len(v) > 1}
        
        if recent_duplicates:
            print(f"   ⚠️  发现最近重复: {len(recent_duplicates)} 组")
            for key, records in recent_duplicates.items():
                question = records[0].user_input[:30] + "..."
                print(f"     {question}: {len(records)} 条记录")
        else:
            print(f"   ✅ 无最近重复记录")
        
        # 按小时统计创建频率
        hour_stats = defaultdict(int)
        for record in recent_records:
            hour = record.created_at.hour
            hour_stats[hour] += 1
        
        print(f"\n📅 最近24小时创建频率:")
        for hour in sorted(hour_stats.keys()):
            print(f"   {hour:02d}:00-{hour:02d}:59: {hour_stats[hour]} 条记录")

if __name__ == '__main__':
    show_duplicate_dashboard()
