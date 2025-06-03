#!/usr/bin/env python3
"""
完整修复验证脚本
验证重复记录问题是否彻底解决
"""

import os
import json
from datetime import datetime
from flask import Flask
from app import app
from models.classification import EvaluationHistory

def verify_duplicate_fix():
    """验证重复记录修复效果"""
    print("🔍 验证重复记录修复效果...")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查数据库状态
        print("📊 当前数据库状态:")
        
        total_records = EvaluationHistory.query.count()
        human_modified = EvaluationHistory.query.filter(
            EvaluationHistory.is_human_modified == True
        ).count()
        ai_only = total_records - human_modified
        
        print(f"   总记录数: {total_records}")
        print(f"   人工修改记录: {human_modified}")
        print(f"   纯AI记录: {ai_only}")
        
        # 2. 检查重复记录
        print("\n🔍 重复记录检查:")
        
        all_records = EvaluationHistory.query.all()
        duplicate_groups = {}
        
        for record in all_records:
            key = f"{record.user_input}|||{record.model_answer}"
            if key not in duplicate_groups:
                duplicate_groups[key] = []
            duplicate_groups[key].append(record)
        
        duplicated_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
        
        if duplicated_groups:
            print(f"   ❌ 仍有 {len(duplicated_groups)} 组重复记录")
            for key, records in duplicated_groups.items():
                question = records[0].user_input[:30] + "..."
                print(f"     重复: {question} ({len(records)}条)")
            return False
        else:
            print("   ✅ 没有重复记录")
        
        # 3. 检查数据完整性
        print("\n📋 数据完整性检查:")
        
        # 检查必要字段
        missing_fields = []
        for record in all_records:
            if not record.user_input:
                missing_fields.append(f"ID {record.id}: 缺少user_input")
            if not record.model_answer:
                missing_fields.append(f"ID {record.id}: 缺少model_answer")
            if record.total_score is None:
                missing_fields.append(f"ID {record.id}: 缺少total_score")
        
        if missing_fields:
            print(f"   ⚠️  发现 {len(missing_fields)} 个数据完整性问题:")
            for issue in missing_fields[:5]:  # 只显示前5个
                print(f"     {issue}")
            if len(missing_fields) > 5:
                print(f"     ... 还有 {len(missing_fields) - 5} 个问题")
        else:
            print("   ✅ 数据完整性良好")
        
        # 4. 检查评分分布
        print("\n📈 评分分布:")
        
        scores = [record.total_score for record in all_records if record.total_score is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"   平均分: {avg_score:.2f}")
            print(f"   最高分: {max_score}")
            print(f"   最低分: {min_score}")
            
            # 分数分布
            excellent = len([s for s in scores if s >= 8])
            good = len([s for s in scores if 6 <= s < 8])
            fair = len([s for s in scores if 4 <= s < 6])
            poor = len([s for s in scores if s < 4])
            
            print(f"   优秀(8-10分): {excellent}条 ({excellent/len(scores)*100:.1f}%)")
            print(f"   良好(6-8分): {good}条 ({good/len(scores)*100:.1f}%)")
            print(f"   一般(4-6分): {fair}条 ({fair/len(scores)*100:.1f}%)")
            print(f"   需改进(<4分): {poor}条 ({poor/len(scores)*100:.1f}%)")
        
        return True

def verify_frontend_fix():
    """验证前端修复"""
    print("\n🔧 前端修复验证:")
    
    frontend_file = '../frontend/src/components/EvaluationForm.js'
    if not os.path.exists(frontend_file):
        print("   ❌ 前端文件不存在")
        return False
    
    with open(frontend_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查防重复机制
    checks = [
        ('humanEvaluationSubmitting', '提交状态跟踪'),
        ('lastSubmissionTime', '时间间隔检查'),
        ('3000', '3秒防重复间隔'),
        ('正在提交中，请勿重复点击', '重复提交提示'),
        ('disabled: humanEvaluationSubmitting', '按钮禁用状态')
    ]
    
    missing_features = []
    for check, description in checks:
        if check not in content:
            missing_features.append(description)
    
    if missing_features:
        print(f"   ⚠️  缺少防重复功能: {', '.join(missing_features)}")
        return False
    else:
        print("   ✅ 前端防重复机制完整")
        return True

def verify_monitoring_tools():
    """验证监控工具"""
    print("\n📊 监控工具验证:")
    
    tools = [
        ('duplicate_monitoring_dashboard.py', '监控仪表板'),
        ('DUPLICATE_RECORDS_SOLUTION_REPORT.md', '解决方案报告'),
        ('fix_duplicate_records.py', '修复工具'),
        ('debug_duplicate_records.py', '调试工具')
    ]
    
    available_tools = []
    missing_tools = []
    
    for tool, description in tools:
        if os.path.exists(tool):
            available_tools.append(description)
        else:
            missing_tools.append(description)
    
    print(f"   ✅ 可用工具: {', '.join(available_tools)}")
    if missing_tools:
        print(f"   ⚠️  缺少工具: {', '.join(missing_tools)}")
    
    return len(missing_tools) == 0

def main():
    """主验证函数"""
    print("🎯 重复记录问题修复验证")
    print("=" * 60)
    
    # 验证各个方面
    db_ok = verify_duplicate_fix()
    frontend_ok = verify_frontend_fix()
    tools_ok = verify_monitoring_tools()
    
    print("\n" + "=" * 60)
    print("📋 验证结果汇总:")
    print(f"   数据库清理: {'✅ 通过' if db_ok else '❌ 失败'}")
    print(f"   前端防重复: {'✅ 通过' if frontend_ok else '❌ 失败'}")
    print(f"   监控工具: {'✅ 通过' if tools_ok else '❌ 失败'}")
    
    if db_ok and frontend_ok and tools_ok:
        print("\n🎉 恭喜！重复记录问题已彻底解决！")
        print("\n✅ 系统现在可以正常使用:")
        print("   - AI评估 → 创建1条记录")
        print("   - 人工评估 → 更新同一条记录") 
        print("   - 防重复提交保护机制已启用")
        print("   - 实时监控工具可用")
        
        print("\n🚀 使用建议:")
        print("   - 定期运行监控: python duplicate_monitoring_dashboard.py")
        print("   - 如有问题调试: python debug_duplicate_records.py")
        print("   - 查看详细报告: cat DUPLICATE_RECORDS_SOLUTION_REPORT.md")
        
        return True
    else:
        print("\n⚠️  修复验证未完全通过，请检查失败项目")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1) 