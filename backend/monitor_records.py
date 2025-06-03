#!/usr/bin/env python3
# 监控评估记录创建的脚本

from app import app
from models.classification import EvaluationHistory
from datetime import datetime

def monitor_records():
    with app.app_context():
        # 监控最近的记录变化
        before_count = EvaluationHistory.query.count()
        print(f"当前记录总数: {before_count}")
        
        # 等待用户操作
        input("请进行一次AI评估 + 人工评估，然后按回车键...")
        
        after_count = EvaluationHistory.query.count()
        new_records = after_count - before_count
        
        print(f"操作后记录总数: {after_count}")
        print(f"新增记录数: {new_records}")
        
        if new_records == 1:
            print("✅ 正常：只创建了1条记录")
        elif new_records == 2:
            print("❌ 异常：创建了2条记录！")
            # 显示最新的记录
            recent = EvaluationHistory.query.order_by(
                EvaluationHistory.id.desc()
            ).limit(2).all()
            
            for i, record in enumerate(recent):
                print(f"记录 {i+1}: ID={record.id}, 人工修改={record.is_human_modified}")
        else:
            print(f"⚠️  异常：创建了 {new_records} 条记录")

if __name__ == '__main__':
    monitor_records()
