#!/usr/bin/env python3
"""
配置数据导出脚本 (全量)
导出分类标准和评估标准数据到JSON文件
用于团队协作和版本控制
"""

import json
import os
import sys
from datetime import datetime

def test_database_connection():
    """测试数据库连接"""
    try:
        from app import app, db
        from sqlalchemy import text
        
        with app.app_context():
            # 兼容SQLAlchemy 2.0+
            try:
                # 新版SQLAlchemy方式
                with db.engine.connect() as connection:
                    result = connection.execute(text('SELECT 1'))
                    result.fetchone()
            except AttributeError:
                # 旧版SQLAlchemy方式（备选）
                result = db.engine.execute('SELECT 1')
                result.fetchone()
            return True
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {str(e)}")
        return False

def export_config_data():
    """导出配置数据"""
    try:
        # 首先测试数据库连接
        if not test_database_connection():
            return False
        
        from app import app, db
        from models.classification import ClassificationStandard, EvaluationStandard
        
        print("🔄 开始导出配置数据...")
        
        with app.app_context():
            # 导出分类标准
            classification_standards = ClassificationStandard.query.all()
            classification_data = [item.to_dict() for item in classification_standards]
            
            # 导出评估标准
            evaluation_standards = EvaluationStandard.query.all()
            evaluation_data = [item.to_dict() for item in evaluation_standards]
            
            # 构建导出数据
            export_data = {
                'metadata': {
                    'export_time': datetime.now().isoformat(),
                    'version': '2.3.4',
                    'description': '智能Q&A评估系统配置数据（全量导出）'
                },
                'classification_standards': {
                    'count': len(classification_data),
                    'data': classification_data
                },
                'evaluation_standards': {
                    'count': len(evaluation_data),
                    'data': evaluation_data
                }
            }
            
            # 确保导出目录存在
            config_dir = 'config_data'
            os.makedirs(config_dir, exist_ok=True)
            
            # 生成文件名（带时间戳）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{config_dir}/config_export_{timestamp}.json'
            
            # 写入JSON文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            # 同时创建最新版本的文件（用于版本控制）
            latest_filename = f'{config_dir}/latest_config.json'
            with open(latest_filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 配置数据导出成功:")
            print(f"   📄 导出文件: {filename}")
            print(f"   📄 最新版本: {latest_filename}")
            print(f"   📊 分类标准: {len(classification_data)} 条")
            print(f"   📊 评估标准: {len(evaluation_data)} 条")
            
            return True
            
    except ImportError as e:
        print(f"❌ 导入失败: {str(e)}")
        print("💡 请确保在backend目录下运行，且已安装所有依赖")
        return False
    except Exception as e:
        print(f"❌ 导出失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("="*50)
    print("📤 配置数据导出工具")
    print("="*50)
    
    success = export_config_data()
    
    if success:
        print("\n🎉 导出完成!")
        print("💡 提示:")
        print("   1. 将config_data/目录提交到版本控制")
        print("   2. 团队成员可使用import_config_data.py导入")
        print("   3. 使用--full-replace参数进行全量替换")
    else:
        print("\n❌ 导出失败")
        
    print("\n" + "="*50) 