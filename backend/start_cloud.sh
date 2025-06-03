#!/bin/bash
# 云端后端启动脚本

echo "🚀 启动智能问答评估系统（云端版）..."

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "✅ 激活虚拟环境..."
    source venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 检查依赖
echo "📦 检查Python依赖..."
pip install -r requirements.txt

# 初始化数据库（如果需要）
if [ ! -f "instance/app.db" ]; then
    echo "🔧 初始化数据库..."
    python quick_init.py
fi

# 检查端口占用
PORT=5001
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  端口 $PORT 已被占用，尝试终止..."
    kill -9 $(lsof -t -i:$PORT)
    sleep 2
fi

# 获取本机IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "🌐 服务器IP: $LOCAL_IP"
echo "🔗 访问地址: http://$LOCAL_IP:$PORT"

# 启动服务
echo "🎯 启动后端服务..."
python app.py

echo "🎉 后端服务已启动！"
