# 智能Q&A评估系统部署指南

## 🎯 部署概述

本指南适用于**远端生产环境**或**新的开发环境**的部署。系统分为前端(React)和后端(Flask)两部分，使用SQLite数据库。

## 📋 部署前检查清单

- [ ] Python 3.8+ 环境
- [ ] Node.js 14+ 环境  
- [ ] Git 访问权限
- [ ] 足够的磁盘空间（至少500MB）
- [ ] 网络连接正常

## 🚀 完整部署流程

### 第一步：克隆项目

```bash
git clone <项目地址>
cd intelligent-qa-evaluator
```

### 第二步：后端部署

#### 1. 创建虚拟环境
```bash
cd backend
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 🔥 初始化数据库（关键步骤）
```bash
# 方法1：使用专用初始化脚本（推荐）
python database/init_db.py

# 方法2：如果上述方法失败，使用应用启动初始化
python app.py
# 然后立即停止（Ctrl+C），这会触发自动初始化
```

#### 4. 导入配置数据（可选）
如果您有团队配置数据：
```bash
cd scripts
python import_config_data.py --full-replace
```

#### 5. 启动后端服务
```bash
# 开发模式
python app.py

# 生产模式（推荐）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 第三步：前端部署

#### 1. 安装依赖
```bash
cd ../frontend
npm install
```

#### 2. 配置API端点
编辑 `src/config/config.js`：
```javascript
const config = {
  API_BASE_URL: 'http://your-backend-server:5000'  // 修改为实际后端地址
};
```

#### 3. 构建并启动
```bash
# 开发模式
npm start

# 生产构建
npm run build
# 然后使用nginx或其他web服务器托管build文件夹
```

## 🛠️ 数据库初始化详解

### 🚨 常见问题：远端数据库为空

**症状**：
- ✅ 后端服务启动正常
- ❌ 无法保存评估记录
- ❌ 分类和评估标准为空

**根本原因**：数据库表未创建或未初始化默认数据

**解决方案**：

#### 方案1：自动初始化脚本
```bash
cd backend
python database/init_db.py
```

**期望输出**：
```
INFO - 开始初始化数据库...
INFO - 数据库表创建完成
INFO - 开始插入默认分类标准...
INFO - 开始插入默认评估标准...
INFO - 数据库初始化完成
```

#### 方案2：检查和修复脚本
```bash
cd backend
python -c "
from database.init_db import create_app, init_database
app = create_app()
with app.app_context():
    init_database()
    print('✅ 数据库初始化完成')
"
```

#### 方案3：强制重新初始化
```bash
cd backend
python -c "
from database.init_db import create_app, clear_database, init_database
app = create_app()
with app.app_context():
    clear_database()
    init_database()
    print('✅ 数据库完全重新初始化')
"
```

### 🔍 验证数据库状态

```bash
cd backend
python -c "
from app import app
from models.classification import ClassificationStandard, EvaluationStandard, EvaluationHistory
with app.app_context():
    cs_count = ClassificationStandard.query.count()
    es_count = EvaluationStandard.query.count()
    eh_count = EvaluationHistory.query.count()
    print(f'📊 数据库状态:')
    print(f'  分类标准: {cs_count} 条')
    print(f'  评估标准: {es_count} 条')
    print(f'  评估历史: {eh_count} 条')
    if cs_count > 0 and es_count > 0:
        print('✅ 数据库初始化正常')
    else:
        print('❌ 数据库需要初始化')
"
```

## 🔧 数据库文件位置

### 默认位置
```
backend/data/qa_evaluator.db
```

### 自定义位置
通过环境变量指定：
```bash
export DATABASE_URL="sqlite:///path/to/your/database.db"
```

## 📝 配置文件说明

### 后端配置（config.py）
```python
# 数据库配置
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/qa_evaluator.db'

# API配置
API_TIMEOUT = 120

# 日志级别
LOG_LEVEL = 'INFO'
```

### 前端配置（src/config/config.js）
```javascript
const config = {
  API_BASE_URL: 'http://localhost:5000',  // 后端API地址
  TIMEOUT: 30000                          // 请求超时时间
};
```

## 🚀 生产环境优化

### 后端生产配置
```bash
# 使用gunicorn启动
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app

# 或使用uwsgi
pip install uwsgi
uwsgi --http :5000 --module app:app --processes 4
```

### 前端生产配置
```bash
# 构建优化版本
npm run build

# 使用nginx托管（nginx.conf示例）
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 安全配置

### 数据库安全
- 🔒 设置适当的文件权限：`chmod 640 backend/data/qa_evaluator.db`
- 🚫 确保数据库文件不可公开访问
- 💾 定期备份数据库文件

### API安全
- 🌐 使用HTTPS（生产环境必须）
- 🔑 配置CORS安全策略
- 📝 启用请求日志记录

## 📊 监控和日志

### 应用日志位置
```
backend/logs/app.log          # 应用日志
backend/logs/evaluation.log   # 评估日志
backend/logs/error.log        # 错误日志
```

### 监控检查点
```bash
# 检查后端服务状态
curl http://localhost:5000/api/health

# 检查数据库连接
curl http://localhost:5000/api/classification-standards

# 检查前端是否正常
curl http://localhost:3000
```

## 🆘 故障排除

### 常见问题和解决方案

#### 1. 数据库连接失败
**错误**: `sqlite3.OperationalError: no such table`
**解决**: 运行数据库初始化脚本
```bash
python database/init_db.py
```

#### 2. 权限问题
**错误**: `Permission denied`
**解决**: 检查文件权限
```bash
chmod -R 755 backend/data/
chmod 640 backend/data/qa_evaluator.db
```

#### 3. 端口占用
**错误**: `Address already in use`
**解决**: 查找并终止占用进程
```bash
# 查找占用端口的进程
lsof -i :5000
# 终止进程
kill -9 <PID>
```

#### 4. 模块导入失败
**错误**: `ModuleNotFoundError`
**解决**: 检查虚拟环境和依赖
```bash
# 重新安装依赖
pip install -r requirements.txt
# 检查Python路径
python -c "import sys; print(sys.path)"
```

#### 5. 前端无法连接后端
**错误**: `Network Error`
**解决**: 检查API配置和CORS
```javascript
// 确保前端配置正确
const config = {
  API_BASE_URL: 'http://正确的后端地址:5000'
};
```

## 🔄 更新和维护

### 应用更新流程
```bash
# 拉取最新代码
git pull

# 更新后端依赖
cd backend
pip install -r requirements.txt

# 运行数据库迁移（如有）
python database/init_db.py

# 更新前端依赖
cd ../frontend
npm install

# 重新构建前端（生产环境）
npm run build

# 重启服务
```

### 配置数据同步
```bash
# 拉取最新配置数据
git pull

# 全量同步配置
cd backend/scripts
python import_config_data.py --full-replace
```

## 📈 性能优化

### 数据库优化
- 📊 定期分析查询性能
- 🗜️ 清理过期的评估历史数据
- 💾 优化数据库索引

### 应用优化
- 🚀 使用Redis缓存（可选）
- 📦 启用gzip压缩
- 🔄 配置负载均衡（多实例）

## 📞 技术支持

### 问题报告
如遇到部署问题，请提供：
1. 🖥️ 操作系统和版本
2. 🐍 Python版本
3. 📝 完整的错误日志
4. 🔧 执行的具体命令

### 数据备份恢复
```bash
# 备份数据库
cp backend/data/qa_evaluator.db backup_$(date +%Y%m%d_%H%M%S).db

# 恢复数据库
cp backup_20240603_103000.db backend/data/qa_evaluator.db
```

---

## 🎯 快速启动检查清单

部署完成后，请验证以下功能：

- [ ] 🔗 后端API响应正常（访问 `/api/health`）
- [ ] 📊 数据库包含分类和评估标准
- [ ] 🎨 前端界面加载正常
- [ ] 🤖 AI评估功能工作正常
- [ ] 💾 评估结果能正确保存
- [ ] 📈 评估历史记录显示正常
- [ ] 👥 人工评估功能正常（如需要）

**完成以上所有检查项，说明部署成功！** 🎉

---
**智能Q&A评估系统 v2.3.0** - 完整部署指南 🚀✨ 