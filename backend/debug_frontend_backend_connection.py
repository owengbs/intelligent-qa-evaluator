#!/usr/bin/env python3
"""
前端后端连接问题调试工具
专门解决云端环境下前端显示成功但后端没收到请求的问题
"""

import os
import json
import time
import threading
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

def create_debug_server():
    """创建调试服务器来监控请求"""
    debug_app = Flask(__name__)
    CORS(debug_app)
    
    # 请求记录
    request_log = []
    
    @debug_app.route('/api/debug/ping', methods=['GET', 'POST'])
    def debug_ping():
        """调试ping接口"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'data': request.get_json() if request.method == 'POST' else None,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        request_log.append(log_entry)
        
        print(f"🔍 收到调试请求: {request.method} {request.path}")
        print(f"   来源: {request.remote_addr}")
        print(f"   时间: {log_entry['timestamp']}")
        
        return jsonify({
            'success': True,
            'message': '调试ping成功',
            'timestamp': log_entry['timestamp'],
            'received_data': log_entry['data']
        })
    
    @debug_app.route('/api/evaluation-history', methods=['POST'])
    def debug_evaluation_history():
        """调试评估历史保存接口"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'data': request.get_json(),
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        request_log.append(log_entry)
        
        print(f"🎯 收到评估历史保存请求!")
        print(f"   时间: {log_entry['timestamp']}")
        print(f"   来源: {request.remote_addr}")
        print(f"   数据: {json.dumps(log_entry['data'], ensure_ascii=False, indent=2)}")
        
        return jsonify({
            'success': True,
            'message': '调试：评估历史保存请求已收到',
            'history_id': 9999,  # 调试用的假ID
            'debug_mode': True,
            'received_data': log_entry['data']
        })
    
    @debug_app.route('/api/debug/requests', methods=['GET'])
    def get_debug_requests():
        """获取调试请求记录"""
        return jsonify({
            'total_requests': len(request_log),
            'requests': request_log[-10:]  # 最近10个请求
        })
    
    @debug_app.route('/health', methods=['GET'])
    def debug_health():
        """调试健康检查"""
        return jsonify({
            'status': 'debug_healthy',
            'timestamp': datetime.now().isoformat(),
            'debug_mode': True
        })
    
    return debug_app, request_log

def analyze_chrome_logs():
    """分析Chrome开发者工具日志的指导"""
    print("\n🔍 Chrome开发者工具网络分析指南")
    print("=" * 50)
    
    instructions = """
📋 请在Chrome中按照以下步骤操作：

1. 打开Chrome开发者工具 (F12)
2. 切换到 "Network" (网络) 标签
3. 确保 "Preserve log" (保留日志) 已勾选
4. 清除现有日志 (Clear 按钮)
5. 进行一次评估操作
6. 观察网络请求

🔍 重点检查以下请求：

A. 评估请求 (/api/evaluate):
   - 状态码应该是 200
   - 响应应该包含评分结果
   - 检查 Request URL 是否正确

B. 历史保存请求 (/api/evaluation-history):
   - 方法应该是 POST
   - 状态码应该是 200  
   - Request URL 应该指向你的云端服务器
   - 检查 Request Headers 中的 Origin

C. 如果没有看到历史保存请求：
   - 说明前端代码没有发送请求
   - 可能是前端逻辑问题

D. 如果看到历史保存请求但状态码不是200：
   - 检查错误响应内容
   - 可能是后端问题

E. 如果Request URL不正确：
   - 检查前端API配置
   - 可能是环境变量问题
"""
    
    print(instructions)
    
    # 保存到文件
    with open('chrome_debug_guide.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print("📄 调试指南已保存到: chrome_debug_guide.md")

def check_frontend_config():
    """检查前端配置"""
    print("\n🔧 检查前端配置")
    print("=" * 30)
    
    # 检查前端目录是否存在
    frontend_path = '../frontend'
    if os.path.exists(frontend_path):
        print("✅ 前端目录存在")
        
        # 检查环境变量文件
        env_files = ['.env', '.env.local', '.env.production']
        for env_file in env_files:
            env_path = os.path.join(frontend_path, env_file)
            if os.path.exists(env_path):
                print(f"📄 发现环境变量文件: {env_file}")
                with open(env_path, 'r') as f:
                    content = f.read()
                    if 'REACT_APP_API_URL' in content:
                        print(f"   内容: {content.strip()}")
                    else:
                        print("   ⚠️  没有找到 REACT_APP_API_URL 配置")
            else:
                print(f"❌ 未找到环境变量文件: {env_file}")
        
        # 检查package.json中的代理配置
        package_json_path = os.path.join(frontend_path, 'package.json')
        if os.path.exists(package_json_path):
            print("📦 检查package.json代理配置...")
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                if 'proxy' in package_data:
                    print(f"   代理配置: {package_data['proxy']}")
                else:
                    print("   ❌ 没有代理配置")
        
        # 检查前端服务文件
        service_file = os.path.join(frontend_path, 'src/services/evaluationService.js')
        if os.path.exists(service_file):
            print("🔍 检查evaluationService.js配置...")
            with open(service_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                for i, line in enumerate(lines[:10]):  # 只看前10行
                    if 'API_BASE_URL' in line:
                        print(f"   第{i+1}行: {line.strip()}")
    else:
        print("❌ 前端目录不存在")

def create_test_requests():
    """创建测试请求脚本"""
    print("\n📜 创建测试请求脚本")
    print("=" * 30)
    
    test_script = """#!/bin/bash
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
curl -s -X POST "http://$SERVER_IP:5001/api/debug/ping" \\
  -H "Content-Type: application/json" \\
  -d '{"test": "ping"}' | jq .

# 测试评估历史保存接口
echo "3. 测试评估历史保存接口..."
curl -s -X POST "http://$SERVER_IP:5001/api/evaluation-history" \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_input": "测试问题",
    "model_answer": "测试答案", 
    "total_score": 8.0,
    "evaluation_criteria": "测试标准"
  }' | jq .

# 模拟前端请求（带Origin头）
echo "4. 模拟前端请求..."
curl -s -X POST "http://$SERVER_IP:5001/api/evaluation-history" \\
  -H "Content-Type: application/json" \\
  -H "Origin: http://$SERVER_IP:3000" \\
  -d '{
    "user_input": "前端模拟测试",
    "model_answer": "前端模拟答案",
    "total_score": 9.0,
    "evaluation_criteria": "前端模拟标准"
  }' | jq .

echo "✅ 测试完成"
"""
    
    script_file = 'test_frontend_backend_connection.sh'
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    os.chmod(script_file, 0o755)
    print(f"📜 测试脚本已创建: {script_file}")
    print("使用方法: bash test_frontend_backend_connection.sh")

def generate_troubleshooting_checklist():
    """生成故障排除检查表"""
    print("\n📋 生成故障排除检查表")
    print("=" * 30)
    
    checklist = """
# 前端后端连接故障排除检查表

## 🔍 问题现象
- [ ] 前端显示评估成功
- [ ] Chrome开发者工具显示请求成功
- [ ] 后端没有收到保存历史的请求
- [ ] 数据库中没有新的评估记录

## 📊 Chrome开发者工具检查
- [ ] 打开Network标签，清除日志
- [ ] 进行一次评估操作
- [ ] 查看是否有 POST /api/evaluation-history 请求
- [ ] 检查请求的URL是否指向正确的服务器
- [ ] 检查请求状态码是否为200
- [ ] 检查响应内容是否来自正确的后端

## 🔧 前端配置检查
- [ ] 检查环境变量 REACT_APP_API_URL 设置
- [ ] 检查package.json中的proxy配置
- [ ] 检查evaluationService.js中的API_BASE_URL
- [ ] 确认前端是否在正确的模式下运行

## 🌐 网络连接检查
- [ ] 后端服务是否正常启动
- [ ] 端口5001是否可访问
- [ ] 防火墙是否阻挡了请求
- [ ] CORS是否正确配置

## 🧪 测试步骤
1. 运行后端调试服务器
2. 运行连接测试脚本
3. 检查Chrome网络日志
4. 对比前端请求URL和后端地址

## 🔧 常见解决方案

### 情况1: 前端请求发到了错误的地址
**解决方案**: 设置正确的环境变量
```bash
export REACT_APP_API_URL=http://云端服务器IP:5001/api
```

### 情况2: 前端使用了开发代理
**解决方案**: 确保代理配置正确或禁用代理
```json
// package.json 中移除或修改
"proxy": "http://云端服务器IP:5001"
```

### 情况3: 网络问题
**解决方案**: 检查防火墙和端口
```bash
sudo ufw allow 5001
sudo ufw allow 3000
```

### 情况4: CORS问题
**解决方案**: 检查后端CORS配置
```python
CORS(app, origins=["http://云端服务器IP:3000"])
```
"""
    
    checklist_file = 'frontend_backend_connection_checklist.md'
    with open(checklist_file, 'w', encoding='utf-8') as f:
        f.write(checklist)
    
    print(f"📋 检查表已创建: {checklist_file}")

def main():
    """主函数"""
    print("🔍 前端后端连接问题调试工具")
    print("=" * 60)
    
    # 1. 分析Chrome日志指南
    analyze_chrome_logs()
    
    # 2. 检查前端配置
    check_frontend_config()
    
    # 3. 创建测试脚本
    create_test_requests()
    
    # 4. 生成检查表
    generate_troubleshooting_checklist()
    
    # 5. 提供调试服务器选项
    print("\n🚀 启动调试服务器选项")
    print("=" * 30)
    print("可以启动一个调试服务器来监控前端请求:")
    print("python -c \"")
    print("from debug_frontend_backend_connection import create_debug_server")
    print("app, log = create_debug_server()")
    print("app.run(host='0.0.0.0', port=5002, debug=True)")
    print("\"")
    
    print("\n" + "=" * 60)
    print("🎯 调试工具准备完毕！")
    print("\n📋 接下来的步骤:")
    print("1. 查看Chrome网络日志 (chrome_debug_guide.md)")
    print("2. 运行连接测试: bash test_frontend_backend_connection.sh")
    print("3. 按照检查表逐项检查 (frontend_backend_connection_checklist.md)")
    print("4. 如需要，启动调试服务器监控请求")

if __name__ == '__main__':
    main() 