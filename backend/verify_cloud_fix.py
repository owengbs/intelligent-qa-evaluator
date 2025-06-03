#!/usr/bin/env python3
"""
验证云端部署修复效果
"""

import os
import json
import subprocess
from datetime import datetime

def get_server_ip():
    """获取服务器IP"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "未知IP"

def check_backend_status():
    """检查后端服务状态"""
    print("🔍 检查后端服务状态...")
    
    try:
        import requests
        server_ip = get_server_ip()
        
        # 测试健康检查
        response = requests.get(f"http://{server_ip}:5001/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 后端健康检查正常: {response.json()}")
        else:
            print(f"❌ 后端健康检查失败: {response.status_code}")
            return False
            
        # 测试评估历史接口
        test_data = {
            "user_input": "【验证测试】云端连接测试",
            "model_answer": "这是一个云端连接验证测试",
            "total_score": 9.0,
            "evaluation_criteria": "验证云端部署修复效果"
        }
        
        response = requests.post(
            f"http://{server_ip}:5001/api/evaluation-history",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 评估历史保存测试成功: 记录ID {result.get('history_id')}")
            return True
        else:
            print(f"❌ 评估历史保存测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 后端测试失败: {str(e)}")
        return False

def check_frontend_config():
    """检查前端配置"""
    print("\n🔍 检查前端配置...")
    
    frontend_path = '../frontend'
    server_ip = get_server_ip()
    
    # 检查 .env 文件
    env_file = os.path.join(frontend_path, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if server_ip in content and 'localhost' not in content:
                print(f"✅ .env 文件配置正确: {content.strip()}")
            else:
                print(f"❌ .env 文件配置错误")
                return False
    
    # 检查 package.json
    package_json = os.path.join(frontend_path, 'package.json')
    if os.path.exists(package_json):
        with open(package_json, 'r') as f:
            package_data = json.load(f)
            if 'proxy' in package_data:
                if server_ip in package_data['proxy'] and 'localhost' not in package_data['proxy']:
                    print(f"✅ package.json 代理配置正确: {package_data['proxy']}")
                else:
                    print(f"❌ package.json 代理配置错误: {package_data['proxy']}")
                    return False
    
    return True

def create_test_instructions():
    """创建测试说明"""
    server_ip = get_server_ip()
    
    instructions = f"""
# 🧪 云端部署验证测试指南

## 问题解决总结
✅ **根本原因**: 前端配置使用localhost导致请求发送到错误地址
✅ **解决方案**: 已将前端配置更新为云端服务器IP地址

## 验证步骤

### 1. 重启前端服务
```bash
# 方法1: 使用自动生成的启动脚本
bash start_frontend_dev.sh

# 方法2: 手动启动
export REACT_APP_API_URL=http://{server_ip}:5001/api
cd ../frontend
npm start
```

### 2. 测试前端后端连接
1. 在浏览器中访问: http://{server_ip}:3000
2. 打开Chrome开发者工具 (F12)
3. 切换到 Network 标签
4. 清除日志并勾选 "Preserve log"
5. 进行一次评估测试

### 3. 检查网络请求
在Chrome Network标签中应该看到：

✅ **评估请求**: POST http://{server_ip}:5001/api/evaluate
   - 状态码: 200
   - 响应包含评分结果

✅ **历史保存请求**: POST http://{server_ip}:5001/api/evaluation-history  
   - 状态码: 200
   - 请求URL指向云端服务器
   - 响应包含成功消息和记录ID

### 4. 验证数据保存
检查后端日志，应该看到：
- "🎯 收到评估历史保存请求!"
- "✅ 成功保存评估历史记录，ID: XXX"

## 故障排除

### 如果仍然有问题：

1. **清除浏览器缓存**:
   - 硬刷新: Ctrl+F5 (Windows) 或 Cmd+Shift+R (Mac)
   - 或者清除浏览器数据

2. **检查防火墙**:
   ```bash
   sudo ufw allow 5001
   sudo ufw allow 3000
   ```

3. **重启所有服务**:
   ```bash
   # 重启后端
   bash start_cloud.sh
   
   # 重启前端
   bash start_frontend_dev.sh
   ```

4. **检查端口占用**:
   ```bash
   lsof -i :5001
   lsof -i :3000
   ```

## 成功标志
- ✅ Chrome Network显示请求发送到 {server_ip}:5001
- ✅ 后端控制台显示收到保存请求
- ✅ 前端显示"保存成功"
- ✅ 数据库中有新的评估记录

当前服务器IP: {server_ip}
当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('CLOUD_VERIFICATION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"📋 验证指南已创建: CLOUD_VERIFICATION_GUIDE.md")

def main():
    """主函数"""
    print("🔬 云端部署修复验证工具")
    print("=" * 50)
    
    server_ip = get_server_ip()
    print(f"🌐 当前服务器IP: {server_ip}")
    
    # 1. 检查后端状态
    backend_ok = check_backend_status()
    
    # 2. 检查前端配置
    frontend_ok = check_frontend_config()
    
    # 3. 创建测试指南
    create_test_instructions()
    
    print("\n" + "=" * 50)
    
    if backend_ok and frontend_ok:
        print("🎉 验证通过！修复成功！")
        print(f"\n📋 接下来请:")
        print(f"1. 重启前端服务: bash start_frontend_dev.sh")
        print(f"2. 访问 http://{server_ip}:3000 测试评估功能")
        print(f"3. 查看Chrome开发者工具确认请求发送到正确地址")
        print(f"4. 参考 CLOUD_VERIFICATION_GUIDE.md 进行完整测试")
    else:
        print("⚠️  验证发现问题，请检查:")
        if not backend_ok:
            print("   - 后端服务未正常运行")
        if not frontend_ok:
            print("   - 前端配置仍有问题")
        print("   - 参考 CLOUD_VERIFICATION_GUIDE.md 进行故障排除")

if __name__ == '__main__':
    main() 