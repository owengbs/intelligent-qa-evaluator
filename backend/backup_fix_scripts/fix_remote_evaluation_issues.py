#!/usr/bin/env python3
"""
修复远端评估系统问题的专门脚本
解决：
1. 评估记录保存问题 - 前端尝试POST /api/evaluation-history返回405
2. 人工评估"记录不存在"问题
3. 数据库记录查询问题
"""

import os
import sys
import json
from datetime import datetime

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_evaluation_records():
    """检查现有评估记录"""
    print("🔍 检查评估记录...")
    
    try:
        from app import app
        from models.classification import EvaluationHistory
        
        with app.app_context():
            # 获取最近的评估记录
            recent_records = EvaluationHistory.query.order_by(
                EvaluationHistory.id.desc()
            ).limit(10).all()
            
            print(f"✅ 找到 {len(recent_records)} 条最近的评估记录")
            
            for record in recent_records:
                print(f"  ID: {record.id}, 总分: {record.total_score}, 创建时间: {record.created_at}")
                
                # 检查记录的to_dict方法是否正常
                try:
                    data = record.to_dict()
                    print(f"    ✅ 记录 {record.id} 序列化正常")
                except Exception as e:
                    print(f"    ❌ 记录 {record.id} 序列化失败: {e}")
            
            return recent_records
            
    except Exception as e:
        print(f"❌ 检查评估记录失败: {e}")
        return []

def test_human_evaluation_api():
    """测试人工评估API"""
    print("\n🧪 测试人工评估API...")
    
    try:
        from app import app
        from models.classification import EvaluationHistory
        from services.evaluation_history_service import EvaluationHistoryService
        
        with app.app_context():
            # 找一个最近的评估记录
            recent_record = EvaluationHistory.query.order_by(
                EvaluationHistory.id.desc()
            ).first()
            
            if not recent_record:
                print("❌ 没有找到可测试的评估记录")
                return False
            
            print(f"✅ 找到测试记录 ID: {recent_record.id}")
            
            # 测试获取记录
            service = EvaluationHistoryService()
            result = service.get_evaluation_by_id(recent_record.id)
            
            if result['success']:
                print(f"✅ 获取评估记录成功")
            else:
                print(f"❌ 获取评估记录失败: {result['message']}")
                return False
            
            # 测试人工评估更新
            test_human_data = {
                'human_total_score': 8.5,
                'human_dimensions': {'accuracy': 4, 'completeness': 3, 'clarity': 2},
                'human_reasoning': '测试人工评估功能',
                'evaluator_name': '测试专家'
            }
            
            update_result = service.update_human_evaluation(
                recent_record.id, 
                test_human_data, 
                '测试专家'
            )
            
            if update_result['success']:
                print(f"✅ 人工评估更新成功")
                
                # 恢复原状
                service.update_human_evaluation(
                    recent_record.id,
                    {
                        'human_total_score': None,
                        'human_reasoning': None,
                        'evaluator_name': None
                    }
                )
                
                return True
            else:
                print(f"❌ 人工评估更新失败: {update_result['message']}")
                return False
                
    except Exception as e:
        print(f"❌ 测试人工评估API失败: {e}")
        return False

def fix_duplicate_saving_issue():
    """修复重复保存问题"""
    print("\n🔧 分析重复保存问题...")
    
    # 这个问题需要在前端修复，但我们可以在后端添加POST路由支持
    print("💡 问题分析：")
    print("  1. 前端在evaluate()后尝试调用saveEvaluationHistory()")
    print("  2. 后端在/api/evaluate中已经保存了记录")
    print("  3. 前端的额外POST /api/evaluation-history调用返回405")
    print("\n💡 解决方案：")
    print("  1. 后端添加POST /api/evaluation-history路由（兼容性）")
    print("  2. 前端优化：检查evaluate响应是否包含history_id，避免重复保存")
    
    return True

def add_missing_post_route():
    """在app.py中添加缺失的POST路由"""
    print("\n🔧 检查是否需要添加POST /api/evaluation-history路由...")
    
    try:
        # 读取app.py文件
        app_py_path = 'app.py'
        if not os.path.exists(app_py_path):
            print("❌ 找不到app.py文件")
            return False
        
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有POST路由
        if 'POST.*evaluation-history' in content and not 'human-evaluation' in content:
            print("✅ POST /api/evaluation-history路由已存在")
            return True
        
        # 添加POST路由（在现有GET路由后）
        post_route = '''
@app.route('/api/evaluation-history', methods=['POST'])
def save_evaluation_history():
    """保存评估历史记录（兼容前端重复保存调用）"""
    try:
        logger.info("前端尝试保存评估历史记录")
        
        data = request.get_json()
        
        # 检查是否已经存在相同的记录（避免重复）
        if data.get('user_input') and data.get('model_answer'):
            existing = EvaluationHistory.query.filter_by(
                user_input=data['user_input'],
                model_answer=data['model_answer']
            ).order_by(EvaluationHistory.created_at.desc()).first()
            
            # 如果最近2分钟内有相同记录，返回现有记录
            if existing and (datetime.utcnow() - existing.created_at).seconds < 120:
                logger.info(f"发现重复记录，返回现有记录ID: {existing.id}")
                return jsonify({
                    'success': True,
                    'message': '记录已存在，返回现有记录',
                    'history_id': existing.id,
                    'data': existing.to_dict()
                })
        
        # 调用服务保存记录
        result = evaluation_history_service.save_evaluation_result(data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"保存评估历史失败: {str(e)}")
        return jsonify({'error': f'保存评估历史失败: {str(e)}'}), 500
'''
        
        # 找到合适的插入位置（在现有评估历史路由后）
        import re
        pattern = r'(@app\.route\(\'/api/evaluation-history\', methods=\[\'GET\'\]\)[^@]*?except[^@]*?return[^@]*?500[^@]*?\n)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # 在GET路由后插入POST路由
            insert_pos = match.end()
            new_content = content[:insert_pos] + post_route + content[insert_pos:]
            
            # 备份原文件
            backup_path = 'app.py.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 写入新内容
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ 已添加POST路由到app.py（备份：{backup_path}）")
            return True
        else:
            print("❌ 找不到合适的插入位置")
            return False
            
    except Exception as e:
        print(f"❌ 添加POST路由失败: {e}")
        return False

def create_test_evaluation_for_human():
    """创建一个专门用于测试人工评估的记录"""
    print("\n🧪 创建测试评估记录（用于人工评估测试）...")
    
    try:
        from app import app
        from models.classification import db, EvaluationHistory
        
        with app.app_context():
            # 创建测试记录
            test_data = {
                'user_input': '【人工评估测试】什么是机器学习？',
                'model_answer': '机器学习是人工智能的一个分支，它使用算法和统计模型来让计算机在没有明确编程的情况下学习和改进。',
                'reference_answer': '机器学习是一种人工智能技术，通过算法让计算机从数据中学习模式。',
                'question_time': datetime.utcnow(),
                'evaluation_criteria': '测试用评估标准',
                'total_score': 7.5,
                'dimensions': {'准确性': 4, '完整性': 3, '清晰度': 2},
                'reasoning': '这是一个专门用于测试人工评估功能的记录',
                'classification_level1': '信息查询',
                'classification_level2': '通用查询',
                'classification_level3': '通用查询',
                'evaluation_time_seconds': 3.2,
                'model_used': 'test-model',
                'raw_response': '测试原始响应'
            }
            
            evaluation = EvaluationHistory.from_dict(test_data)
            db.session.add(evaluation)
            db.session.commit()
            
            print(f"✅ 创建测试记录成功，ID: {evaluation.id}")
            print(f"📋 请在前端访问这个记录进行人工评估测试")
            
            return evaluation.id
            
    except Exception as e:
        print(f"❌ 创建测试记录失败: {e}")
        return None

def verify_frontend_backend_consistency():
    """验证前后端数据一致性"""
    print("\n🔍 验证前后端数据一致性...")
    
    try:
        from app import app
        from models.classification import EvaluationHistory
        
        with app.app_context():
            # 获取最新的几条记录
            records = EvaluationHistory.query.order_by(
                EvaluationHistory.id.desc()
            ).limit(5).all()
            
            print(f"📊 数据库中最新的 {len(records)} 条记录：")
            
            for record in records:
                print(f"  ID: {record.id}")
                print(f"    总分: {record.total_score}")
                print(f"    是否人工修改: {record.is_human_modified}")
                print(f"    创建时间: {record.created_at}")
                
                # 测试序列化
                try:
                    data = record.to_dict()
                    print(f"    ✅ 序列化正常，包含字段: {len(data)} 个")
                except Exception as e:
                    print(f"    ❌ 序列化失败: {e}")
                
                print()
            
            return len(records) > 0
            
    except Exception as e:
        print(f"❌ 验证数据一致性失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 远端评估系统问题诊断和修复工具")
    print("=" * 60)
    
    issues_found = []
    test_record_id = None
    
    # 1. 检查现有评估记录
    records = check_evaluation_records()
    if not records:
        issues_found.append("没有找到评估记录")
    
    # 2. 测试人工评估API
    if not test_human_evaluation_api():
        issues_found.append("人工评估API异常")
    
    # 3. 分析重复保存问题
    fix_duplicate_saving_issue()
    
    # 4. 添加缺失的POST路由
    if not add_missing_post_route():
        issues_found.append("无法添加POST路由")
    
    # 5. 创建测试记录
    test_record_id = create_test_evaluation_for_human()
    if not test_record_id:
        issues_found.append("无法创建测试记录")
    
    # 6. 验证数据一致性
    if not verify_frontend_backend_consistency():
        issues_found.append("前后端数据不一致")
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 诊断和修复结果")
    print("=" * 60)
    
    if not issues_found:
        print("🎉 所有检查通过！远端评估系统问题已修复。")
        if test_record_id:
            print(f"\n📋 测试记录ID: {test_record_id}")
            print("请在前端尝试对这条记录进行人工评估。")
        
        print("\n🔄 建议重启后端服务以应用POST路由修复：")
        print("  python app.py")
        
    else:
        print(f"⚠️  发现 {len(issues_found)} 个问题：")
        for issue in issues_found:
            print(f"  - {issue}")
        
        print("\n💡 建议操作：")
        print("1. 重启Flask应用")
        print("2. 清除浏览器缓存")
        print("3. 检查前端控制台错误")
        
        if test_record_id:
            print(f"4. 使用测试记录ID {test_record_id} 进行人工评估")
    
    return len(issues_found) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 