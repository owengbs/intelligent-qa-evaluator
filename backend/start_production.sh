#!/bin/bash
"""
生产环境后端启动脚本
"""

echo "🌐 启动生产环境后端服务..."

# 设置生产环境变量
export APP_ENV=production
export FLASK_ENV=production

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境，尝试激活..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 未找到虚拟环境，请先创建: python -m venv venv"
        exit 1
    fi
fi

# 检查依赖
echo "📦 检查Python依赖..."
pip install -r requirements.txt

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到.env文件，尝试复制模板..."
    if [ -f "env_production.txt" ]; then
        cp env_production.txt .env
        echo "✅ .env文件已创建"
    else
        echo "❌ 请创建.env文件配置DeepSeek API密钥"
        exit 1
    fi
fi

# 数据库初始化
echo "💾 初始化生产环境数据库..."
python init_production_db.py
if [ $? -ne 0 ]; then
    echo "❌ 数据库初始化失败"
    exit 1
fi

# 显示配置信息
echo "🔧 检查配置信息..."
python config.py

# 启动Flask应用
echo "🚀 启动Flask应用 (端口: 7860)..."
echo "🌐 API地址: http://9.135.87.101:7860/api"
echo "🔗 健康检查: http://9.135.87.101:7860/api/health"
echo ""
echo "💡 提示:"
echo "   - 按 Ctrl+C 停止服务"
echo "   - 在另一个终端运行前端启动脚本"
echo ""

# 启动应用
python app.py 