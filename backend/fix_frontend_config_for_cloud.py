#!/usr/bin/env python3
"""
修复前端配置脚本 - 解决云端部署时localhost问题
"""

import os
import json
import shutil
from datetime import datetime

def get_server_ip():
    """获取服务器IP地址"""
    try:
        import socket
        # 连接到外部地址来获取本机IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        return ip
    except:
        return "YOUR_SERVER_IP"

def check_frontend_config():
    """检查当前前端配置"""
    print("🔍 检查当前前端配置...")
    
    frontend_path = '../frontend'
    if not os.path.exists(frontend_path):
        print(f"❌ 前端目录不存在: {frontend_path}")
        return False
    
    issues = []
    
    # 检查环境变量文件
    env_file = os.path.join(frontend_path, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if 'localhost' in content:
                issues.append(f"❌ .env文件包含localhost配置")
                print(f"   当前内容: {content.strip()}")
    
    # 检查package.json
    package_json = os.path.join(frontend_path, 'package.json')
    if os.path.exists(package_json):
        with open(package_json, 'r') as f:
            package_data = json.load(f)
            if 'proxy' in package_data and 'localhost' in package_data['proxy']:
                issues.append(f"❌ package.json包含localhost代理配置")
                print(f"   当前代理: {package_data['proxy']}")
    
    # 检查服务文件
    service_file = os.path.join(frontend_path, 'src/services/evaluationService.js')
    if os.path.exists(service_file):
        with open(service_file, 'r') as f:
            content = f.read()
            if 'localhost' in content:
                issues.append(f"❌ evaluationService.js包含localhost配置")
    
    if issues:
        print(f"🚨 发现 {len(issues)} 个配置问题:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ 前端配置检查通过")
        return True

def fix_frontend_config(server_ip=None):
    """修复前端配置"""
    print("\n🔧 修复前端配置...")
    
    if not server_ip:
        server_ip = get_server_ip()
        print(f"🌐 检测到服务器IP: {server_ip}")
    
    frontend_path = '../frontend'
    backup_suffix = f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 修复 .env 文件
    env_file = os.path.join(frontend_path, '.env')
    if os.path.exists(env_file):
        # 备份原文件
        shutil.copy(env_file, f"{env_file}{backup_suffix}")
        print(f"📄 已备份 .env 文件")
        
        # 读取并修改
        with open(env_file, 'r') as f:
            content = f.read()
        
        # 替换localhost为实际IP
        new_content = content.replace('localhost', server_ip)
        
        with open(env_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ 已更新 .env 文件:")
        print(f"   REACT_APP_API_URL=http://{server_ip}:5001/api")
    
    # 修复 package.json 代理配置
    package_json = os.path.join(frontend_path, 'package.json')
    if os.path.exists(package_json):
        # 备份原文件
        shutil.copy(package_json, f"{package_json}{backup_suffix}")
        print(f"📄 已备份 package.json 文件")
        
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        
        # 修改代理配置
        if 'proxy' in package_data:
            old_proxy = package_data['proxy']
            package_data['proxy'] = f"http://{server_ip}:5001"
            
            with open(package_json, 'w') as f:
                json.dump(package_data, f, indent=2)
            
            print(f"✅ 已更新 package.json 代理配置:")
            print(f"   从: {old_proxy}")
            print(f"   到: {package_data['proxy']}")

def create_cloud_env_file(server_ip=None):
    """创建云端专用的环境变量文件"""
    if not server_ip:
        server_ip = get_server_ip()
    
    frontend_path = '../frontend'
    cloud_env_content = f"""# 云端部署环境变量配置
REACT_APP_API_URL=http://{server_ip}:5001/api
GENERATE_SOURCEMAP=false

# 如果需要禁用代理，请在package.json中移除proxy配置
"""
    
    # 创建 .env.production 文件
    env_prod_file = os.path.join(frontend_path, '.env.production')
    with open(env_prod_file, 'w') as f:
        f.write(cloud_env_content)
    
    print(f"📄 已创建云端环境变量文件: .env.production")
    print(f"   内容: REACT_APP_API_URL=http://{server_ip}:5001/api")

def create_start_commands():
    """创建启动命令脚本"""
    print("\n📜 创建前端启动脚本...")
    
    server_ip = get_server_ip()
    
    # 开发环境启动脚本
    dev_script = f"""#!/bin/bash
# 前端开发环境启动脚本（云端版）

echo "🚀 启动前端开发服务器（云端版）..."

cd ../frontend

# 设置环境变量
export REACT_APP_API_URL=http://{server_ip}:5001/api
echo "🌐 API地址设置为: $REACT_APP_API_URL"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "🎯 启动前端服务器..."
npm start
"""
    
    # 生产环境启动脚本
    prod_script = f"""#!/bin/bash
# 前端生产环境启动脚本

echo "🏗️  构建前端生产版本..."

cd ../frontend

# 设置环境变量
export REACT_APP_API_URL=http://{server_ip}:5001/api
export NODE_ENV=production

# 构建
npm run build

echo "✅ 前端构建完成，输出目录: build/"
echo "📋 可以使用以下命令启动静态服务器:"
echo "   npx serve -s build -p 3000"
"""
    
    # 保存脚本
    with open('start_frontend_dev.sh', 'w') as f:
        f.write(dev_script)
    
    with open('start_frontend_prod.sh', 'w') as f:
        f.write(prod_script)
    
    # 设置执行权限
    os.chmod('start_frontend_dev.sh', 0o755)
    os.chmod('start_frontend_prod.sh', 0o755)
    
    print(f"📜 已创建前端启动脚本:")
    print(f"   - start_frontend_dev.sh (开发环境)")
    print(f"   - start_frontend_prod.sh (生产环境)")

def verify_fix():
    """验证修复结果"""
    print("\n🧪 验证修复结果...")
    
    frontend_path = '../frontend'
    
    # 检查 .env 文件
    env_file = os.path.join(frontend_path, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
            if 'localhost' not in content:
                print("✅ .env 文件已修复")
            else:
                print("❌ .env 文件仍包含localhost")
    
    # 检查 package.json
    package_json = os.path.join(frontend_path, 'package.json')
    if os.path.exists(package_json):
        with open(package_json, 'r') as f:
            package_data = json.load(f)
            if 'proxy' in package_data and 'localhost' not in package_data['proxy']:
                print("✅ package.json 代理配置已修复")
            elif 'proxy' not in package_data:
                print("✅ package.json 无代理配置（使用环境变量）")
            else:
                print("❌ package.json 代理配置仍包含localhost")

def main():
    """主函数"""
    print("🔧 前端配置云端部署修复工具")
    print("=" * 50)
    
    # 1. 检查当前配置
    config_ok = check_frontend_config()
    
    if not config_ok:
        print("\n🚨 检测到前端配置问题，需要修复！")
        
        # 获取服务器IP
        server_ip = get_server_ip()
        print(f"\n🌐 将使用服务器IP: {server_ip}")
        
        if server_ip == "YOUR_SERVER_IP":
            print("⚠️  无法自动检测服务器IP，请手动输入:")
            server_ip = input("请输入云端服务器IP地址: ").strip()
        
        # 2. 修复配置
        fix_frontend_config(server_ip)
        
        # 3. 创建云端环境变量文件
        create_cloud_env_file(server_ip)
        
        # 4. 创建启动脚本
        create_start_commands()
        
        # 5. 验证修复
        verify_fix()
        
        print("\n" + "=" * 50)
        print("🎉 前端配置修复完成！")
        
        print(f"\n📋 接下来的步骤:")
        print(f"1. 重启前端服务:")
        print(f"   bash start_frontend_dev.sh")
        print(f"")
        print(f"2. 或者手动设置环境变量:")
        print(f"   export REACT_APP_API_URL=http://{server_ip}:5001/api")
        print(f"   cd ../frontend && npm start")
        print(f"")
        print(f"3. 在浏览器中访问: http://{server_ip}:3000")
        print(f"4. 测试评估功能，检查Chrome开发者工具中的网络请求")
        
    else:
        print("\n✅ 前端配置正常，无需修复")
    
    print(f"\n💡 提示:")
    print(f"   - 如果问题仍然存在，请检查防火墙设置")
    print(f"   - 确保端口 5001 和 3000 已开放")
    print(f"   - 使用Chrome开发者工具检查网络请求")

if __name__ == '__main__':
    main() 