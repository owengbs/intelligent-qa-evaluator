#!/usr/bin/env python3
"""
测试LLM API连接的脚本
"""
import os
import requests
import json
from services.llm_client import LLMClient

def test_direct_api():
    """直接测试API调用"""
    print("🔍 直接测试LLM API调用...")
    
    api_base = os.getenv('LLM_API_BASE', "http://v2.open.venus.oa.com/llmproxy")
    api_key = os.getenv('LLM_API_KEY', "xxBZykeTGIVeqyGNaxNoMDro@2468")
    
    print(f"📍 API Base: {api_base}")
    print(f"🔑 API Key: {api_key[:10]}...")
    
    url = f"{api_base}/chat/completions"
    print(f"🌐 完整URL: {url}")
    
    data = {
        "model": "deepseek-v3-local-II",
        "messages": [{"role": "user", "content": "Hello, 测试一下API连接"}],
        "max_tokens": 100,
        "temperature": 0.1
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("📤 发送API请求...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"📊 状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        print(f"📄 响应内容: {response.text[:500]}")
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result:
                print(f"✅ API调用成功！回答: {result['choices'][0]['message']['content']}")
            else:
                print(f"❌ 响应格式错误: {result}")
        else:
            print(f"❌ API调用失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"💥 请求异常: {str(e)}")
        import traceback
        traceback.print_exc()

def test_llm_client():
    """测试LLM客户端"""
    print("\n🔍 测试LLM客户端...")
    
    try:
        client = LLMClient()
        print(f"✅ LLM客户端创建成功")
        print(f"📍 API Base: {client.api_base}")
        print(f"🔑 API Key: {client.api_key[:10]}...")
        
        response = client.dialog("你好，请回答测试问题", task_type='evaluation')
        print(f"✅ LLM客户端调用成功！回答: {response[:100]}...")
        
    except Exception as e:
        print(f"💥 LLM客户端调用失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始LLM API连接测试...\n")
    
    # 检查环境变量
    print("📋 环境变量检查:")
    for key in ['LLM_API_BASE', 'LLM_API_KEY', 'LLM_MODEL']:
        value = os.getenv(key, 'Not Set')
        if key == 'LLM_API_KEY' and value != 'Not Set':
            value = value[:10] + "..."
        print(f"   {key}: {value}")
    print()
    
    # 测试直接API调用
    test_direct_api()
    
    # 测试LLM客户端
    test_llm_client()
    
    print("\n🎯 测试完成") 