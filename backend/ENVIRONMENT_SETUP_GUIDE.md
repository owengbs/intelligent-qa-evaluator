# 🌍 环境配置指南

本指南说明如何在不同环境（本地开发 vs 线上生产）下启动智能Q&A评估系统。

## 📋 环境概览

### 本地开发环境 (Local)
- **后端端口**: 5001
- **前端端口**: 3000
- **API地址**: http://localhost:5001/api
- **前端地址**: http://localhost:3000
- **调试模式**: 开启

### 生产环境 (Production)
- **后端端口**: 7860
- **前端端口**: 8701
- **API地址**: http://9.135.87.101:7860/api
- **前端地址**: http://9.135.87.101:8701
- **调试模式**: 关闭

## 🚀 快速启动

### 本地开发环境

#### 1. 启动后端 (端口: 5001)
```bash
cd backend
bash start_local.sh
```

#### 2. 启动前端 (端口: 3000)
```bash
cd backend
bash start_frontend_local.sh
```

### 生产环境

#### 1. 启动后端 (端口: 7860)
```bash
cd backend
bash start_production.sh
```

#### 2. 启动前端 (端口: 8701)
```bash
cd backend
bash start_frontend_production.sh
```

## 🔧 手动配置

### 后端配置

后端会根据 `APP_ENV` 环境变量自动选择配置：

```bash
# 本地环境
export APP_ENV=local
python app.py  # 启动在端口 5001

# 生产环境
export APP_ENV=production
python app.py  # 启动在端口 7860
```

### 前端配置

#### 本地环境 (.env.local)
```env
REACT_APP_API_URL=http://localhost:5001/api
REACT_APP_ENV=local
PORT=3000
HOST=localhost
GENERATE_SOURCEMAP=true
FAST_REFRESH=true
```

#### 生产环境 (.env.production)
```env
REACT_APP_API_URL=http://9.135.87.101:7860/api
REACT_APP_ENV=production
PORT=8701
HOST=9.135.87.101
GENERATE_SOURCEMAP=false
FAST_REFRESH=false
INLINE_RUNTIME_CHUNK=false
```

## 📂 文件结构

```
backend/
├── config.py                      # 环境配置文件
├── app.py                         # 主应用文件
├── start_local.sh                 # 本地后端启动脚本
├── start_production.sh            # 生产后端启动脚本
├── start_frontend_local.sh        # 本地前端启动脚本
├── start_frontend_production.sh   # 生产前端启动脚本
├── env_local.txt                  # 本地前端配置模板
├── env_production.txt             # 生产前端配置模板
└── ...

frontend/
├── .env.local                     # 本地环境配置（自动生成）
├── .env.production               # 生产环境配置（自动生成）
└── ...
```

## 🔄 环境切换

### 方法1: 使用启动脚本（推荐）
启动脚本会自动设置环境变量和配置文件。

### 方法2: 手动设置环境变量
```bash
# 切换到本地环境
export APP_ENV=local

# 切换到生产环境
export APP_ENV=production
```

### 方法3: 修改前端配置文件
直接复制对应的环境配置文件：
```bash
# 本地环境
cp backend/env_local.txt frontend/.env.local

# 生产环境
cp backend/env_production.txt frontend/.env.production
```

## 🐛 故障排除

### 问题1: 端口被占用
```bash
# 查看端口占用
lsof -i :5001  # 本地后端
lsof -i :3000  # 本地前端
lsof -i :7860  # 生产后端
lsof -i :8701  # 生产前端

# 杀死占用进程
kill -9 <PID>
```

### 问题2: 前端配置文件未更新
```bash
# 手动复制配置文件
cd backend

# 本地环境
cp env_local.txt ../frontend/.env.local

# 生产环境
cp env_production.txt ../frontend/.env.production
```

### 问题3: API连接失败
检查：
1. 后端服务是否正常启动
2. 前端配置的API地址是否正确
3. 防火墙是否阻止了端口访问

## 📊 配置验证

### 验证后端配置
```bash
cd backend
python config.py
```
输出示例：
```
🌍 运行环境: local
🏠 服务器地址: 0.0.0.0:5001
🌐 API地址: http://localhost:5001/api
🖥️  前端地址: localhost:3000
🔧 调试模式: True
```

### 验证前端配置
在浏览器开发者工具中检查：
```javascript
console.log(process.env.REACT_APP_API_URL);
console.log(process.env.REACT_APP_ENV);
```

## 🎯 最佳实践

1. **开发阶段**: 使用本地环境启动脚本
2. **测试阶段**: 在本地使用生产环境配置测试
3. **部署阶段**: 使用生产环境启动脚本
4. **配置文件**: 不要直接修改 `.env` 文件，而是修改模板文件

## 🔐 安全注意事项

1. **生产环境**: 确保调试模式关闭
2. **API地址**: 生产环境使用正确的服务器IP
3. **端口配置**: 确保防火墙允许相应端口访问

## 📝 环境变量说明

| 变量名 | 本地值 | 生产值 | 说明 |
|--------|--------|--------|------|
| `APP_ENV` | `local` | `production` | 后端环境标识 |
| `REACT_APP_API_URL` | `http://localhost:5001/api` | `http://9.135.87.101:7860/api` | 前端API地址 |
| `PORT` (后端) | `5001` | `7860` | 后端服务端口 |
| `PORT` (前端) | `3000` | `8701` | 前端服务端口 |
| `DEBUG` | `true` | `false` | 调试模式 |

---

**🎉 恭喜！现在您可以轻松在不同环境之间切换了！** 