#!/usr/bin/env python3
"""
快速修复POST /api/evaluation-history 405错误的脚本
避免函数名冲突，直接在app.py中添加缺失的路由
"""

import os
import sys
import re

def fix_post_route():
    """在app.py中添加缺失的POST路由"""
    print("🔧 修复POST /api/evaluation-history 405错误...")
    
    try:
        app_py_path = 'app.py'
        if not os.path.exists(app_py_path):
            print("❌ 找不到app.py文件")
            return False
        
        # 读取文件
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有POST路由（除了human-evaluation）
        if "methods=['POST']" in content and "/api/evaluation-history" in content:
            # 进一步检查是否为评估历史的POST路由
            lines = content.split('\n')
            has_post_route = False
            
            for i, line in enumerate(lines):
                if "'/api/evaluation-history'" in line and "methods=['POST']" in line:
                    has_post_route = True
                    break
            
            if has_post_route:
                print("✅ POST /api/evaluation-history路由已存在")
                return True
        
        # 添加POST路由，使用不同的函数名避免冲突
        post_route_code = '''
@app.route('/api/evaluation-history', methods=['POST'])
def post_evaluation_history():
    """保存评估历史记录（兼容前端重复保存调用）"""
    try:
        logger.info("前端尝试保存评估历史记录")
        
        data = request.get_json()
        
        # 检查是否已经存在相同的记录（避免重复）
        if data.get('user_input') and data.get('model_answer'):
            from models.classification import EvaluationHistory
            from datetime import datetime, timedelta
            
            # 查找最近2分钟内的相同记录
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            existing = EvaluationHistory.query.filter(
                EvaluationHistory.user_input == data['user_input'],
                EvaluationHistory.model_answer == data['model_answer'],
                EvaluationHistory.created_at >= two_minutes_ago
            ).first()
            
            if existing:
                logger.info(f"发现重复记录，返回现有记录ID: {existing.id}")
                return jsonify({
                    'success': True,
                    'message': '记录已存在，返回现有记录',
                    'history_id': existing.id,
                    'data': existing.to_dict()
                })
        
        # 调用服务保存记录
        result = evaluation_history_service.save_evaluation_result(data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"保存评估历史失败: {str(e)}")
        return jsonify({'error': f'保存评估历史失败: {str(e)}'}), 500
'''
        
        # 找到合适的插入位置（在GET路由后面）
        pattern = r'(@app\.route\(\'/api/evaluation-history\', methods=\[\'GET\'\]\)[^@]*?return jsonify\(\{\'error\':[^}]*\}\), 500)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            # 在GET路由后插入POST路由
            insert_pos = match.end()
            new_content = content[:insert_pos] + post_route_code + content[insert_pos:]
            
            # 备份原文件
            backup_path = 'app.py.backup_405fix'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"📁 已备份原文件到: {backup_path}")
            
            # 写入新内容
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 已添加POST路由到app.py")
            print("🔄 请重启Flask应用以生效")
            return True
        else:
            print("❌ 找不到GET路由的插入位置")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def verify_fix():
    """验证修复是否成功"""
    print("\n🔍 验证修复结果...")
    
    try:
        app_py_path = 'app.py'
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否包含POST路由
        if "post_evaluation_history" in content and "methods=['POST']" in content:
            print("✅ POST路由添加成功")
            
            # 统计evaluation-history相关路由
            lines = content.split('\n')
            routes_count = 0
            for line in lines:
                if "'/api/evaluation-history'" in line and "@app.route" in line:
                    routes_count += 1
                    print(f"  📍 找到路由: {line.strip()}")
            
            print(f"✅ 总共找到 {routes_count} 个evaluation-history路由")
            return True
        else:
            print("❌ POST路由添加失败")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🚨 POST /api/evaluation-history 405错误快速修复工具")
    print("=" * 50)
    
    success = fix_post_route()
    
    if success:
        verify_fix()
        print("\n" + "=" * 50)
        print("🎉 修复完成！")
        print("\n📋 接下来的步骤：")
        print("1. 重启Flask应用：python app.py")
        print("2. 测试评估功能，确认不再有405错误")
        print("3. 检查浏览器控制台，确认POST请求成功")
        print("4. 测试人工评估功能")
    else:
        print("\n" + "=" * 50)
        print("❌ 修复失败，请手动添加路由或联系技术支持")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 