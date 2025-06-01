#!/usr/bin/env python3
"""
测试评估API的脚本
验证/api/evaluate接口是否正常工作
"""

import requests
import json
import sys
from datetime import datetime

def test_evaluate_api():
    """测试评估API"""
    
    # API地址
    api_url = 'http://localhost:5001/api/evaluate'
    
    # 测试数据
    test_data = {
        'user_input': '中国平安的股价走势如何？',
        'model_answer': '中国平安(601318.SH)的股价近期呈现震荡走势。从技术面来看，股价在25-30元区间波动，成交量相对稳定。基本面方面，公司2023年业绩稳健，寿险业务增长良好。',
        'reference_answer': '中国平安股价受市场情绪和基本面双重影响，需要结合具体时点分析。建议关注公司财报和行业政策变化。',
        'question_time': '2024-03-15 10:30:00',
        'evaluation_criteria': '准确性\t分析是否基于实际数据\t0-4分：完全准确=4分；基本准确=2分；有误导=0分\n完整性\t是否覆盖技术面和基本面\t0-3分：全面覆盖=3分；部分覆盖=1分；不完整=0分\n时效性\t信息是否符合问题时点\t0-2分：时效性强=2分；一般=1分；过时=0分\n安全性\t避免投资建议风险\t0-1分：合规=1分；有风险=0分',
        'scoring_prompt': '''请根据以下评估标准对股票分析回答进行评分：

评估标准：
{evaluation_criteria}

评估信息：
问题时间: {question_time}
用户问题: {user_input}
模型回答: {model_answer}
参考答案: {reference_answer}

请严格按照以下格式返回评估结果:
总分: [分数]/10
评分理由: [详细的评分分析]'''
    }
    
    print("🧪 开始测试评估API...")
    print(f"📡 请求地址: {api_url}")
    print(f"📋 测试数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print("-" * 80)
    
    try:
        # 发送POST请求
        response = requests.post(
            api_url,
            json=test_data,
            headers={'Content-Type': 'application/json'},
            timeout=180  # 3分钟超时
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 评估API测试成功!")
            print(f"📈 评估结果:")
            print(f"   总分: {result.get('score', 'N/A')}")
            print(f"   评分理由: {result.get('reasoning', 'N/A')[:200]}...")
            print(f"   使用模型: {result.get('model_used', 'N/A')}")
            print(f"   评估耗时: {result.get('evaluation_time_seconds', 'N/A')}秒")
            
            if 'classification' in result:
                classification = result['classification']
                print(f"   分类结果: {classification.get('level1', 'N/A')} → {classification.get('level2', 'N/A')} → {classification.get('level3', 'N/A')}")
            
            return True
        else:
            print(f"❌ 评估API测试失败!")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时！大模型可能需要更长时间处理。")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器！请确保后端服务正在运行。")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False

def test_health_check():
    """测试健康检查接口"""
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=10)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"服务信息: {response.json()}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始测试后端API...")
    print("=" * 80)
    
    # 首先测试健康检查
    print("1. 测试健康检查接口...")
    if not test_health_check():
        print("💀 健康检查失败，请检查后端服务是否正常运行。")
        sys.exit(1)
    
    print("\n2. 测试评估接口...")
    if test_evaluate_api():
        print("\n🎉 所有测试通过！评估API工作正常。")
    else:
        print("\n💀 评估API测试失败！")
        sys.exit(1) 