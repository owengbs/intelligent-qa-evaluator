# 🚀 快速部署指南

## 📋 环境对比

| 配置项 | 本地开发环境 | 线上生产环境 |
|--------|-------------|-------------|
| 后端端口 | **5001** | **7860** |
| 前端端口 | **3000** | **8701** |
| 后端IP | localhost | 9.135.87.101 |
| 前端IP | localhost | 9.135.87.101 |
| 调试模式 | 开启 | 关闭 |

## ⚡ 一键启动

### 本地开发环境
```bash
# 启动后端 (端口: 5001)
cd backend
bash start_local.sh

# 启动前端 (端口: 3000) - 新窗口
cd backend
bash start_frontend_local.sh

# 访问地址
# 前端: http://localhost:3000
# 后端API: http://localhost:5001/api
```

### 线上生产环境
```bash
# 启动后端 (端口: 7860)
cd backend
bash start_production.sh

# 启动前端 (端口: 8701) - 新窗口
cd backend
bash start_frontend_production.sh

# 访问地址
# 前端: http://9.135.87.101:8701
# 后端API: http://9.135.87.101:7860/api
```

## 🔄 环境切换

### 切换到本地环境
```bash
export APP_ENV=local
```

### 切换到生产环境
```bash
export APP_ENV=production
```

## ⚙️ 手动启动

### 本地环境
```bash
# 后端
cd backend
export APP_ENV=local
source venv/bin/activate
python app.py  # 启动在 5001 端口

# 前端
cd frontend
cp ../backend/env_local.txt .env.local
npm start  # 启动在 3000 端口
```

### 生产环境
```bash
# 后端
cd backend
export APP_ENV=production
source venv/bin/activate
python app.py  # 启动在 7860 端口

# 前端
cd frontend
cp ../backend/env_production.txt .env.production
npm run build
serve -s build -l 8701  # 启动在 8701 端口
```

## 🔧 验证配置

### 检查当前环境
```bash
cd backend
python config.py
```

### 验证服务运行
```bash
# 检查后端健康状态
curl http://localhost:5001/health        # 本地
curl http://9.135.87.101:7860/health     # 生产

# 检查端口占用
lsof -i :5001  # 本地后端
lsof -i :3000  # 本地前端
lsof -i :7860  # 生产后端
lsof -i :8701  # 生产前端
```

## 🎯 关键文件

- `config.py` - 环境配置文件
- `env_local.txt` - 本地前端配置模板
- `env_production.txt` - 生产前端配置模板
- `start_local.sh` - 本地后端启动脚本
- `start_production.sh` - 生产后端启动脚本

## 🚨 常见问题

### Q: 端口被占用怎么办？
```bash
# 查找并杀死占用进程
lsof -i :端口号
kill -9 <PID>
```

### Q: 前端连接不到后端？
1. 检查后端服务是否启动
2. 检查前端 `.env` 文件中的 API 地址
3. 确认防火墙设置

### Q: 如何强制使用特定环境？
```bash
# 直接设置环境变量
APP_ENV=production python app.py
```

---

**🎉 现在您可以轻松在本地和生产环境之间切换了！** 