#!/usr/bin/env python3
"""
修复远端环境问题的脚本
主要解决：
1. 数据库日期字段格式不一致问题
2. 人工评估记录不存在问题
3. 数据库表结构缺失问题
"""

import os
import sys
import sqlite3
from datetime import datetime
import json

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_database_structure():
    """检查数据库表结构"""
    print("🔍 检查数据库表结构...")
    
    db_path = os.path.join('data', 'qa_evaluator.db')
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查evaluation_history表结构
        cursor.execute("PRAGMA table_info(evaluation_history)")
        columns = cursor.fetchall()
        
        print(f"✅ evaluation_history表有 {len(columns)} 个字段")
        
        # 检查是否有人工评估字段
        column_names = [col[1] for col in columns]
        human_eval_fields = [
            'human_total_score',
            'human_dimensions_json', 
            'human_reasoning',
            'human_evaluation_by',
            'human_evaluation_time',
            'is_human_modified'
        ]
        
        missing_fields = []
        for field in human_eval_fields:
            if field not in column_names:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少人工评估字段: {missing_fields}")
            return False
        else:
            print("✅ 人工评估字段完整")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查数据库结构失败: {e}")
        return False

def fix_date_format_issues():
    """修复日期格式问题"""
    print("\n🔧 修复日期格式问题...")
    
    try:
        from app import app
        from models.classification import db, EvaluationHistory
        
        with app.app_context():
            # 获取所有评估记录
            evaluations = EvaluationHistory.query.all()
            
            fixed_count = 0
            for evaluation in evaluations:
                try:
                    # 尝试调用to_dict方法，如果出错就修复
                    evaluation.to_dict()
                except Exception as e:
                    print(f"修复记录 {evaluation.id} 的日期格式问题...")
                    
                    # 修复可能的日期字段问题
                    if evaluation.question_time and isinstance(evaluation.question_time, str):
                        try:
                            evaluation.question_time = datetime.fromisoformat(evaluation.question_time.replace('Z', '+00:00'))
                        except:
                            evaluation.question_time = None
                    
                    if evaluation.human_evaluation_time and isinstance(evaluation.human_evaluation_time, str):
                        try:
                            evaluation.human_evaluation_time = datetime.fromisoformat(evaluation.human_evaluation_time.replace('Z', '+00:00'))
                        except:
                            evaluation.human_evaluation_time = None
                    
                    if evaluation.created_at and isinstance(evaluation.created_at, str):
                        try:
                            evaluation.created_at = datetime.fromisoformat(evaluation.created_at.replace('Z', '+00:00'))
                        except:
                            evaluation.created_at = datetime.utcnow()
                    
                    if evaluation.updated_at and isinstance(evaluation.updated_at, str):
                        try:
                            evaluation.updated_at = datetime.fromisoformat(evaluation.updated_at.replace('Z', '+00:00'))
                        except:
                            evaluation.updated_at = datetime.utcnow()
                    
                    fixed_count += 1
            
            if fixed_count > 0:
                db.session.commit()
                print(f"✅ 修复了 {fixed_count} 条记录的日期格式")
            else:
                print("✅ 所有记录的日期格式正常")
            
            return True
            
    except Exception as e:
        print(f"❌ 修复日期格式失败: {e}")
        return False

def verify_human_evaluation_api():
    """验证人工评估API功能"""
    print("\n🧪 验证人工评估API功能...")
    
    try:
        from app import app
        from models.classification import EvaluationHistory
        
        with app.app_context():
            # 找一个评估记录进行测试
            evaluation = EvaluationHistory.query.first()
            
            if not evaluation:
                print("⚠️  没有评估记录可用于测试")
                return False
            
            print(f"✅ 找到测试记录 ID: {evaluation.id}")
            
            # 测试to_dict方法
            try:
                data = evaluation.to_dict()
                print("✅ to_dict方法正常")
            except Exception as e:
                print(f"❌ to_dict方法失败: {e}")
                return False
            
            # 测试人工评估更新
            try:
                evaluation.human_total_score = 8.0
                evaluation.human_reasoning = "测试人工评估"
                evaluation.human_evaluation_by = "测试用户"
                evaluation.human_evaluation_time = datetime.utcnow()
                evaluation.is_human_modified = True
                
                from models.classification import db
                db.session.commit()
                print("✅ 人工评估更新功能正常")
                
                # 恢复原状
                evaluation.human_total_score = None
                evaluation.human_reasoning = None
                evaluation.human_evaluation_by = None
                evaluation.human_evaluation_time = None
                evaluation.is_human_modified = False
                db.session.commit()
                
            except Exception as e:
                print(f"❌ 人工评估更新失败: {e}")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ 验证人工评估API失败: {e}")
        return False

def check_evaluation_statistics():
    """检查评估统计功能"""
    print("\n📊 检查评估统计功能...")
    
    try:
        from app import app
        from services.evaluation_history_service import EvaluationHistoryService
        
        with app.app_context():
            service = EvaluationHistoryService()
            
            # 测试获取统计信息
            stats = service.get_evaluation_statistics()
            
            if stats['success']:
                print("✅ 评估统计功能正常")
                print(f"  总评估数: {stats['data']['total_evaluations']}")
                return True
            else:
                print(f"❌ 评估统计功能失败: {stats['message']}")
                return False
                
    except Exception as e:
        print(f"❌ 检查评估统计功能失败: {e}")
        return False

def create_test_evaluation():
    """创建测试评估记录"""
    print("\n🧪 创建测试评估记录...")
    
    try:
        from app import app
        from models.classification import db, EvaluationHistory
        
        with app.app_context():
            # 创建测试记录
            test_data = {
                'user_input': '测试问题：什么是人工智能？',
                'model_answer': '人工智能是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。',
                'reference_answer': '人工智能（AI）是使机器能够执行通常需要人类智能的任务的技术。',
                'question_time': datetime.utcnow(),
                'evaluation_criteria': '测试评估标准',
                'total_score': 7.5,
                'dimensions': {'准确性': 4, '完整性': 3, '流畅性': 3},
                'reasoning': '这是一个测试评估记录',
                'classification_level1': '信息查询',
                'classification_level2': '通用查询',
                'classification_level3': '通用查询',
                'evaluation_time_seconds': 2.5,
                'model_used': 'deepseek-chat',
                'raw_response': '测试原始响应'
            }
            
            evaluation = EvaluationHistory.from_dict(test_data)
            db.session.add(evaluation)
            db.session.commit()
            
            print(f"✅ 创建测试记录成功，ID: {evaluation.id}")
            
            # 测试人工评估更新
            evaluation.human_total_score = 8.0
            evaluation.human_reasoning = "人工评估：回答质量很好，准确性高"
            evaluation.human_evaluation_by = "测试专家"
            evaluation.human_evaluation_time = datetime.utcnow()
            evaluation.is_human_modified = True
            
            db.session.commit()
            print("✅ 人工评估更新成功")
            
            # 验证数据
            data = evaluation.to_dict()
            print(f"✅ 数据序列化成功，ID: {data['id']}")
            
            return evaluation.id
            
    except Exception as e:
        print(f"❌ 创建测试评估记录失败: {e}")
        return None

def main():
    """主函数"""
    print("🔧 远端环境问题修复工具")
    print("=" * 50)
    
    issues_found = []
    
    # 1. 检查数据库结构
    if not check_database_structure():
        issues_found.append("数据库结构问题")
    
    # 2. 修复日期格式问题
    if not fix_date_format_issues():
        issues_found.append("日期格式问题")
    
    # 3. 验证人工评估API
    if not verify_human_evaluation_api():
        issues_found.append("人工评估API问题")
    
    # 4. 检查评估统计
    if not check_evaluation_statistics():
        issues_found.append("评估统计问题")
    
    # 5. 创建测试记录
    test_id = create_test_evaluation()
    if not test_id:
        issues_found.append("测试记录创建问题")
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 修复结果总结")
    print("=" * 50)
    
    if not issues_found:
        print("🎉 所有检查通过！远端环境问题已修复。")
        if test_id:
            print(f"\n📋 测试记录ID: {test_id}")
            print("您可以在前端尝试对这条记录进行人工评估。")
    else:
        print(f"⚠️  发现 {len(issues_found)} 个问题：")
        for issue in issues_found:
            print(f"  - {issue}")
        
        print("\n💡 建议操作：")
        print("1. 运行数据库初始化: python quick_init.py")
        print("2. 重新创建数据库: python database/init_db.py")
        print("3. 检查Flask应用配置")
    
    return len(issues_found) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 