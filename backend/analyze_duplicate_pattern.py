#!/usr/bin/env python3
"""
分析重复记录模式并提供修复方案
"""

import json
from datetime import datetime, timedelta
from app import app
from models.classification import EvaluationHistory

def analyze_duplicate_pattern():
    """分析重复记录的具体模式"""
    print("🔍 深度分析重复记录模式...")
    
    with app.app_context():
        # 获取所有记录
        all_records = EvaluationHistory.query.order_by(EvaluationHistory.created_at.desc()).all()
        
        print(f"📊 总记录数: {len(all_records)}")
        
        # 按问题内容分组
        content_groups = {}
        for record in all_records:
            key = f"{record.user_input}|||{record.model_answer}"
            if key not in content_groups:
                content_groups[key] = []
            content_groups[key].append(record)
        
        # 找出重复组
        duplicate_groups = {k: v for k, v in content_groups.items() if len(v) > 1}
        
        if not duplicate_groups:
            print("✅ 未发现重复记录")
            return
        
        print(f"\n🚨 发现 {len(duplicate_groups)} 组重复记录:")
        
        for i, (key, records) in enumerate(duplicate_groups.items(), 1):
            question = records[0].user_input[:40] + "..." if len(records[0].user_input) > 40 else records[0].user_input
            print(f"\n📋 组 {i}: {question}")
            print(f"   重复记录数: {len(records)}")
            
            # 详细分析每条记录
            for j, record in enumerate(records):
                human_flag = "👨‍💼" if record.is_human_modified else "🤖"
                ai_score = record.total_score if record.total_score is not None else "无"
                human_score = record.human_total_score if record.human_total_score is not None else "无"
                
                print(f"   记录 {j+1}: ID {record.id} {human_flag}")
                print(f"     创建时间: {record.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     更新时间: {record.updated_at.strftime('%Y-%m-%d %H:%M:%S') if record.updated_at else '无'}")
                print(f"     AI分数: {ai_score}, 人工分数: {human_score}")
                print(f"     人工评估者: {record.human_evaluation_by or '无'}")
            
            # 分析时间间隔
            if len(records) >= 2:
                times = [(r.created_at, r.id) for r in records]
                times.sort()  # 按时间排序
                
                print(f"   📅 时间分析:")
                for k in range(len(times) - 1):
                    time_diff = (times[k+1][0] - times[k][0]).total_seconds()
                    print(f"     ID {times[k][1]} → ID {times[k+1][1]}: 间隔 {time_diff:.1f}秒")
                
                # 分析模式
                has_ai_only = any(not r.is_human_modified for r in records)
                has_human_modified = any(r.is_human_modified for r in records)
                
                print(f"   🔍 模式分析:")
                print(f"     包含纯AI记录: {'是' if has_ai_only else '否'}")
                print(f"     包含人工修改: {'是' if has_human_modified else '否'}")
                
                if has_ai_only and has_human_modified:
                    print(f"     ⚠️  疑似人工评估时重复创建了记录！")

def identify_root_cause():
    """识别根本原因"""
    print("\n🔬 根本原因分析:")
    
    # 检查最近的重复记录模式
    with app.app_context():
        # 获取最近1小时的记录
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_records = EvaluationHistory.query.filter(
            EvaluationHistory.created_at >= one_hour_ago
        ).order_by(EvaluationHistory.created_at.desc()).all()
        
        if not recent_records:
            print("   📊 最近1小时无新记录")
            return
        
        print(f"   📊 最近1小时记录数: {len(recent_records)}")
        
        # 分析最近记录的模式
        for record in recent_records:
            human_flag = "👨‍💼" if record.is_human_modified else "🤖"
            print(f"   - ID {record.id} {human_flag} {record.created_at.strftime('%H:%M:%S')} {record.user_input[:30]}...")

def provide_targeted_fix():
    """提供针对性修复方案"""
    print("\n🔧 针对性修复方案:")
    
    print("根据分析，重复记录问题的可能原因：")
    print("1. 前端人工评估时意外触发了新记录创建")
    print("2. Redux状态管理导致的重复提交")
    print("3. 网络重试机制导致的重复请求")
    
    print("\n📋 建议的修复步骤：")
    
    # 生成修复补丁
    frontend_fix = """
// 修复方案1: 修改前端evaluationService.js
// 在saveEvaluationHistory方法中添加重复检测

async saveEvaluationHistory(historyData) {
  try {
    // 添加重复检测：检查最近5分钟内是否有相同的记录
    const recentCheck = await this.api.get('/evaluation-history', {
      params: {
        user_input: historyData.user_input,
        model_answer: historyData.model_answer,
        recent_minutes: 5
      }
    });
    
    if (recentCheck.data && recentCheck.data.data && recentCheck.data.data.length > 0) {
      console.log('检测到重复记录，跳过保存');
      return recentCheck.data.data[0]; // 返回现有记录
    }
    
    const response = await this.api.post('/evaluation-history', historyData);
    return response.data;
  } catch (error) {
    console.error('保存评估历史失败:', error);
    throw new Error('保存评估历史失败');
  }
}
"""
    
    backend_fix = """
# 修复方案2: 修改后端evaluation_history_service.py
# 在save_evaluation_result方法开头添加重复检测

def save_evaluation_result(self, evaluation_data, classification_result=None):
    try:
        // 重复检测：检查最近5分钟内是否有相同内容的记录
        user_input = evaluation_data.get('user_input')
        model_answer = evaluation_data.get('model_answer')
        
        if user_input and model_answer:
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            existing_record = EvaluationHistory.query.filter(
                EvaluationHistory.user_input == user_input,
                EvaluationHistory.model_answer == model_answer,
                EvaluationHistory.created_at >= five_minutes_ago
            ).first()
            
            if existing_record:
                self.logger.warning(f"检测到重复记录，返回现有记录ID: {existing_record.id}")
                return {
                    'success': True,
                    'message': '检测到重复记录，返回现有记录',
                    'history_id': existing_record.id,
                    'data': existing_record.to_dict(),
                    'is_duplicate': True
                }
        
        // 继续原有保存逻辑...
"""
    
    print("1. 前端修复：添加重复检测机制")
    print("2. 后端修复：服务层重复检测")
    print("3. 清理现有重复记录")
    
    with open('frontend_duplicate_fix.js', 'w') as f:
        f.write(frontend_fix)
    
    with open('backend_duplicate_fix.py', 'w') as f:
        f.write(backend_fix)
    
    print("\n📄 修复代码已生成:")
    print("   - frontend_duplicate_fix.js")
    print("   - backend_duplicate_fix.py")

def main():
    """主函数"""
    print("🔍 重复记录模式分析工具")
    print("=" * 50)
    
    analyze_duplicate_pattern()
    identify_root_cause()
    provide_targeted_fix()
    
    print("\n" + "=" * 50)
    print("🎯 分析完成！请查看生成的修复代码文件")

if __name__ == '__main__':
    main() 