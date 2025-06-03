#!/usr/bin/env python3
"""
最终重复记录修复方案
根据问题分析，提供彻底的解决方案
"""

import json
import os

def analyze_problem():
    """分析问题根源"""
    print("🔍 重复记录问题分析")
    print("=" * 50)
    
    print("📋 问题描述:")
    print("   用户在进行人工评估时，系统创建了两条历史记录")
    print("   - 第1条：AI评估完成时自动创建")
    print("   - 第2条：人工评估时意外创建")
    
    print("\n🔬 根本原因:")
    print("   1. 前端evaluationService.evaluate()会自动保存评估历史")
    print("   2. 人工评估应该只更新现有记录，但可能触发了新记录创建")
    print("   3. 缺乏重复检测机制")

def create_backend_fix():
    """创建后端修复方案"""
    print("\n🔧 生成后端修复方案...")
    
    backend_fix = '''
# 后端修复：在evaluation_history_service.py的save_evaluation_result方法开头添加重复检测

def save_evaluation_result(self, evaluation_data, classification_result=None):
    """
    保存评估结果到历史记录（带重复检测）
    """
    try:
        # ====== 新增：重复记录检测 ======
        user_input = evaluation_data.get('user_input')
        model_answer = evaluation_data.get('model_answer')
        
        if user_input and model_answer:
            # 检查最近5分钟内是否有相同内容的记录
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
        # ====== 重复检测结束 ======
        
        # 继续原有的保存逻辑...
        history = EvaluationHistory(
            user_input=evaluation_data.get('user_input'),
            model_answer=evaluation_data.get('model_answer'),
            reference_answer=evaluation_data.get('reference_answer'),
            question_time=evaluation_data.get('question_time'),
            evaluation_criteria=evaluation_data.get('evaluation_criteria') or evaluation_data.get('evaluation_criteria_used'),
            total_score=evaluation_data.get('total_score') or evaluation_data.get('score', 0.0),
            dimensions_json=json.dumps(evaluation_data.get('dimensions', {}), ensure_ascii=False),
            reasoning=evaluation_data.get('reasoning'),
            classification_level1=classification_result.get('level1') if classification_result else None,
            classification_level2=classification_result.get('level2') if classification_result else None,
            classification_level3=classification_result.get('level3') if classification_result else None,
            evaluation_time_seconds=evaluation_data.get('evaluation_time_seconds', 0),
            model_used=evaluation_data.get('model_used', 'unknown'),
            raw_response=evaluation_data.get('raw_response'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(history)
        db.session.commit()
        
        self.logger.info(f"成功保存评估历史记录，ID: {history.id}")
        
        return {
            'success': True,
            'message': '评估历史保存成功',
            'history_id': history.id,
            'data': history.to_dict()
        }
        
    except SQLAlchemyError as e:
        self.logger.error(f"保存评估历史失败: {str(e)}")
        db.session.rollback()
        return {
            'success': False,
            'message': f'保存评估历史失败: {str(e)}'
        }
'''
    
    with open('backend_duplicate_fix.txt', 'w', encoding='utf-8') as f:
        f.write(backend_fix)
    
    print("   ✅ backend_duplicate_fix.txt 已生成")

def create_frontend_fix():
    """创建前端修复方案"""
    print("\n🔧 生成前端修复方案...")
    
    frontend_fix = '''
// 前端修复1: 修改evaluationService.js的saveEvaluationHistory方法

async saveEvaluationHistory(historyData) {
  try {
    // ====== 新增：重复检测 ======
    console.log('保存评估历史前检查重复...', historyData);
    
    // 检查是否是重复保存请求
    const currentTime = Date.now();
    const requestKey = `${historyData.user_input}|||${historyData.model_answer}`;
    
    // 使用内存缓存防止短时间内重复请求
    if (!this._recentSaves) {
      this._recentSaves = new Map();
    }
    
    const lastSaveTime = this._recentSaves.get(requestKey);
    if (lastSaveTime && (currentTime - lastSaveTime) < 30000) { // 30秒内
      console.log('检测到30秒内重复保存请求，跳过');
      return { success: true, message: '跳过重复保存', is_duplicate: true };
    }
    
    // 记录本次保存时间
    this._recentSaves.set(requestKey, currentTime);
    
    // 清理过期的缓存（保留最近5分钟）
    const fiveMinutesAgo = currentTime - 300000;
    for (const [key, time] of this._recentSaves.entries()) {
      if (time < fiveMinutesAgo) {
        this._recentSaves.delete(key);
      }
    }
    // ====== 重复检测结束 ======
    
    const response = await this.api.post('/evaluation-history', historyData);
    console.log('评估历史保存成功');
    return response.data;
  } catch (error) {
    console.error('保存评估历史失败:', error);
    throw new Error('保存评估历史失败');
  }
}

// 前端修复2: 修改EvaluationForm.js的handleHumanEvaluationSubmit方法
// 确保人工评估只调用更新接口，不触发新记录创建

const handleHumanEvaluationSubmit = async () => {
  // 防重复提交检查
  const now = Date.now();
  if (humanEvaluationSubmitting) {
    message.warning('正在提交中，请勿重复点击');
    return;
  }
  
  if (now - lastSubmissionTime < 3000) {
    message.warning('提交过于频繁，请稍后再试');
    return;
  }
  
  try {
    setHumanEvaluationSubmitting(true);
    setLastSubmissionTime(now);
    setHumanEvaluationLoading(true);
    
    const values = await humanForm.validateFields();
    
    // 构建人工评估数据
    const humanData = {
      human_total_score: values.human_total_score,
      human_reasoning: values.human_reasoning,
      evaluator_name: values.evaluator_name || '评估专家'
    };
    
    // 收集各维度分数
    const humanDimensions = {};
    Object.keys(values).forEach(key => {
      if (key.startsWith('dimension_')) {
        const dimensionKey = key.replace('dimension_', '');
        humanDimensions[dimensionKey] = values[key];
      }
    });
    
    if (Object.keys(humanDimensions).length > 0) {
      humanData.human_dimensions = humanDimensions;
    }
    
    // ====== 关键修复：只调用PUT更新接口，绝不创建新记录 ======
    console.log('提交人工评估数据（仅更新现有记录）:', humanData);
    console.log('目标记录ID:', currentHistoryId);
    
    if (!currentHistoryId) {
      throw new Error('无法获取评估记录ID，请重新评估');
    }
    
    const response = await api.put(`/api/evaluation-history/${currentHistoryId}/human-evaluation`, humanData);
    
    if (response.data.success) {
      message.success('人工评估保存成功');
      setHumanEvaluationVisible(false);
      
      // ====== 删除：不再尝试更新本地状态 ======
      // 人工评估成功后，数据已保存到数据库
      // 用户可以重新评估查看更新后的结果
      
    } else {
      message.error(response.data.message || '人工评估保存失败');
    }
    
  } catch (error) {
    console.error('人工评估提交失败:', error);
    message.error('人工评估提交失败，请重试');
  } finally {
    setHumanEvaluationLoading(false);
    setHumanEvaluationSubmitting(false);
  }
};
'''
    
    with open('frontend_duplicate_fix.txt', 'w', encoding='utf-8') as f:
        f.write(frontend_fix)
    
    print("   ✅ frontend_duplicate_fix.txt 已生成")

def create_cleanup_script():
    """创建清理重复记录的脚本"""
    print("\n🧹 生成重复记录清理脚本...")
    
    cleanup_script = '''#!/usr/bin/env python3
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
'''
    
    with open('cleanup_duplicates.py', 'w', encoding='utf-8') as f:
        f.write(cleanup_script)
    
    print("   ✅ cleanup_duplicates.py 已生成")

def create_deployment_guide():
    """创建部署指南"""
    print("\n📋 生成部署指南...")
    
    guide = '''# 重复记录问题修复部署指南

## 🎯 修复目标
彻底解决人工评估时创建重复记录的问题

## 📋 修复步骤

### 1. 后端修复
将 `backend_duplicate_fix.txt` 中的代码应用到 `backend/services/evaluation_history_service.py`:
- 在 `save_evaluation_result` 方法开头添加重复检测逻辑
- 检查最近5分钟内是否有相同内容的记录

### 2. 前端修复
将 `frontend_duplicate_fix.txt` 中的代码应用到前端文件:
- 修改 `frontend/src/services/evaluationService.js` 的 `saveEvaluationHistory` 方法
- 修改 `frontend/src/components/EvaluationForm.js` 的 `handleHumanEvaluationSubmit` 方法

### 3. 清理现有重复记录
运行清理脚本:
```bash
cd backend
python cleanup_duplicates.py
```

### 4. 重启服务
```bash
# 重启后端
cd backend && python app.py

# 重启前端
cd frontend && npm start
```

### 5. 验证修复效果
运行验证脚本:
```bash
cd backend
python duplicate_monitoring_dashboard.py
```

## 🔍 修复原理

### 后端防护
- 在保存评估结果前检查重复
- 5分钟内相同内容直接返回现有记录
- 避免数据库层面的重复创建

### 前端防护
- 内存缓存防止30秒内重复保存
- 人工评估只调用更新接口，不创建新记录
- 完善的防重复提交机制

### 清理策略
- 优先保留有人工评估的记录
- 合并人工评估数据到保留记录
- 删除多余的重复记录

## ✅ 验证标准
修复成功的标志：
- 重复记录数量为0
- AI评估+人工评估只产生1条记录
- 前端界面反应正常

## 🚨 注意事项
- 备份数据库后再执行清理脚本
- 修复后建议进行完整的功能测试
- 监控系统运行一段时间确保稳定
'''
    
    with open('DEPLOYMENT_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("   ✅ DEPLOYMENT_GUIDE.md 已生成")

def main():
    """主函数"""
    analyze_problem()
    create_backend_fix()
    create_frontend_fix()
    create_cleanup_script()
    create_deployment_guide()
    
    print("\n" + "=" * 50)
    print("🎉 修复方案生成完成！")
    print("\n📄 生成的文件:")
    print("   - backend_duplicate_fix.txt: 后端修复代码")
    print("   - frontend_duplicate_fix.txt: 前端修复代码") 
    print("   - cleanup_duplicates.py: 重复记录清理脚本")
    print("   - DEPLOYMENT_GUIDE.md: 详细部署指南")
    
    print("\n🚀 下一步:")
    print("1. 按照 DEPLOYMENT_GUIDE.md 应用修复")
    print("2. 运行清理脚本删除现有重复记录")
    print("3. 重启服务并验证修复效果")

if __name__ == '__main__':
    main() 