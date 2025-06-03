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

# 生产环境构建
echo "🔨 构建生产版本..."
npm run build

# 启动前端服务（生产模式）
echo "🚀 启动前端服务 (端口: 8701)..."

# 方法1: 尝试使用npx serve
if npx serve --version &> /dev/null 2>&1; then
    echo "✅ 使用 npx serve 启动服务..."
    npx serve -s build -l 8701
elif command -v python3 &> /dev/null; then
    # 方法2: 使用Python的HTTP服务器作为备选
    echo "⚠️  npx serve不可用，使用Python HTTP服务器..."
    cd build && python3 -m http.server 8701
elif command -v python &> /dev/null; then
    # 方法3: 使用Python2的HTTP服务器
    echo "⚠️  使用Python2 HTTP服务器..."
    cd build && python -m SimpleHTTPServer 8701
else
    echo "❌ 错误: 无法找到合适的HTTP服务器"
    echo "请手动安装serve: npm install -g serve"
    echo "然后运行: serve -s build -l 8701"
    exit 1
fi 