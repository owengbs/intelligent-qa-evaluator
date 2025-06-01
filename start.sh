#!/bin/bash

echo "🚀 启动智能问答评估系统..."

# 检查是否在项目根目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务..."
cd backend

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查并安装依赖
if [ ! -d "venv" ]; then
    echo "🔧 创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "📚 安装Python依赖..."
pip install -r requirements.txt

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "⚙️  复制环境配置文件..."
    cp env_example.txt .env
    echo "⚠️  请编辑 backend/.env 文件配置您的LLM API"
fi

# 后台启动Flask应用
echo "🌐 启动Flask后端服务..."
nohup python app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

cd ..

# 启动前端
echo "🎨 启动前端应用..."
cd frontend

# 检查Node.js环境
if ! command -v npm &> /dev/null; then
    echo "❌ 错误: 未找到npm，请先安装Node.js"
    kill $BACKEND_PID
    exit 1
fi

# 检查并安装依赖
if [ ! -d "node_modules" ]; then
    echo "📚 安装Node.js依赖..."
    npm install
fi

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "⚙️  复制前端环境配置..."
    cp env_config.txt .env
fi

# 启动React应用
echo "🚀 启动React前端应用..."
npm start &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ 系统启动完成!"
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:5000"
echo ""
echo "📝 日志文件位置:"
echo "   - 后端日志: logs/backend.log"
echo "   - 应用日志: logs/qa_evaluator_$(date +%Y%m%d).log"
echo ""
echo "🛑 停止服务: Ctrl+C 或运行 ./stop.sh"
echo ""

# 等待用户中断
wait 