# 🚨 远端评估问题紧急修复指令

## 问题现象
- ✅ 评估功能能正常完成，显示分数
- ❌ 浏览器控制台报错：`POST /api/evaluation-history 405 (Method Not Allowed)`
- ❌ 点击"人工评估"时提示："评估记录不存在"

## ⚡ 一键修复（推荐）

### 步骤1：更新代码
```bash
# 拉取最新代码
git pull origin main
```

### 步骤2：修复405错误
```bash
# 进入后端目录
cd backend

# 运行快速修复脚本
python quick_fix_405.py
```

### 步骤3：重启服务
```bash
# 停止当前Flask服务（Ctrl+C）
# 然后重新启动
python app.py
```

## 🔍 验证修复效果

1. **测试评估保存**：
   - 完成一次问答评估
   - 打开浏览器开发者工具（F12）
   - 查看Network标签，确认没有405错误

2. **测试人工评估**：
   - 进入"评估历史"页面
   - 选择任意一条记录
   - 点击"人工评估"按钮
   - 确认能正常打开评估弹窗

## 🛠️ 手动修复（备选）

如果自动修复失败，请手动在 `backend/app.py` 文件中添加以下代码：

**插入位置**：在第534行 `get_evaluation_statistics()` 函数之后添加：

```python
@app.route('/api/evaluation-history', methods=['POST'])
def post_evaluation_history():
    """保存评估历史记录（兼容前端重复保存调用）"""
    try:
        logger.info("前端尝试保存评估历史记录")
        
        data = request.get_json()
        
        # 检查是否已经存在相同的记录（避免重复）
        if data.get('user_input') and data.get('model_answer'):
            from models.classification import EvaluationHistory
            from datetime import datetime, timedelta
            
            # 查找最近2分钟内的相同记录
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            existing = EvaluationHistory.query.filter(
                EvaluationHistory.user_input == data['user_input'],
                EvaluationHistory.model_answer == data['model_answer'],
                EvaluationHistory.created_at >= two_minutes_ago
            ).first()
            
            if existing:
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
```

## ❗ 注意事项

1. **确保备份**：修复脚本会自动备份原文件为 `app.py.backup_405fix`
2. **重启必需**：添加路由后必须重启Flask应用才能生效
3. **检查日志**：如果仍有问题，查看Flask应用的输出日志

## 📞 如果问题仍然存在

请提供以下信息：
1. 修复脚本的完整输出
2. Flask应用重启后的日志
3. 浏览器开发者工具中的Network请求详情

---

**修复时间预估**：2-3分钟
**适用版本**：v2.3.1及以后版本 