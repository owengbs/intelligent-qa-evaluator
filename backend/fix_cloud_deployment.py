#!/usr/bin/env python3
"""
云端部署问题一键修复脚本
解决评估数据保存和配置问题
"""

import os
import json
import sys
from datetime import datetime

def check_environment():
    """检查云端环境配置"""
    print("🔍 检查云端环境配置...")
    
    # 检查基本文件
    required_files = [
        'app.py',
        'requirements.txt',
        'config.py',
        'services/evaluation_history_service.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {missing_files}")
        return False
    else:
        print("✅ 必要文件检查通过")
    
    # 检查虚拟环境
    if not os.path.exists('venv'):
        print("⚠️  虚拟环境不存在，需要创建")
        return False
    else:
        print("✅ 虚拟环境存在")
    
    return True

def test_backend_api():
    """测试后端API是否正常工作"""
    print("\n🧪 测试后端API...")
    
    try:
        from app import app, evaluation_history_service
        
        with app.app_context():
            # 测试数据保存
            test_data = {
                'user_input': '【云端测试】什么是人工智能？',
                'model_answer': '人工智能是计算机科学的一个分支。',
                'reference_answer': '人工智能是让机器模拟人类智能的技术。',
                'question_time': datetime.now().isoformat(),
                'evaluation_criteria': '测试评估标准',
                'total_score': 8.0,
                'dimensions': {'准确性': 4, '完整性': 4},
                'reasoning': '云端部署测试',
                'raw_response': '测试响应'
            }
            
            result = evaluation_history_service.save_evaluation_result(test_data)
            
            if result.get('success'):
                print(f"✅ 数据保存测试成功，记录ID: {result.get('history_id')}")
                return True
            else:
                print(f"❌ 数据保存测试失败: {result.get('message')}")
                return False
                
    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")
        return False

def fix_frontend_config():
    """生成前端配置修复方案"""
    print("\n🔧 生成前端配置修复方案...")
    
    config_instructions = """
云端前端配置修复指南：

1. 设置环境变量（推荐）：
   export REACT_APP_API_URL=http://你的云端服务器IP:5001/api
   # 例如：export REACT_APP_API_URL=http://192.168.1.100:5001/api

2. 或者修改前端代码（如果无法设置环境变量）：
   文件：frontend/src/services/evaluationService.js
   修改第3行：
   const API_BASE_URL = 'http://你的云端服务器IP:5001/api';

3. 确保前端能访问后端：
   - 检查云端服务器防火墙是否开放5001端口
   - 确认后端启动时绑定了正确的IP地址
   - 测试命令：curl http://云端服务器IP:5001/health

4. 重启前端服务：
   cd frontend
   npm start
"""
    
    print(config_instructions)
    
    # 创建配置文件
    config_file = 'cloud_frontend_config.md'
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_instructions)
    
    print(f"📄 配置说明已保存到: {config_file}")

def create_startup_script():
    """创建云端启动脚本"""
    print("\n📜 创建云端启动脚本...")
    
    startup_script = """#!/bin/bash
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
"""
    
    script_file = 'start_cloud.sh'
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(startup_script)
    
    # 设置执行权限
    os.chmod(script_file, 0o755)
    
    print(f"📜 启动脚本已创建: {script_file}")
    print("使用方法: bash start_cloud.sh")

def generate_troubleshooting_guide():
    """生成故障排除指南"""
    print("\n📋 生成故障排除指南...")
    
    guide = """
# 云端部署故障排除指南

## 常见问题及解决方案

### 1. 评估结果无法保存
**症状**: 前端评估完成后，历史记录中没有数据
**原因**: 字段映射问题已修复
**验证**: 
```bash
curl -X POST http://localhost:5001/api/evaluation-history \\
  -H "Content-Type: application/json" \\
  -d '{
    "user_input": "测试问题",
    "model_answer": "测试答案",
    "total_score": 8.0,
    "evaluation_criteria": "测试标准"
  }'
```

### 2. 前端无法连接后端
**症状**: 网络错误或CORS错误
**解决方案**:
1. 检查后端是否启动: `curl http://服务器IP:5001/health`
2. 检查防火墙设置: `sudo ufw allow 5001`
3. 确认IP地址正确: `hostname -I`

### 3. 依赖包问题
**症状**: 导入错误或模块不存在
**解决方案**:
```bash
source venv/bin/activate
pip install -r requirements.txt
pip list | grep -E "(flask|sqlalchemy|openai)"
```

### 4. 数据库问题
**症状**: 数据库文件不存在或表结构错误
**解决方案**:
```bash
python quick_init.py
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 5. 端口占用
**症状**: 地址已在使用
**解决方案**:
```bash
sudo lsof -i :5001
sudo kill -9 PID号
```

## 部署检查清单

- [ ] 虚拟环境已创建并激活
- [ ] 依赖包已安装
- [ ] 数据库已初始化
- [ ] 后端服务可正常启动
- [ ] 健康检查接口正常: /health
- [ ] 评估历史保存接口正常: POST /api/evaluation-history
- [ ] 前端环境变量已配置
- [ ] 防火墙端口已开放

## 联系支持
如果问题仍未解决，请提供：
- 错误日志完整信息
- 服务器环境信息（OS、Python版本）
- 网络配置信息
"""
    
    guide_file = 'CLOUD_TROUBLESHOOTING.md'
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"📖 故障排除指南已创建: {guide_file}")

def main():
    """主函数"""
    print("🔧 云端部署问题一键修复工具")
    print("=" * 60)
    
    # 1. 检查环境
    env_ok = check_environment()
    
    # 2. 测试API
    if env_ok:
        api_ok = test_backend_api()
    else:
        api_ok = False
    
    # 3. 生成配置修复方案
    fix_frontend_config()
    
    # 4. 创建启动脚本
    create_startup_script()
    
    # 5. 生成故障排除指南
    generate_troubleshooting_guide()
    
    print("\n" + "=" * 60)
    
    if env_ok and api_ok:
        print("🎉 后端修复完成！数据保存问题已解决。")
        print("\n📋 接下来的步骤:")
        print("1. 使用启动脚本: bash start_cloud.sh")
        print("2. 配置前端环境变量（参考 cloud_frontend_config.md）")
        print("3. 测试完整的评估流程")
    else:
        print("⚠️  检测到问题，请查看上述错误信息并参考故障排除指南")
    
    print(f"\n📄 生成的文件:")
    print("  - start_cloud.sh (启动脚本)")
    print("  - cloud_frontend_config.md (前端配置)")
    print("  - CLOUD_TROUBLESHOOTING.md (故障排除)")

if __name__ == '__main__':
    main() 