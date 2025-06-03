#!/usr/bin/env python3
"""
调试重复记录问题
分析为什么AI评估完成后进行人工评估会创建两条记录
"""

import json
from datetime import datetime, timedelta
from flask import Flask
from app import app, evaluation_history_service
from models.classification import db, EvaluationHistory

def analyze_duplicate_records():
    """分析重复记录问题"""
    print("🔍 分析重复记录问题...")
    
    with app.app_context():
        # 查找最近的记录
        recent_records = EvaluationHistory.query.order_by(
            EvaluationHistory.created_at.desc()
        ).limit(20).all()
        
        print(f"📊 最近20条记录:")
        for record in recent_records:
            human_flag = "👨‍💼" if record.is_human_modified else "🤖"
            print(f"  ID: {record.id} | {human_flag} | {record.user_input[:30]}... | 分数: {record.total_score} | 创建时间: {record.created_at}")
        
        # 查找可能重复的记录（相同问题和答案）
        print(f"\n🔍 查找可能重复的记录...")
        
        duplicates = []
        for record in recent_records:
            similar_records = EvaluationHistory.query.filter(
                EvaluationHistory.user_input == record.user_input,
                EvaluationHistory.model_answer == record.model_answer,
                EvaluationHistory.id != record.id
            ).all()
            
            if similar_records:
                duplicates.append({
                    'original': record,
                    'duplicates': similar_records
                })
        
        if duplicates:
            print(f"🚨 发现 {len(duplicates)} 组重复记录:")
            for group in duplicates:
                print(f"  原记录 ID: {group['original'].id}")
                for dup in group['duplicates']:
                    print(f"    重复记录 ID: {dup.id} | 人工修改: {dup.is_human_modified}")
        else:
            print("✅ 未发现明显的重复记录")

def test_evaluation_flow():
    """测试评估流程，模拟AI评估+人工评估的完整过程"""
    print("\n🧪 测试完整评估流程...")
    
    with app.app_context():
        # 1. 模拟AI评估结果保存
        print("1️⃣ 模拟AI评估结果保存...")
        
        ai_evaluation_data = {
            'user_input': '【测试】什么是机器学习？',
            'model_answer': '机器学习是人工智能的一个分支。',
            'reference_answer': '机器学习是一种AI技术。',
            'question_time': datetime.now().isoformat(),
            'evaluation_criteria': '测试评估标准',
            'total_score': 7.5,
            'dimensions': {'准确性': 4, '完整性': 3, '流畅性': 2.5},
            'reasoning': 'AI评估结果',
            'raw_response': '原始LLM响应'
        }
        
        ai_result = evaluation_history_service.save_evaluation_result(ai_evaluation_data)
        
        if ai_result['success']:
            history_id = ai_result['history_id']
            print(f"✅ AI评估保存成功，ID: {history_id}")
            
            # 2. 模拟人工评估更新
            print("2️⃣ 模拟人工评估更新...")
            
            human_evaluation_data = {
                'human_total_score': 8.0,
                'human_dimensions': {'准确性': 4, '完整性': 3, '流畅性': 3},
                'human_reasoning': '人工评估：回答质量良好，流畅性需要提升',
                'evaluator_name': '测试专家'
            }
            
            human_result = evaluation_history_service.update_human_evaluation(
                history_id, human_evaluation_data, '测试专家'
            )
            
            if human_result['success']:
                print(f"✅ 人工评估更新成功")
                
                # 3. 检查是否只有一条记录
                records = EvaluationHistory.query.filter(
                    EvaluationHistory.user_input == ai_evaluation_data['user_input']
                ).all()
                
                print(f"📊 相同问题的记录数量: {len(records)}")
                
                if len(records) == 1:
                    print("✅ 正常：只有一条记录")
                    record = records[0]
                    print(f"   记录详情:")
                    print(f"   - ID: {record.id}")
                    print(f"   - AI分数: {record.total_score}")
                    print(f"   - 人工分数: {record.human_total_score}")
                    print(f"   - 人工修改标记: {record.is_human_modified}")
                else:
                    print(f"❌ 异常：有 {len(records)} 条记录")
                    for i, record in enumerate(records):
                        print(f"   记录 {i+1}: ID={record.id}, 人工修改={record.is_human_modified}")
                
                # 清理测试数据
                for record in records:
                    db.session.delete(record)
                db.session.commit()
                print("🗑️  测试数据已清理")
                
                return True
            else:
                print(f"❌ 人工评估更新失败: {human_result['message']}")
                return False
        else:
            print(f"❌ AI评估保存失败: {ai_result['message']}")
            return False

def check_frontend_logic():
    """检查前端逻辑可能导致的重复问题"""
    print("\n🔍 分析前端可能的重复保存逻辑...")
    
    frontend_analysis = """
📋 前端逻辑分析：

1. AI评估流程:
   - 用户提交评估 → evaluationService.evaluate() 
   - evaluate() 成功后自动调用 saveEvaluationHistory()
   - 创建第一条记录 ✅

2. 人工评估流程:
   - 用户点击"人工评估" → handleHumanEvaluation()
   - 用户提交人工评估 → handleHumanEvaluationSubmit()
   - 调用 PUT /api/evaluation-history/{id}/human-evaluation
   - 应该**更新**现有记录，不创建新记录 ✅

3. 可能的问题点:
   ❓ 前端是否在人工评估时意外触发了额外的保存？
   ❓ 后端人工评估更新逻辑是否有问题？
   ❓ 是否存在并发请求导致的重复？

4. 需要检查的地方:
   - handleHumanEvaluationSubmit 中是否有多余的保存调用
   - 后端 update_human_evaluation 是否会创建新记录
   - 前端是否存在重复提交
"""
    
    print(frontend_analysis)

def check_backend_logic():
    """检查后端逻辑"""
    print("\n🔍 检查后端人工评估更新逻辑...")
    
    # 检查update_human_evaluation方法
    print("📋 后端逻辑分析:")
    print("1. update_human_evaluation 方法:")
    print("   - 通过 history_id 查找现有记录")
    print("   - 更新 human_* 字段")
    print("   - 设置 is_human_modified = True")
    print("   - 调用 db.session.commit() 保存更改")
    print("   - ✅ 应该只是更新，不会创建新记录")
    
    print("\n2. 可能的问题:")
    print("   - ❓ 前端是否调用了错误的接口？")
    print("   - ❓ 是否存在其他代码路径创建了新记录？")
    print("   - ❓ 数据库事务是否有问题？")

def create_monitoring_script():
    """创建监控脚本来追踪记录创建"""
    print("\n📜 创建记录监控脚本...")
    
    monitor_script = """#!/usr/bin/env python3
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
"""
    
    with open('monitor_records.py', 'w', encoding='utf-8') as f:
        f.write(monitor_script)
    
    print("📜 监控脚本已创建: monitor_records.py")
    print("使用方法: python monitor_records.py")

def suggest_fix():
    """提出修复建议"""
    print("\n🔧 修复建议:")
    
    suggestions = """
1. **立即检查项**:
   - 检查前端 handleHumanEvaluationSubmit 是否有多余的保存调用
   - 确认后端 update_human_evaluation 不会创建新记录
   - 检查是否存在前端重复提交问题

2. **前端修复**:
   - 在人工评估提交时添加防重复提交机制
   - 确保人工评估只调用更新接口，不调用创建接口

3. **后端修复**:
   - 在 update_human_evaluation 中添加更多日志
   - 确保人工评估更新是原子操作

4. **监控方案**:
   - 使用 monitor_records.py 脚本实时监控
   - 在前后端添加详细的操作日志

5. **数据清理**:
   - 识别并合并重复的记录
   - 保留人工评估结果，删除多余的AI评估记录
"""
    
    print(suggestions)

def main():
    """主函数"""
    print("🔧 重复记录问题调试工具")
    print("=" * 60)
    
    # 1. 分析现有重复记录
    analyze_duplicate_records()
    
    # 2. 测试评估流程
    test_evaluation_flow()
    
    # 3. 分析前端逻辑
    check_frontend_logic()
    
    # 4. 检查后端逻辑
    check_backend_logic()
    
    # 5. 创建监控脚本
    create_monitoring_script()
    
    # 6. 提出修复建议
    suggest_fix()
    
    print("\n" + "=" * 60)
    print("🎯 调试分析完成！")
    print("\n📋 接下来的步骤:")
    print("1. 运行监控脚本: python monitor_records.py")
    print("2. 进行一次完整的评估测试")
    print("3. 根据监控结果确定具体问题")
    print("4. 实施相应的修复方案")

if __name__ == '__main__':
    main() 