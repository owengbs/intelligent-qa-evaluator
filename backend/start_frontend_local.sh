#!/bin/bash
"""
本地前端启动脚本
"""

echo "🖥️  启动本地前端服务..."

# 检查是否在正确的目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 未找到前端目录，请确保在backend目录下运行此脚本"
    exit 1
fi

# 切换到前端目录
cd ../frontend

# 复制本地环境配置
echo "🔧 配置本地环境..."
cp ../backend/env_local.txt .env.local

# 显示配置信息
echo "🌍 环境: 本地开发"
echo "🏠 前端地址: http://localhost:3000"
echo "🌐 API地址: http://localhost:5001/api"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动前端服务
echo "🚀 启动前端服务 (端口: 3000)..."
npm start 