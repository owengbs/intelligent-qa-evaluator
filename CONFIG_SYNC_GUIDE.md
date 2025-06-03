# 配置数据同步指南

## 🎯 目的

本系统将**配置数据**（分类标准、评估标准）与**用户数据**（评估历史）分离：
- ✅ 配置数据：通过JSON文件进行版本控制和团队同步
- ❌ 用户数据：不进行版本控制，每个环境独立维护

## 🆕 全量同步 vs 增量同步

### 🔄 全量同步（推荐）
- **特点**：完全替换现有配置数据，确保团队间配置完全一致
- **适用场景**：团队协作、配置标准化、解决配置不一致问题
- **安全性**：自动备份现有配置，支持恢复

### 📥 增量同步
- **特点**：只导入不存在的配置，不覆盖现有数据
- **适用场景**：个人使用、配置补充
- **限制**：无法同步删除的配置项，可能导致团队不一致

## 📤 导出本地配置数据

当您更新了分类标准或评估标准，需要同步给团队时：

```bash
cd backend/scripts
python export_config_data.py
```

**导出特点**：
- 🔄 **全量导出**：包含所有配置数据（默认 + 用户添加）
- 📁 输出到 `backend/config_data/` 目录
- 🏷️ 标记为 `sync_mode: full_replace` 支持全量同步

生成文件：
- `classification_standards.json` - 分类标准
- `evaluation_standards.json` - 评估标准  
- `export_summary.json` - 导出摘要

## 📥 导入团队配置数据

### 🔄 全量替换导入（推荐）

确保与团队配置完全一致：

```bash
cd backend/scripts
python import_config_data.py --full-replace
```

**全量替换特点**：
- ✅ 自动备份现有配置
- 🧹 清除所有现有配置数据
- 📥 导入新的配置数据
- 🔄 确保配置完全一致
- 🛡️ 保护用户评估历史数据

### 📥 增量导入

只导入不存在的配置：

```bash
cd backend/scripts
python import_config_data.py
```

### 高级选项

```bash
# 指定配置目录
python import_config_data.py --config-dir ../config_data --full-replace

# 跳过备份（不推荐）
python import_config_data.py --full-replace --no-backup

# 查看帮助
python import_config_data.py --help
```

### 🆘 兼容性问题解决

如果导入脚本报错 `'Engine' object has no attribute 'execute'`，请使用以下方法之一：

#### 方法1：使用兼容版本脚本
最新版本的 `import_config_data.py` 已经修复了SQLAlchemy兼容性问题，支持新旧版本API。

#### 方法2：使用简化导入脚本
如果Flask应用初始化有问题，可以使用直接操作数据库的简化版本：

```bash
cd backend/scripts
python simple_import.py
```

## 🔄 团队协作流程

### 配置更新者（如：产品经理）
1. 在系统中更新分类标准或评估标准
2. 运行导出脚本：`python export_config_data.py`
3. 提交配置文件到Git：
   ```bash
   git add backend/config_data/
   git commit -m "feat: 更新评估标准配置（全量）"
   git push
   ```

### 配置使用者（如：开发人员）
1. 拉取最新代码：`git pull`
2. 全量导入配置：`python import_config_data.py --full-replace`
3. 系统自动同步配置到本地数据库

## 📊 同步模式对比

| 特性 | 全量同步 | 增量同步 |
|------|----------|----------|
| 配置一致性 | ✅ 完全一致 | ⚠️ 可能不一致 |
| 删除的配置 | ✅ 会同步删除 | ❌ 不会删除 |
| 修改的配置 | ✅ 会同步修改 | ❌ 不会修改 |
| 数据安全性 | ✅ 自动备份 | ✅ 保留原数据 |
| 团队协作 | ✅ 强烈推荐 | ❌ 不推荐 |
| 使用复杂度 | 🟡 中等 | 🟢 简单 |

## 📋 配置文件格式

### classification_standards.json
```json
{
  "export_time": "2025-06-03T10:00:00",
  "description": "分类标准配置数据 - 全量同步用于团队协作",
  "version": "2.3.0",
  "sync_mode": "full_replace",
  "count": 19,
  "data": [
    {
      "level1": "金融投资",
      "level1_definition": "与投资理财相关的问题",
      "level2": "选股",
      "level3": "基本面分析",
      "level3_definition": "基于公司财务数据的分析",
      "examples": "分析某公司的盈利能力...",
      "is_default": true
    }
  ]
}
```

### evaluation_standards.json
```json
{
  "export_time": "2025-06-03T10:00:00", 
  "description": "评估标准配置数据 - 全量同步用于团队协作",
  "version": "2.3.0",
  "sync_mode": "full_replace",
  "count": 28,
  "data": [
    {
      "level2_category": "选股",
      "dimension": "准确性",
      "reference_standard": "信息是否准确无误",
      "scoring_principle": "完全准确4分，轻微误差2分，重大错误0分",
      "max_score": 4,
      "is_default": true
    }
  ]
}
```

## ⚠️ 注意事项

### 数据安全
1. **用户数据保护**：只同步配置数据，用户评估历史绝不会泄露
2. **自动备份**：全量替换前自动备份现有配置
3. **权限控制**：配置导出/导入需要数据库写权限

### 同步建议
1. **推荐全量同步**：确保团队配置完全一致
2. **定期同步**：配置更新后及时同步给团队
3. **备份重要配置**：重要配置更新前建议先备份数据库

## 🛠️ 故障排除

### 导出失败
- 检查数据库连接是否正常
- 确保有读取权限

### 导入失败

#### SQLAlchemy API兼容性错误
**错误信息**：`'Engine' object has no attribute 'execute'`

**解决方案**：
1. 使用最新版本的 `import_config_data.py`，已支持新旧API兼容
2. 或使用简化版本：`python simple_import.py`

#### 数据库连接失败
**错误信息**：`数据库连接失败`

**解决方案**：
1. 确保数据库文件存在：`backend/data/qa_evaluator.db`
2. 检查文件权限是否可读写
3. 确保虚拟环境已激活

#### Flask应用初始化失败
**错误信息**：`应用上下文错误`

**解决方案**：
1. 检查依赖是否完整安装：`pip install -r requirements.txt`
2. 使用简化版导入脚本：`python simple_import.py`

#### 全量替换失败
**错误信息**：`清除现有配置失败`

**解决方案**：
1. 检查数据库文件权限
2. 确保没有其他程序占用数据库
3. 使用备份文件恢复：从自动生成的备份文件中恢复

### 配置不生效
- 重启应用服务
- 检查是否正确导入到目标数据库
- 确认应用读取的是正确的数据库文件

## 🚀 快速开始

### 首次设置
1. 确保数据库中有配置数据
2. 导出配置：`python export_config_data.py`
3. 提交到Git：`git add backend/config_data/ && git commit -m "feat: 初始配置数据（全量）"`

### 日常使用（推荐全量同步）
- **更新配置**：修改 → 导出 → 提交
- **同步配置**：拉取 → 全量导入 (`--full-replace`)
- **查看状态**：检查 `export_summary.json`

### 团队同步最佳实践
```bash
# 配置更新者工作流
python export_config_data.py
git add backend/config_data/
git commit -m "feat: 更新XX配置标准（全量）"
git push

# 配置使用者工作流  
git pull
python import_config_data.py --full-replace
# 确认配置已同步，重启应用
```

### 紧急恢复
如果遇到不可解决的导入问题：
1. 查找自动备份文件：`config_backup_*.json`
2. 手动恢复或重新初始化数据库：`python database/init_db.py`
3. 使用简化导入：`python simple_import.py`

## 🔍 全量同步的优势

### ✅ 解决的问题
1. **配置不一致**：团队成员间配置标准不统一
2. **无法删除**：删除的配置项无法在团队间同步
3. **修改不生效**：配置修改无法自动更新到其他环境
4. **版本冲突**：配置版本管理混乱

### 🎯 适用场景
- 📋 标准化团队配置
- 🔄 解决配置不一致问题  
- 🗑️ 同步删除废弃的配置
- ✏️ 同步修改现有配置
- 👥 多人协作开发
- 🚀 部署到生产环境

---
**智能Q&A评估系统 v2.3.0** - 配置数据全量同步系统 🔄✨ 