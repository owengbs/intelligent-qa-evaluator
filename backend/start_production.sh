#!/bin/bash
"""
生产环境启动脚本
"""

echo "🚀 启动生产环境..."

# 设置环境变量
export APP_ENV=production

# 显示配置信息
echo "🌍 环境: 生产环境 (production)"
echo "🏠 后端地址: http://9.135.87.101:7860"
echo "🖥️  前端地址: http://9.135.87.101:8701"

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "📦 激活Python虚拟环境..."
    source venv/bin/activate
else
    echo "⚠️  警告: 未找到venv目录，请先创建虚拟环境"
    echo "运行: python -m venv venv"
    exit 1
fi

# 安装依赖（如果需要）
if [ ! -f "venv/lib/python*/site-packages/flask" ]; then
    echo "📦 安装Python依赖..."
    pip install -r requirements.txt
fi

# 配置前端环境
echo "🔧 配置前端环境..."
cp env_production.txt ../frontend/.env.production 2>/dev/null || echo "⚠️  前端配置文件复制失败，请手动复制"

# 启动后端服务
echo "🚀 启动后端服务 (端口: 7860)..."
python app.py 