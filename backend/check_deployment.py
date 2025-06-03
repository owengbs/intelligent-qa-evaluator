#!/usr/bin/env python3
"""
部署检查脚本
验证智能Q&A评估系统的部署状态，确保所有组件正常工作
"""

import os
import sys
import json
import sqlite3
from datetime import datetime

def check_environment():
    """检查基础环境"""
    print("🔍 检查基础环境...")
    issues = []
    
    # 检查Python版本
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info < (3, 8):
        issues.append(f"❌ Python版本过低: {py_version} (需要3.8+)")
    else:
        print(f"✅ Python版本: {py_version}")
    
    # 检查必要的目录
    required_dirs = ['data', 'logs', 'scripts']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"✅ 创建目录: {dir_name}")
            except Exception as e:
                issues.append(f"❌ 无法创建目录 {dir_name}: {e}")
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    # 检查必要的文件
    required_files = ['app.py', 'config.py', 'requirements.txt']
    for file_name in required_files:
        if not os.path.exists(file_name):
            issues.append(f"❌ 缺少文件: {file_name}")
        else:
            print(f"✅ 文件存在: {file_name}")
    
    return issues

def check_dependencies():
    """检查Python依赖"""
    print("\n🔍 检查Python依赖...")
    issues = []
    
    # 必要的依赖包
    required_packages = [
        'flask', 'flask_cors', 'flask_sqlalchemy', 
        'sqlalchemy', 'requests', 'openai'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            issues.append(f"❌ 缺少依赖: {package}")
    
    return issues

def check_database():
    """检查数据库状态"""
    print("\n🔍 检查数据库状态...")
    issues = []
    
    db_path = os.path.join('data', 'qa_evaluator.db')
    
    # 检查数据库文件
    if not os.path.exists(db_path):
        issues.append(f"❌ 数据库文件不存在: {db_path}")
        return issues
    
    print(f"✅ 数据库文件存在: {db_path}")
    
    # 检查数据库表和数据
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查必要的表
        required_tables = [
            'classification_standards',
            'evaluation_standards', 
            'evaluation_history'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ 表存在: {table}")
                
                # 检查表中的数据
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if table in ['classification_standards', 'evaluation_standards'] and count == 0:
                    issues.append(f"⚠️  表为空，需要初始化默认数据")
                else:
                    print(f"  └─ 数据量: {count} 条")
            else:
                issues.append(f"❌ 缺少表: {table}")
        
        # 检查评估历史表结构（人工评估字段）
        cursor.execute("PRAGMA table_info(evaluation_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        human_eval_columns = [
            'human_total_score', 'human_dimensions_json', 'human_reasoning',
            'human_evaluation_by', 'human_evaluation_time', 'is_human_modified'
        ]
        
        missing_columns = [col for col in human_eval_columns if col not in columns]
        if missing_columns:
            issues.append(f"⚠️  缺少人工评估字段: {', '.join(missing_columns)}")
        else:
            print("✅ 人工评估字段完整")
        
        conn.close()
        
    except Exception as e:
        issues.append(f"❌ 数据库检查失败: {e}")
    
    return issues

def check_flask_app():
    """检查Flask应用"""
    print("\n🔍 检查Flask应用...")
    issues = []
    
    try:
        # 尝试导入应用
        from app import app
        from models.classification import db, ClassificationStandard, EvaluationStandard, EvaluationHistory
        
        with app.app_context():
            # 检查数据库连接
            try:
                cs_count = ClassificationStandard.query.count()
                es_count = EvaluationStandard.query.count()
                eh_count = EvaluationHistory.query.count()
                
                print(f"✅ Flask应用正常，数据库连接成功")
                print(f"  └─ 分类标准: {cs_count} 条")
                print(f"  └─ 评估标准: {es_count} 条")
                print(f"  └─ 评估历史: {eh_count} 条")
                
                if cs_count == 0 or es_count == 0:
                    issues.append("⚠️  配置数据为空，建议运行: python quick_init.py")
                
            except Exception as e:
                issues.append(f"❌ 数据库查询失败: {e}")
                
    except Exception as e:
        issues.append(f"❌ Flask应用导入失败: {e}")
    
    return issues

def check_config_data():
    """检查配置数据"""
    print("\n🔍 检查配置数据...")
    issues = []
    
    config_dir = os.path.join('scripts', 'config_data')
    if os.path.exists(config_dir):
        print(f"✅ 配置数据目录存在: {config_dir}")
        
        # 检查配置文件
        config_files = [
            'classification_standards.json',
            'evaluation_standards.json',
            'export_summary.json'
        ]
        
        for file_name in config_files:
            file_path = os.path.join(config_dir, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if 'count' in data:
                        print(f"✅ {file_name} ({data.get('count', 0)} 条记录)")
                    else:
                        print(f"✅ {file_name}")
                        
                except Exception as e:
                    issues.append(f"❌ 配置文件格式错误 {file_name}: {e}")
            else:
                issues.append(f"⚠️  配置文件不存在: {file_name}")
    else:
        issues.append(f"⚠️  配置数据目录不存在: {config_dir}")
    
    return issues

def check_api_endpoints():
    """检查API端点（需要服务运行）"""
    print("\n🔍 检查API端点...")
    issues = []
    
    try:
        import requests
        import time
        
        # 启动应用进行测试（这里只是导入检查）
        from app import app
        
        # 检查关键路由是否定义
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint not in ['static']:
                routes.append(f"{rule.rule} ({', '.join(rule.methods)})")
        
        if routes:
            print(f"✅ API路由已定义 ({len(routes)} 条)")
            for route in routes[:5]:  # 显示前5条
                print(f"  └─ {route}")
            if len(routes) > 5:
                print(f"  └─ ... 还有 {len(routes) - 5} 条路由")
        else:
            issues.append("❌ 未找到API路由定义")
            
    except Exception as e:
        issues.append(f"❌ API检查失败: {e}")
    
    return issues

def generate_report(all_issues):
    """生成检查报告"""
    print("\n" + "=" * 60)
    print("📋 部署状态报告")
    print("=" * 60)
    
    if not all_issues:
        print("🎉 恭喜！部署检查全部通过，系统可以正常使用。")
        print("\n✅ 建议下一步操作：")
        print("1. 启动后端服务: python app.py")
        print("2. 启动前端服务: cd ../frontend && npm start")
        print("3. 访问系统: http://localhost:3000")
        return True
    else:
        print(f"⚠️  发现 {len(all_issues)} 个问题需要解决：")
        print()
        
        # 按严重程度分类
        critical_issues = [issue for issue in all_issues if issue.startswith("❌")]
        warnings = [issue for issue in all_issues if issue.startswith("⚠️")]
        
        if critical_issues:
            print("🚨 严重问题（必须解决）：")
            for issue in critical_issues:
                print(f"   {issue}")
            print()
        
        if warnings:
            print("⚠️  警告（建议解决）：")
            for issue in warnings:
                print(f"   {issue}")
            print()
        
        # 提供解决建议
        print("💡 解决建议：")
        if any("数据库" in issue for issue in all_issues):
            print("   - 运行数据库初始化: python quick_init.py")
        if any("依赖" in issue for issue in all_issues):
            print("   - 安装依赖: pip install -r requirements.txt")
        if any("配置数据" in issue for issue in all_issues):
            print("   - 导入配置数据: cd scripts && python import_config_data.py --full-replace")
        
        return False

def main():
    """主函数"""
    print("🚀 智能Q&A评估系统 - 部署状态检查")
    print("=" * 60)
    
    all_issues = []
    
    # 执行所有检查
    all_issues.extend(check_environment())
    all_issues.extend(check_dependencies())
    all_issues.extend(check_database())
    all_issues.extend(check_flask_app())
    all_issues.extend(check_config_data())
    all_issues.extend(check_api_endpoints())
    
    # 生成报告
    success = generate_report(all_issues)
    
    # 保存检查结果
    result = {
        'timestamp': datetime.now().isoformat(),
        'success': success,
        'issues_count': len(all_issues),
        'issues': all_issues
    }
    
    try:
        with open('deployment_check_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📄 检查结果已保存: deployment_check_result.json")
    except Exception as e:
        print(f"\n⚠️  无法保存检查结果: {e}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 