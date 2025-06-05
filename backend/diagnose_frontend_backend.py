#!/usr/bin/env python3
"""
前后端连接问题诊断脚本
专门解决生产环境前端无法正确请求后端接口的问题
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime

def print_header(title):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_backend_health():
    """检查后端健康状态"""
    print_header("检查后端健康状态")
    
    backend_url = "http://9.135.87.101:7860"
    health_url = f"{backend_url}/health"
    api_url = f"{backend_url}/api/health"
    
    print(f"🌐 后端地址: {backend_url}")
    print(f"🔗 健康检查地址: {health_url}")
    print(f"🔗 API健康检查地址: {api_url}")
    
    try:
        # 检查基础健康接口
        response = requests.get(health_url, timeout=10)
        print(f"✅ 基础健康检查: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 检查API健康接口
        try:
            api_response = requests.get(api_url, timeout=10)
            print(f"✅ API健康检查: {api_response.status_code}")
            print(f"   响应: {api_response.json()}")
        except Exception as e:
            print(f"⚠️  API健康检查失败: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ 后端健康检查失败: {e}")
        return False

def check_frontend_config():
    """检查前端配置"""
    print_header("检查前端配置")
    
    frontend_dir = "../frontend"
    if not os.path.exists(frontend_dir):
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return False
    
    # 检查环境配置文件
    env_file = os.path.join(frontend_dir, ".env.production")
    if os.path.exists(env_file):
        print(f"✅ 找到环境配置文件: {env_file}")
        with open(env_file, 'r') as f:
            content = f.read()
            print("📋 环境配置内容:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"   {line}")
    else:
        print(f"❌ 环境配置文件不存在: {env_file}")
        
    # 检查构建文件中的API配置
    build_dir = os.path.join(frontend_dir, "build")
    if os.path.exists(build_dir):
        print(f"✅ 找到构建目录: {build_dir}")
        
        # 查找主要的JS文件
        try:
            result = subprocess.run(
                ["find", build_dir, "-name", "*.js", "-type", "f"],
                capture_output=True, text=True, cwd=frontend_dir
            )
            
            if result.returncode == 0:
                js_files = result.stdout.strip().split('\n')
                main_js = next((f for f in js_files if 'main.' in f), js_files[0] if js_files else None)
                
                if main_js:
                    print(f"🔍 检查构建文件: {main_js}")
                    
                    # 检查API地址
                    try:
                        grep_result = subprocess.run(
                            ["grep", "-o", "http://[^\"']*api", main_js],
                            capture_output=True, text=True
                        )
                        
                        if grep_result.returncode == 0:
                            api_urls = grep_result.stdout.strip().split('\n')
                            print("📍 构建文件中的API地址:")
                            for url in set(api_urls[:3]):  # 去重并显示前3个
                                print(f"   {url}")
                        else:
                            print("⚠️  未在构建文件中找到API地址")
                            
                    except Exception as e:
                        print(f"⚠️  检查构建文件失败: {e}")
                        
        except Exception as e:
            print(f"⚠️  查找JS文件失败: {e}")
    else:
        print(f"❌ 构建目录不存在: {build_dir}")
        
    return True

def check_frontend_status():
    """检查前端服务状态"""
    print_header("检查前端服务状态")
    
    frontend_url = "http://9.135.87.101:8701"
    print(f"🌐 前端地址: {frontend_url}")
    
    try:
        response = requests.get(frontend_url, timeout=10)
        print(f"✅ 前端服务状态: {response.status_code}")
        
        # 检查响应头
        print("📋 响应头信息:")
        important_headers = ['content-type', 'access-control-allow-origin', 'server']
        for header in important_headers:
            value = response.headers.get(header)
            if value:
                print(f"   {header}: {value}")
                
        return True
        
    except Exception as e:
        print(f"❌ 前端服务检查失败: {e}")
        return False

def test_api_endpoints():
    """测试关键API接口"""
    print_header("测试关键API接口")
    
    base_url = "http://9.135.87.101:7860/api"
    
    # 测试接口列表
    endpoints = [
        ("GET", "/health", None, "健康检查"),
        ("GET", "/classification-standards", None, "分类标准"),
        ("GET", "/evaluation-standards", None, "评估标准"),
        ("GET", "/evaluation-history", None, "评估历史"),
    ]
    
    results = []
    for method, path, data, description in endpoints:
        url = f"{base_url}{path}"
        print(f"🧪 测试 {description}: {method} {url}")
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=10)
                
            print(f"   ✅ 状态码: {response.status_code}")
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if isinstance(json_response, dict):
                        print(f"   📊 响应字段: {list(json_response.keys())}")
                    elif isinstance(json_response, list):
                        print(f"   📊 响应数组长度: {len(json_response)}")
                except:
                    print(f"   📄 响应长度: {len(response.text)} 字符")
                    
            results.append((description, True, response.status_code))
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            results.append((description, False, str(e)))
    
    return results

def test_cors():
    """测试CORS配置"""
    print_header("测试CORS配置")
    
    api_url = "http://9.135.87.101:7860/api/health"
    
    # 模拟前端发起的带Origin的请求
    headers = {
        'Origin': 'http://9.135.87.101:8701',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        print(f"✅ CORS测试响应: {response.status_code}")
        
        cors_headers = [
            'access-control-allow-origin',
            'access-control-allow-methods', 
            'access-control-allow-headers'
        ]
        
        print("📋 CORS响应头:")
        for header in cors_headers:
            value = response.headers.get(header)
            if value:
                print(f"   {header}: {value}")
            else:
                print(f"   {header}: 未设置")
                
        # 检查是否允许前端域名
        allow_origin = response.headers.get('access-control-allow-origin')
        if allow_origin == '*' or allow_origin == 'http://9.135.87.101:8701':
            print("✅ CORS配置允许前端访问")
            return True
        else:
            print(f"⚠️  CORS可能不允许前端访问: {allow_origin}")
            return False
            
    except Exception as e:
        print(f"❌ CORS测试失败: {e}")
        return False

def generate_diagnostic_report():
    """生成诊断报告"""
    print_header("生成诊断报告")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'backend_healthy': False,
        'frontend_healthy': False,
        'cors_ok': False,
        'api_endpoints': [],
        'recommendations': []
    }
    
    # 执行各项检查
    report['backend_healthy'] = check_backend_health()
    time.sleep(1)
    
    report['frontend_healthy'] = check_frontend_status()
    time.sleep(1)
    
    check_frontend_config()
    time.sleep(1)
    
    report['api_endpoints'] = test_api_endpoints()
    time.sleep(1)
    
    report['cors_ok'] = test_cors()
    
    # 生成建议
    if not report['backend_healthy']:
        report['recommendations'].append("❌ 后端服务未正常运行，请检查后端启动状态")
        
    if not report['frontend_healthy']:
        report['recommendations'].append("❌ 前端服务未正常运行，请检查前端启动状态")
        
    if not report['cors_ok']:
        report['recommendations'].append("⚠️  CORS配置可能有问题，请检查后端CORS设置")
        
    failed_apis = [ep for ep in report['api_endpoints'] if not ep[1]]
    if failed_apis:
        report['recommendations'].append(f"⚠️  部分API接口异常: {[ep[0] for ep in failed_apis]}")
        
    if not report['recommendations']:
        report['recommendations'].append("✅ 所有检查都正常，前后端连接应该没有问题")
        
    # 输出报告
    print("\n" + "="*60)
    print("📋 诊断报告摘要")
    print("="*60)
    
    print(f"🕐 检查时间: {report['timestamp']}")
    print(f"🔧 后端健康: {'✅' if report['backend_healthy'] else '❌'}")
    print(f"🌐 前端健康: {'✅' if report['frontend_healthy'] else '❌'}")
    print(f"🔗 CORS配置: {'✅' if report['cors_ok'] else '❌'}")
    
    print(f"\n📊 API接口测试结果:")
    for name, success, status in report['api_endpoints']:
        print(f"   {name}: {'✅' if success else '❌'} {status}")
        
    print(f"\n💡 建议:")
    for recommendation in report['recommendations']:
        print(f"   {recommendation}")
        
    # 保存报告
    report_file = f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 完整报告已保存: {report_file}")
    
    return report

if __name__ == "__main__":
    print("🔍 开始前后端连接诊断...")
    print(f"📅 诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    report = generate_diagnostic_report()
    
    print("\n" + "="*60)
    print("🎯 诊断完成")
    print("="*60)
    
    if report['backend_healthy'] and report['frontend_healthy'] and report['cors_ok']:
        print("✅ 前后端连接配置正常，如果仍有问题，可能是前端代码中的API调用逻辑问题")
        print("💡 建议检查浏览器开发者工具的Network标签，查看实际的API请求情况")
    else:
        print("❌ 发现配置问题，请根据上述建议进行修复")
        
    print(f"\n📄 详细诊断报告: {os.path.abspath('.')}") 