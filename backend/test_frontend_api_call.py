#!/usr/bin/env python3
"""
模拟前端API调用测试脚本
测试前端应该如何调用后端API
"""

import requests
import json
import time
from datetime import datetime

# 后端API地址
API_BASE_URL = "http://9.135.87.101:7860/api"

def test_api_call(endpoint, method="GET", data=None, description=""):
    """测试API调用"""
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://9.135.87.101:8701'  # 模拟前端Origin
    }
    
    print(f"\n🧪 测试 {description}")
    print(f"   {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
            
        print(f"   ✅ 状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                if isinstance(json_data, dict):
                    if 'success' in json_data:
                        print(f"   📊 success: {json_data['success']}")
                    if 'message' in json_data:
                        print(f"   💬 message: {json_data['message']}")
                    if 'data' in json_data:
                        print(f"   📦 data keys: {list(json_data['data'].keys()) if isinstance(json_data['data'], dict) else 'array'}")
                elif isinstance(json_data, list):
                    print(f"   📊 数组长度: {len(json_data)}")
            except:
                print(f"   📄 响应长度: {len(response.text)} 字符")
        else:
            print(f"   ❌ 错误: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ 异常: {e}")
        return False

def simulate_evaluation_workflow():
    """模拟完整的评估流程"""
    print("🎯 模拟前端评估流程")
    print("="*50)
    
    # 1. 健康检查
    if not test_api_call("/health", "GET", None, "健康检查"):
        print("❌ 健康检查失败")
        return False
    
    # 2. 获取分类标准
    if not test_api_call("/classification-standards", "GET", None, "获取分类标准"):
        print("❌ 获取分类标准失败")
        return False
    
    # 3. 获取评估标准
    if not test_api_call("/evaluation-standards", "GET", None, "获取评估标准"):
        print("❌ 获取评估标准失败")
        return False
    
    # 4. 进行评估（这是核心流程）
    evaluation_data = {
        "user_input": "什么是人工智能？",
        "model_answer": "人工智能是一种通过机器学习和算法实现智能行为的技术。",
        "reference_answer": "人工智能是模拟人类智能的技术。",
        "question_time": datetime.now().isoformat(),
        "evaluation_criteria": "请评估答案的准确性、完整性和有用性"
    }
    
    if not test_api_call("/evaluate", "POST", evaluation_data, "AI评估"):
        print("❌ AI评估失败")
        return False
    
    # 5. 获取评估历史
    if not test_api_call("/evaluation-history", "GET", None, "获取评估历史"):
        print("❌ 获取评估历史失败")
        return False
    
    # 6. 手动保存评估历史（模拟前端保存逻辑）
    history_data = {
        "user_input": "测试保存历史记录",
        "model_answer": "这是一个测试答案",
        "reference_answer": "",
        "question_time": datetime.now().isoformat(),
        "evaluation_criteria": "测试评估标准",
        "total_score": 7.5,
        "dimensions": {"准确性": 8, "完整性": 7, "流畅性": 8},
        "reasoning": "测试评估理由",
        "raw_response": "测试原始响应"
    }
    
    if not test_api_call("/evaluation-history", "POST", history_data, "保存评估历史"):
        print("❌ 保存评估历史失败")
        return False
    
    print("\n✅ 所有API调用都成功！")
    return True

def test_cors_preflight():
    """测试CORS预检请求"""
    print("\n🔍 测试CORS预检请求")
    
    url = f"{API_BASE_URL}/evaluation-history"
    headers = {
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
        'Origin': 'http://9.135.87.101:8701'
    }
    
    try:
        response = requests.options(url, headers=headers, timeout=10)
        print(f"   预检请求状态码: {response.status_code}")
        
        cors_headers = {
            'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
            'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
            'access-control-allow-headers': response.headers.get('access-control-allow-headers')
        }
        
        print("   CORS头信息:")
        for header, value in cors_headers.items():
            print(f"     {header}: {value or '未设置'}")
            
        return response.status_code in [200, 204]
        
    except Exception as e:
        print(f"   ❌ CORS预检失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始模拟前端API调用测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API地址: {API_BASE_URL}")
    
    # 测试CORS预检
    cors_ok = test_cors_preflight()
    
    # 测试完整评估流程
    workflow_ok = simulate_evaluation_workflow()
    
    print("\n" + "="*50)
    print("📋 测试结果总结")
    print("="*50)
    print(f"🔗 CORS预检: {'✅' if cors_ok else '❌'}")
    print(f"🎯 评估流程: {'✅' if workflow_ok else '❌'}")
    
    if cors_ok and workflow_ok:
        print("\n✅ 后端API完全正常，前端应该能正常调用")
        print("💡 如果前端仍有问题，建议：")
        print("   1. 检查浏览器开发者工具Network标签")
        print("   2. 确认前端的API调用代码")
        print("   3. 检查环境变量是否正确设置")
    else:
        print("\n❌ 发现问题，请检查后端服务") 