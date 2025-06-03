#!/bin/bash
# 前端后端连接测试脚本

echo "🧪 测试前端后端连接..."

# 获取服务器IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "🌐 服务器IP: $SERVER_IP"

# 测试后端健康检查
echo "1. 测试后端健康检查..."
curl -s "http://$SERVER_IP:5001/health" | jq .

# 测试调试ping接口
echo "2. 测试调试ping接口..."
curl -s -X POST "http://$SERVER_IP:5001/api/debug/ping" \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}' | jq .

# 测试评估历史保存接口
echo "3. 测试评估历史保存接口..."
curl -s -X POST "http://$SERVER_IP:5001/api/evaluation-history" \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "测试问题",
    "model_answer": "测试答案", 
    "total_score": 8.0,
    "evaluation_criteria": "测试标准"
  }' | jq .

# 模拟前端请求（带Origin头）
echo "4. 模拟前端请求..."
curl -s -X POST "http://$SERVER_IP:5001/api/evaluation-history" \
  -H "Content-Type: application/json" \
  -H "Origin: http://$SERVER_IP:3000" \
  -d '{
    "user_input": "前端模拟测试",
    "model_answer": "前端模拟答案",
    "total_score": 9.0,
    "evaluation_criteria": "前端模拟标准"
  }' | jq .

echo "✅ 测试完成"
