# 云端部署路由冲突问题修复指南

## 问题描述

在云端环境启动后端服务时出现以下错误：

```
AssertionError: View function mapping is overwriting an existing endpoint function: save_evaluation_history
```

这个错误发生在 `app.py` 第 500 行，提示 Flask 路由注册时发现重复的端点函数。

## 问题根因分析

### 1. 路由冲突原因
- **修复脚本冲突**：项目中存在多个修复脚本（`quick_fix_405.py`、`fix_remote_evaluation_issues.py`）
- **函数名重复**：这些脚本都尝试添加同名的 `save_evaluation_history` 函数
- **环境差异**：本地环境没有执行修复脚本，云端环境执行了导致冲突

### 2. 缺失的 POST 路由
- 当前 `app.py` 只有 `/api/evaluation-history` 的 GET、DELETE、PUT 路由
- 缺少 POST 路由导致前端保存评估记录时出现 405 错误

## 解决方案

### 步骤 1：清理冲突的修复脚本

在后端目录执行：

```bash
cd backend
python cleanup_fix_scripts.py
```

这个脚本会：
- 备份冲突的修复脚本到 `backup_fix_scripts/` 目录
- 删除可能导致路由冲突的文件
- 验证当前路由配置

### 步骤 2：验证路由修复

执行清理脚本后，`app.py` 现在包含以下评估历史路由：

```python
# GET - 获取评估历史记录（分页）
@app.route('/api/evaluation-history', methods=['GET'])
def get_evaluation_history():

# POST - 保存评估历史记录（已修复）
@app.route('/api/evaluation-history', methods=['POST'])
def create_evaluation_history():

# GET - 根据ID获取单个评估记录
@app.route('/api/evaluation-history/<int:history_id>', methods=['GET'])
def get_evaluation_by_id(history_id):

# DELETE - 删除评估记录
@app.route('/api/evaluation-history/<int:history_id>', methods=['DELETE'])
def delete_evaluation(history_id):

# PUT - 更新人工评估结果
@app.route('/api/evaluation-history/<int:history_id>/human-evaluation', methods=['PUT'])
def update_human_evaluation(history_id):
```

### 步骤 3：重启服务

```bash
# 激活虚拟环境
source venv/bin/activate

# 重启应用
python app.py
```

### 步骤 4：验证修复效果

1. **检查服务启动**：确认没有路由冲突错误
2. **测试 POST 接口**：
   ```bash
   curl -X POST http://localhost:5001/api/evaluation-history \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'
   ```
3. **前端功能测试**：验证评估保存功能正常工作

## 预防措施

### 1. 避免重复修复
- 不要同时运行多个修复脚本
- 在生产环境应用修复前先在测试环境验证

### 2. 版本控制管理
- 所有修复都应通过代码提交而非临时脚本
- 使用 Git 跟踪配置变更

### 3. 部署流程规范
```bash
# 标准云端部署流程
git clone <project-url>
cd intelligent-qa-evaluator/backend

# 环境准备
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 数据库初始化
python quick_init.py

# 配置同步（如需要）
cd scripts
python import_config_data.py --full-replace
cd ..

# 清理潜在冲突（如遇到问题）
python cleanup_fix_scripts.py

# 启动服务
python app.py
```

## 技术细节

### 路由注册机制
Flask 在启动时会检查所有 `@app.route` 装饰器，如果发现：
- 相同的路由路径
- 相同的 HTTP 方法
- 不同的函数名

就会抛出 `AssertionError`，提示端点函数覆盖冲突。

### 修复策略
1. **唯一函数名**：使用 `create_evaluation_history` 替代 `save_evaluation_history`
2. **路由整合**：在主 `app.py` 文件中统一管理所有路由
3. **脚本清理**：移除临时修复脚本，避免重复执行

## 联系支持

如果按照本指南操作后仍有问题，请提供：
- 完整的错误日志
- 执行步骤的输出结果
- 当前的路由配置信息

---

**修复完成后，系统将支持完整的评估功能，包括：**
- ✅ AI 自动评估
- ✅ 人工评估修正
- ✅ 历史记录管理
- ✅ 配置数据同步 