# 配置数据同步指南

## 🎯 目的

本系统将**配置数据**（分类标准、评估标准）与**用户数据**（评估历史）分离：
- ✅ 配置数据：通过JSON文件进行版本控制和团队同步
- ❌ 用户数据：不进行版本控制，每个环境独立维护

## 📤 导出本地配置数据

当您更新了分类标准或评估标准，需要同步给团队时：

```bash
cd backend/scripts
python export_config_data.py
```

这将在 `backend/config_data/` 目录生成：
- `classification_standards.json` - 分类标准
- `evaluation_standards.json` - 评估标准  
- `export_summary.json` - 导出摘要

## 📥 导入团队配置数据

当团队成员更新了配置，您需要同步到本地时：

```bash
cd backend/scripts
python import_config_data.py
```

### 高级选项

```bash
# 指定配置目录
python import_config_data.py --config-dir ../config_data

# 强制更新已存在的配置
python import_config_data.py --force-update
```

## 🔄 团队协作流程

### 配置更新者（如：产品经理）
1. 在系统中更新分类标准或评估标准
2. 运行导出脚本：`python export_config_data.py`
3. 提交配置文件到Git：
   ```bash
   git add config_data/
   git commit -m "feat: 更新评估标准配置"
   git push
   ```

### 配置使用者（如：开发人员）
1. 拉取最新代码：`git pull`
2. 导入最新配置：`python import_config_data.py`
3. 系统自动同步配置到本地数据库

## 📋 配置文件格式

### classification_standards.json
```json
{
  "export_time": "2025-06-03T10:00:00",
  "description": "分类标准配置数据 - 用于团队同步",
  "count": 10,
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
  "description": "评估标准配置数据 - 用于团队同步",
  "count": 15,
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

1. **数据安全**：只有配置数据会同步，用户评估历史不会泄露
2. **冲突处理**：默认不覆盖已存在的配置，使用 `--force-update` 强制更新
3. **备份建议**：重要配置更新前建议先备份数据库
4. **权限控制**：配置导出/导入需要数据库写权限

## 🛠️ 故障排除

### 导出失败
- 检查数据库连接是否正常
- 确保有读取权限

### 导入失败  
- 检查JSON文件格式是否正确
- 确保有数据库写权限
- 查看具体错误信息

### 配置不生效
- 重启应用服务
- 检查是否正确导入到目标数据库

## 🚀 快速开始

### 首次设置
1. 确保数据库中有配置数据
2. 导出配置：`python export_config_data.py`
3. 提交到Git：`git add config_data/ && git commit -m "feat: 初始配置数据"`

### 日常使用
- **更新配置**：修改 → 导出 → 提交
- **同步配置**：拉取 → 导入
- **查看状态**：检查 `export_summary.json`

---
**智能Q&A评估系统 v2.3.0** - 配置数据同步系统 🔄✨ 