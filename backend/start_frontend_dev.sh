#!/bin/bash
# 前端开发环境启动脚本（云端版）

echo "🚀 启动前端开发服务器（云端版）..."

cd ../frontend

# 设置环境变量
export REACT_APP_API_URL=http://192.168.255.10:5001/api
echo "🌐 API地址设置为: $REACT_APP_API_URL"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "🎯 启动前端服务器..."
npm start
