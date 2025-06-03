# 数据库设置说明

## 🎯 重要说明

**数据库文件不应被版本控制！** 每个环境（开发/测试/生产）应维护独立的数据库实例。

## 🚀 初始化数据库

对于新的部署环境或首次运行，请执行以下步骤：

### 1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python init_db.py
```

这将创建一个新的SQLite数据库文件，包含以下表结构：
- `evaluation_history` - 评估历史记录（包含人工评估字段）
- `classification_standards` - 分类标准
- `evaluation_standards` - 评估标准

### 3. 验证数据库
数据库文件将在以下位置创建：
```
backend/data/qa_evaluator.db
```

## 🔄 数据库迁移

### v2.3.0 人工评估字段
如果您的数据库是在v2.3.0之前创建的，运行 `init_db.py` 将自动添加以下字段：
- `human_total_score` - 人工评估总分
- `human_dimensions_json` - 人工评估各维度分数
- `human_reasoning` - 人工评估理由
- `human_evaluation_by` - 评估者姓名
- `human_evaluation_time` - 人工评估时间
- `is_human_modified` - 是否已人工修正

## ⚠️ 注意事项

1. **数据备份**：在生产环境中，请定期备份数据库文件
2. **权限设置**：确保应用有读写 `backend/data/` 目录的权限
3. **环境隔离**：不同环境使用不同的数据库文件
4. **版本控制**：数据库文件已被添加到 `.gitignore`，不会被提交到Git

## 🔧 故障排除

### 数据库文件丢失
如果数据库文件意外丢失，重新运行：
```bash
python init_db.py
```

### 表结构更新
当系统升级后，运行迁移脚本：
```bash
python init_db.py
```
脚本会自动检测并添加缺失的字段。

### 权限问题
确保 `backend/data/` 目录存在且可写：
```bash
mkdir -p backend/data
chmod 755 backend/data
```

## 📊 数据库结构

### evaluation_history 表
```sql
CREATE TABLE evaluation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_input TEXT NOT NULL,
    model_answer TEXT NOT NULL,
    reference_answer TEXT,
    question_time TEXT,
    evaluation_criteria TEXT NOT NULL,
    total_score REAL NOT NULL,
    dimensions_json TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    classification_level1 TEXT,
    classification_level2 TEXT,
    classification_level3 TEXT,
    evaluation_time_seconds REAL,
    model_used TEXT DEFAULT 'deepseek-chat',
    raw_response TEXT,
    -- v2.3.0 人工评估字段
    human_total_score INTEGER,
    human_dimensions_json TEXT,
    human_reasoning TEXT,
    human_evaluation_by TEXT,
    human_evaluation_time TIMESTAMP,
    is_human_modified BOOLEAN DEFAULT FALSE,
    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---
**智能Q&A评估系统 v2.3.0** - 支持AI+人工协作评估 🤖👨‍💼 