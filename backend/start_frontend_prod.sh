#!/bin/bash
# 前端生产环境启动脚本

echo "🏗️  构建前端生产版本..."

cd ../frontend

# 设置环境变量
export REACT_APP_API_URL=http://192.168.255.10:5001/api
export NODE_ENV=production

# 构建
npm run build

echo "✅ 前端构建完成，输出目录: build/"
echo "📋 可以使用以下命令启动静态服务器:"
echo "   npx serve -s build -p 3000"
