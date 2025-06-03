#!/usr/bin/env python3
"""
清理现有重复记录脚本
"""

from app import app
from models.classification import EvaluationHistory, db
from datetime import datetime

def clean_duplicate_records():
    with app.app_context():
        print("🧹 开始清理重复记录...")
        
        # 获取所有记录
        all_records = EvaluationHistory.query.all()
        print(f"📊 总记录数: {len(all_records)}")
        
        # 按内容分组
        content_groups = {}
        for record in all_records:
            key = f"{record.user_input}|||{record.model_answer}"
            if key not in content_groups:
                content_groups[key] = []
            content_groups[key].append(record)
        
        # 找出重复组
        duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
        
        if not duplicate_groups:
            print("✅ 没有发现重复记录")
            return
        
        print(f"🚨 发现 {len(duplicate_groups)} 组重复记录")
        
        cleaned_count = 0
        for key, records in duplicate_groups.items():
            # 排序：优先保留人工修改的记录，然后按ID排序
            records.sort(key=lambda x: (not x.is_human_modified, x.id))
            
            # 保留第一条，删除其余
            keep_record = records[0]
            delete_records = records[1:]
            
            print(f"保留记录ID: {keep_record.id}, 删除: {[r.id for r in delete_records]}")
            
            # 合并人工评估数据
            for delete_record in delete_records:
                if delete_record.is_human_modified and not keep_record.is_human_modified:
                    keep_record.human_total_score = delete_record.human_total_score
                    keep_record.human_dimensions_json = delete_record.human_dimensions_json
                    keep_record.human_reasoning = delete_record.human_reasoning
                    keep_record.human_evaluation_by = delete_record.human_evaluation_by
                    keep_record.human_evaluation_time = delete_record.human_evaluation_time
                    keep_record.is_human_modified = True
                    keep_record.updated_at = datetime.utcnow()
                
                db.session.delete(delete_record)
                cleaned_count += 1
        
        db.session.commit()
        print(f"✅ 清理完成，删除了 {cleaned_count} 条重复记录")

if __name__ == '__main__':
    clean_duplicate_records()
