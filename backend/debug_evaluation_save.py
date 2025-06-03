#!/usr/bin/env python3
"""
评估数据保存问题调试脚本
分析前端发送的数据格式和后端处理逻辑
"""

import json
import os
from datetime import datetime
from flask import Flask
from app import app, evaluation_history_service
from models.classification import db, EvaluationHistory

def test_evaluation_data_format():
    """测试不同格式的评估数据"""
    print("🔍 测试评估数据格式和保存逻辑...")
    
    # 测试用例1：完整的评估数据（前端发送的格式）
    test_data_1 = {
        'user_input': '什么是机器学习？',
        'model_answer': '机器学习是人工智能的一个分支，它使用算法和统计模型来让计算机在没有明确编程的情况下学习和改进。',
        'reference_answer': '机器学习是一种人工智能技术。',
        'question_time': '2025-06-03T10:30:00',
        'evaluation_criteria': '请评估答案的准确性、相关性和有用性',
        'total_score': 7.5,
        'dimensions': {'准确性': 4, '完整性': 3, '流畅性': 2.5},
        'reasoning': '答案准确且完整，但可以更简洁',
        'raw_response': '原始LLM响应'
    }
    
    # 测试用例2：评估API返回后前端发送的格式
    test_data_2 = {
        'user_input': '什么是机器学习？',
        'model_answer': '机器学习是人工智能的一个分支。',
        'reference_answer': '机器学习是一种人工智能技术。',
        'question_time': '2025-06-03T10:30:00',
        'evaluation_criteria': '请评估答案的准确性、相关性和有用性',
        'total_score': 7.5,
        'dimensions': {'准确性': 4, '完整性': 3, '流畅性': 2.5},
        'reasoning': '答案准确且完整，但可以更简洁',
        'raw_response': '原始LLM响应'
    }
    
    # 测试用例3：缺少必需字段的数据
    test_data_3 = {
        'test': 'data'  # 缺少必需字段
    }
    
    with app.app_context():
        print("\n📊 测试数据格式:")
        
        for i, test_data in enumerate([test_data_1, test_data_2, test_data_3], 1):
            print(f"\n--- 测试用例 {i} ---")
            print(f"输入数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
            
            try:
                # 测试保存
                result = evaluation_history_service.save_evaluation_result(test_data)
                print(f"保存结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print(f"✅ 测试用例 {i} 保存成功")
                else:
                    print(f"❌ 测试用例 {i} 保存失败: {result.get('message')}")
                    
            except Exception as e:
                print(f"❌ 测试用例 {i} 出现异常: {str(e)}")

def analyze_frontend_backend_data_flow():
    """分析前后端数据流转"""
    print("\n🔄 分析前后端数据流转...")
    
    print("1. 前端评估请求流程:")
    print("   用户填写表单 → 调用 evaluationService.evaluate() → POST /api/evaluate")
    print("   → 后端返回评估结果 → 前端自动调用 saveEvaluationHistory()")
    print("   → POST /api/evaluation-history → 保存到数据库")
    
    print("\n2. 前端发送的数据结构:")
    frontend_data = {
        "user_input": "用户问题",
        "model_answer": "模型回答", 
        "reference_answer": "参考答案",
        "question_time": "2025-06-03T10:30:00",
        "evaluation_criteria": "评估标准",
        "total_score": 7.5,
        "dimensions": {"准确性": 4, "完整性": 3},
        "reasoning": "评估理由",
        "raw_response": "原始响应"
    }
    print(f"   {json.dumps(frontend_data, ensure_ascii=False, indent=4)}")
    
    print("\n3. 后端期望的数据结构（evaluation_history_service.py）:")
    backend_expected = {
        "user_input": "evaluation_data.get('user_input')",
        "model_answer": "evaluation_data.get('model_answer')",
        "reference_answer": "evaluation_data.get('reference_answer')",
        "question_time": "evaluation_data.get('question_time')",
        "evaluation_criteria": "evaluation_data.get('evaluation_criteria_used')",  # 注意这里是 evaluation_criteria_used
        "total_score": "evaluation_data.get('score', 0.0)",  # 注意这里是 score
        "dimensions": "evaluation_data.get('dimensions', {})",
        "reasoning": "evaluation_data.get('reasoning')",
        "raw_response": "evaluation_data.get('raw_response')"
    }
    print(f"   {json.dumps(backend_expected, ensure_ascii=False, indent=4)}")
    
    print("\n4. 发现的字段映射问题:")
    print("   ❌ 前端发送: 'total_score' → 后端期望: 'score'")
    print("   ❌ 前端发送: 'evaluation_criteria' → 后端期望: 'evaluation_criteria_used'")

def check_database_schema():
    """检查数据库模式"""
    print("\n📋 检查数据库模式...")
    
    with app.app_context():
        try:
            # 检查表结构
            result = db.session.execute("PRAGMA table_info(evaluation_history)")
            columns = result.fetchall()
            
            print("evaluation_history 表结构:")
            required_fields = []
            for col in columns:
                col_id, name, data_type, not_null, default_val, pk = col
                constraint = "NOT NULL" if not_null else "NULLABLE"
                if pk:
                    constraint += " PRIMARY KEY"
                print(f"  {name}: {data_type} ({constraint})")
                if not_null and not pk and default_val is None:
                    required_fields.append(name)
            
            print(f"\n必需字段（NOT NULL且无默认值）: {required_fields}")
            
            # 检查现有记录数量
            count = EvaluationHistory.query.count()
            print(f"当前记录数量: {count}")
            
        except Exception as e:
            print(f"❌ 检查数据库模式失败: {e}")

def fix_backend_data_mapping():
    """修复后端数据映射问题"""
    print("\n🔧 生成后端数据映射修复方案...")
    
    print("问题分析:")
    print("1. 前端发送的字段名与后端期望的字段名不匹配")
    print("2. evaluation_history_service.py 中的字段映射需要调整")
    
    print("\n修复方案:")
    print("修改 backend/services/evaluation_history_service.py 中的 save_evaluation_result 方法")
    print("将字段映射调整为:")
    
    fixed_mapping = """
    history_data = {
        'user_input': evaluation_data.get('user_input'),
        'model_answer': evaluation_data.get('model_answer'),
        'reference_answer': evaluation_data.get('reference_answer'),
        'question_time': evaluation_data.get('question_time'),
        'evaluation_criteria': evaluation_data.get('evaluation_criteria') or evaluation_data.get('evaluation_criteria_used'),
        'total_score': evaluation_data.get('total_score') or evaluation_data.get('score', 0.0),
        'dimensions': evaluation_data.get('dimensions', {}),
        'reasoning': evaluation_data.get('reasoning'),
        'evaluation_time_seconds': evaluation_data.get('evaluation_time_seconds'),
        'model_used': evaluation_data.get('model_used'),
        'raw_response': evaluation_data.get('raw_response')
    }
    """
    print(fixed_mapping)

def test_cloud_vs_local_config():
    """测试云端与本地配置差异"""
    print("\n☁️ 检查云端与本地配置差异...")
    
    print("前端配置检查:")
    print("1. API_BASE_URL 配置:")
    print("   - 环境变量: REACT_APP_API_URL")
    print("   - 默认值: http://localhost:5001/api")
    print("   - 云端应该设置为: http://your-cloud-server:5001/api")
    
    print("\n2. package.json 代理配置:")
    print("   - 本地代理: http://localhost:5001")
    print("   - 云端需要修改为实际的后端地址")
    
    print("\n后端配置检查:")
    print("1. Flask 启动配置:")
    print("   - 本地: app.run(host='0.0.0.0', port=5001)")
    print("   - 云端: 确保端口5001可访问")
    
    print("\n2. CORS 配置:")
    print("   - 当前: CORS(app) # 允许所有来源")
    print("   - 建议: 在生产环境限制CORS来源")

def main():
    """主函数"""
    print("🔧 评估数据保存问题调试工具")
    print("=" * 60)
    
    # 1. 测试数据格式
    test_evaluation_data_format()
    
    # 2. 分析数据流转
    analyze_frontend_backend_data_flow()
    
    # 3. 检查数据库模式
    check_database_schema()
    
    # 4. 生成修复方案
    fix_backend_data_mapping()
    
    # 5. 检查配置差异
    test_cloud_vs_local_config()
    
    print("\n" + "=" * 60)
    print("🎯 调试完成！请根据上述分析结果进行修复。")

if __name__ == '__main__':
    main() 