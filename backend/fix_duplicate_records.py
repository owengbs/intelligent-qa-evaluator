#!/usr/bin/env python3
"""
修复重复记录问题
1. 清理现有重复记录
2. 添加前端防重复提交机制
3. 后端添加重复记录清理
"""

import json
from datetime import datetime, timedelta
from flask import Flask
from app import app, evaluation_history_service
from models.classification import db, EvaluationHistory

def analyze_and_clean_duplicates():
    """分析并清理重复记录"""
    print("🧹 清理重复记录...")
    
    with app.app_context():
        # 找出所有重复的记录组
        all_records = EvaluationHistory.query.all()
        duplicate_groups = {}
        
        # 按问题和答案分组
        for record in all_records:
            key = f"{record.user_input}|||{record.model_answer}"
            if key not in duplicate_groups:
                duplicate_groups[key] = []
            duplicate_groups[key].append(record)
        
        # 找出有重复的组
        duplicated_groups = {k: v for k, v in duplicate_groups.items() if len(v) > 1}
        
        if not duplicated_groups:
            print("✅ 没有发现重复记录")
            return
        
        print(f"🚨 发现 {len(duplicated_groups)} 组重复记录，总计 {sum(len(group) for group in duplicated_groups.values())} 条记录")
        
        cleaned_count = 0
        preserved_count = 0
        
        for key, records in duplicated_groups.items():
            question = records[0].user_input[:50] + "..." if len(records[0].user_input) > 50 else records[0].user_input
            print(f"\n📝 处理重复组: {question}")
            print(f"   重复记录数: {len(records)}")
            
            # 排序：优先保留人工修改的记录，然后按ID排序
            records.sort(key=lambda x: (not x.is_human_modified, x.id))
            
            # 保留第一条（最优先的）记录
            keep_record = records[0]
            delete_records = records[1:]
            
            print(f"   保留记录: ID={keep_record.id}, 人工修改={keep_record.is_human_modified}")
            
            for delete_record in delete_records:
                print(f"   删除记录: ID={delete_record.id}, 人工修改={delete_record.is_human_modified}")
                
                # 如果要删除的记录有人工评估数据，合并到保留的记录中
                if delete_record.is_human_modified and not keep_record.is_human_modified:
                    print(f"     ⚠️  要删除的记录有人工评估，合并到保留记录中")
                    keep_record.human_total_score = delete_record.human_total_score
                    keep_record.human_dimensions_json = delete_record.human_dimensions_json
                    keep_record.human_reasoning = delete_record.human_reasoning
                    keep_record.human_evaluation_by = delete_record.human_evaluation_by
                    keep_record.human_evaluation_time = delete_record.human_evaluation_time
                    keep_record.is_human_modified = True
                    keep_record.updated_at = datetime.utcnow()
                
                db.session.delete(delete_record)
                cleaned_count += 1
            
            preserved_count += 1
        
        try:
            db.session.commit()
            print(f"\n✅ 清理完成:")
            print(f"   - 保留记录: {preserved_count} 条")
            print(f"   - 删除记录: {cleaned_count} 条")
            print(f"   - 总计节省: {cleaned_count} 条记录")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 清理失败: {e}")

def add_frontend_duplicate_prevention():
    """为前端添加防重复提交机制"""
    print("\n🔒 生成前端防重复提交补丁...")
    
    frontend_patch = """
// 前端防重复提交机制补丁
// 文件位置: frontend/src/components/EvaluationForm.js

// 1. 在组件状态中添加提交状态跟踪
const [humanEvaluationSubmitting, setHumanEvaluationSubmitting] = useState(false);
const [lastSubmissionTime, setLastSubmissionTime] = useState(0);

// 2. 修改 handleHumanEvaluationSubmit 方法
const handleHumanEvaluationSubmit = async () => {
  // 防重复提交检查
  const now = Date.now();
  if (humanEvaluationSubmitting) {
    message.warning('正在提交中，请勿重复点击');
    return;
  }
  
  if (now - lastSubmissionTime < 3000) { // 3秒内不允许重复提交
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
    
    // 调用API更新人工评估 - 只调用一次，使用PUT方法
    console.log('提交人工评估数据:', humanData);
    const response = await api.put(`/api/evaluation-history/${currentHistoryId}/human-evaluation`, humanData);
    
    if (response.data.success) {
      message.success('人工评估保存成功');
      setHumanEvaluationVisible(false);
      
      // 更新当前显示的结果
      setResult(prevResult => ({
        ...prevResult,
        human_total_score: humanData.human_total_score,
        human_reasoning: humanData.human_reasoning,
        is_human_modified: true
      }));
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

// 3. 修改提交按钮，添加禁用状态
// 在 renderHumanEvaluationModal 中的 Modal 配置
<Modal
  title={...}
  open={humanEvaluationVisible}
  onCancel={() => setHumanEvaluationVisible(false)}
  onOk={handleHumanEvaluationSubmit}
  okText="保存评估"
  cancelText="取消"
  width={800}
  confirmLoading={humanEvaluationLoading}
  okButtonProps={{
    disabled: humanEvaluationSubmitting, // 添加禁用状态
    loading: humanEvaluationLoading
  }}
>
"""
    
    with open('frontend_duplicate_prevention_patch.txt', 'w', encoding='utf-8') as f:
        f.write(frontend_patch)
    
    print("📄 前端补丁已生成: frontend_duplicate_prevention_patch.txt")

def add_backend_duplicate_detection():
    """为后端添加重复检测逻辑"""
    print("\n🔍 生成后端重复检测补丁...")
    
    backend_patch = """
# 后端重复检测机制补丁
# 文件位置: backend/services/evaluation_history_service.py

# 在 save_evaluation_result 方法开始处添加重复检测
def save_evaluation_result(self, evaluation_data, classification_result=None):
    \"\"\"
    保存评估结果到历史记录（带重复检测）
    \"\"\"
    try:
        # 重复检测：检查是否已存在相同的问题和答案
        user_input = evaluation_data.get('user_input')
        model_answer = evaluation_data.get('model_answer')
        
        if user_input and model_answer:
            # 查找最近5分钟内的相同记录
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
                    'message': '评估历史已存在（防重复）',
                    'history_id': existing_record.id,
                    'data': existing_record.to_dict(),
                    'is_duplicate': True
                }
        
        # 原有的保存逻辑...
        # [保持现有代码不变]
        
    except SQLAlchemyError as e:
        # 错误处理逻辑...
"""
    
    # 后端API接口添加重复检测
    api_patch = """
# 文件位置: backend/app.py
# 在 create_evaluation_history 路由中添加重复检测

@app.route('/api/evaluation-history', methods=['POST'])
def create_evaluation_history():
    \"\"\"创建评估历史记录（带防重复机制）\"\"\"
    try:
        logger.info("收到创建评估历史请求")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': '缺少评估数据'}), 400
        
        # 添加请求指纹检测
        request_fingerprint = f"{data.get('user_input', '')}|{data.get('model_answer', '')}|{data.get('total_score', 0)}"
        
        # 检查Redis缓存中是否有相同请求（如果使用Redis）
        # 或者检查数据库中最近的记录
        
        result = evaluation_history_service.save_evaluation_result(data)
        
        if result.get('is_duplicate'):
            logger.info(f"防重复检测：返回现有记录 {result.get('history_id')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"创建评估历史失败: {str(e)}")
        return jsonify({'error': f'创建评估历史失败: {str(e)}'}), 500
"""
    
    with open('backend_duplicate_detection_patch.txt', 'w', encoding='utf-8') as f:
        f.write(backend_patch + "\n\n" + api_patch)
    
    print("📄 后端补丁已生成: backend_duplicate_detection_patch.txt")

def create_monitoring_dashboard():
    """创建重复记录监控仪表板"""
    print("\n📊 创建监控仪表板...")
    
    dashboard_script = """#!/usr/bin/env python3
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
        
        print(f"\\n⏰ 最近24小时:")
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
        
        print(f"\\n📅 最近24小时创建频率:")
        for hour in sorted(hour_stats.keys()):
            print(f"   {hour:02d}:00-{hour:02d}:59: {hour_stats[hour]} 条记录")

if __name__ == '__main__':
    show_duplicate_dashboard()
"""
    
    with open('duplicate_monitoring_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(dashboard_script)
    
    print("📄 监控仪表板已创建: duplicate_monitoring_dashboard.py")

def create_fix_summary():
    """创建修复总结"""
    print("\n📋 修复总结")
    print("=" * 50)
    
    summary = """
# 重复记录问题修复总结

## 🔍 问题分析
1. **重复记录确实存在**：发现多组重复的评估记录
2. **后端逻辑正常**：人工评估更新机制工作正常，不会创建新记录
3. **可能原因**：前端重复提交、网络重试、用户操作导致

## 🛠️ 修复方案

### 1. 数据清理 ✅
- 运行 `python fix_duplicate_records.py` 自动清理重复记录
- 优先保留有人工评估的记录
- 合并人工评估数据到保留的记录中

### 2. 前端防重复机制
- 添加提交状态跟踪 (`humanEvaluationSubmitting`)
- 实现3秒防重复间隔
- 按钮禁用状态防止重复点击
- 应用补丁：`frontend_duplicate_prevention_patch.txt`

### 3. 后端重复检测
- 5分钟内相同内容检测
- 返回现有记录而非创建新记录
- API级别的防重复机制
- 应用补丁：`backend_duplicate_detection_patch.txt`

### 4. 监控工具
- `duplicate_monitoring_dashboard.py`：实时监控重复情况
- `monitor_records.py`：手动测试监控

## 📋 部署步骤

1. **立即清理现有重复记录**：
   ```bash
   python fix_duplicate_records.py
   ```

2. **应用前端补丁**：
   - 参考 `frontend_duplicate_prevention_patch.txt`
   - 修改 `frontend/src/components/EvaluationForm.js`

3. **应用后端补丁**：
   - 参考 `backend_duplicate_detection_patch.txt`
   - 修改相关后端文件

4. **部署后验证**：
   ```bash
   python duplicate_monitoring_dashboard.py
   python monitor_records.py
   ```

## 🎯 预期效果
- ✅ 消除现有重复记录
- ✅ 防止新的重复记录产生
- ✅ 提升系统数据质量
- ✅ 改善用户体验

## 📊 监控指标
- 总记录数量变化
- 重复记录检测率
- 用户重复提交拦截率
- 系统性能影响（应该很小）
"""
    
    with open('DUPLICATE_RECORDS_FIX_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("📄 修复总结已创建: DUPLICATE_RECORDS_FIX_SUMMARY.md")

def main():
    """主函数"""
    print("🔧 重复记录修复工具")
    print("=" * 60)
    
    # 1. 分析并清理现有重复记录
    analyze_and_clean_duplicates()
    
    # 2. 生成前端防重复机制
    add_frontend_duplicate_prevention()
    
    # 3. 生成后端重复检测逻辑
    add_backend_duplicate_detection()
    
    # 4. 创建监控工具
    create_monitoring_dashboard()
    
    # 5. 创建修复总结
    create_fix_summary()
    
    print("\n" + "=" * 60)
    print("🎉 重复记录修复完成！")
    print("\n📋 生成的文件:")
    print("  - frontend_duplicate_prevention_patch.txt (前端补丁)")
    print("  - backend_duplicate_detection_patch.txt (后端补丁)")
    print("  - duplicate_monitoring_dashboard.py (监控仪表板)")
    print("  - DUPLICATE_RECORDS_FIX_SUMMARY.md (修复总结)")
    
    print("\n🚀 下一步操作:")
    print("1. 应用前端和后端补丁")
    print("2. 重启前后端服务")
    print("3. 运行监控工具验证效果")
    print("4. 进行完整的评估测试")

if __name__ == '__main__':
    main() 