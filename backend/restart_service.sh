#!/bin/bash

echo "🔄 重启智能QA评估系统后端服务..."

# 查找并停止现有的Python进程
echo "📋 查找现有的Python后端进程..."
pgrep -f "python.*app.py" | while read pid; do
    echo "🛑 停止进程 $pid"
    kill $pid
done

# 等待进程完全停止
sleep 2

# 重新启动服务
echo "🚀 启动后端服务..."
cd /data/macxin/intelligent-qa-evaluator/backend

# 检查运行环境
if [ "$APP_ENV" = "production" ]; then
    echo "🌐 生产环境模式启动"
    nohup python app.py > production.log 2>&1 &
else
    echo "🛠️ 开发环境模式启动" 
    nohup python app.py > app.log 2>&1 &
fi

sleep 3

# 验证服务是否启动成功
if pgrep -f "python.*app.py" > /dev/null; then
    echo "✅ 后端服务启动成功！"
    echo "📊 进程信息："
    pgrep -f "python.*app.py" | xargs ps -p
else
    echo "❌ 后端服务启动失败，请检查日志"
fi

echo "📝 如需查看日志，请运行："
echo "   tail -f app.log  (开发环境)"
echo "   tail -f production.log  (生产环境)" 