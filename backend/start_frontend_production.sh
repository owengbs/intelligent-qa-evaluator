#!/bin/bash
"""
生产环境前端启动脚本
"""

echo "🖥️  启动生产环境前端服务..."

# 检查是否在正确的目录
if [ ! -d "../frontend" ]; then
    echo "❌ 错误: 未找到前端目录，请确保在backend目录下运行此脚本"
    exit 1
fi

# 切换到前端目录
cd ../frontend

# 复制生产环境配置
echo "🔧 配置生产环境..."
cp ../backend/env_production.txt .env.production

# 显示配置信息
echo "🌍 环境: 生产环境"
echo "🏠 前端地址: http://9.135.87.101:8701"
echo "🌐 API地址: http://9.135.87.101:7860/api"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 生产环境构建（可选）
echo "🔨 构建生产版本..."
npm run build

# 启动前端服务（生产模式）
echo "🚀 启动前端服务 (端口: 8701)..."
# 使用serve来启动生产构建
if command -v serve &> /dev/null; then
    serve -s build -l 8701
else
    echo "📦 安装serve工具..."
    npm install -g serve
    serve -s build -l 8701
fi 