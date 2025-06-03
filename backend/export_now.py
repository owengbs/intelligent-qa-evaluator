import sqlite3
import json
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('data/qa_evaluator.db')
conn.row_factory = sqlite3.Row

# 导出分类标准
cursor = conn.cursor()
cursor.execute("""
    SELECT level1, level1_definition, level2, level3, 
           level3_definition, examples, is_default
    FROM classification_standards
    ORDER BY level1, level2, level3
""")

classification_data = []
for row in cursor.fetchall():
    classification_data.append({
        'level1': row['level1'],
        'level1_definition': row['level1_definition'],
        'level2': row['level2'], 
        'level3': row['level3'],
        'level3_definition': row['level3_definition'],
        'examples': row['examples'],
        'is_default': bool(row['is_default'])
    })

# 导出评估标准
cursor.execute("""
    SELECT level2_category, dimension, reference_standard,
           scoring_principle, max_score, is_default
    FROM evaluation_standards
    ORDER BY level2_category, dimension
""")

evaluation_data = []
for row in cursor.fetchall():
    evaluation_data.append({
        'level2_category': row['level2_category'],
        'dimension': row['dimension'],
        'reference_standard': row['reference_standard'],
        'scoring_principle': row['scoring_principle'],
        'max_score': row['max_score'],
        'is_default': bool(row['is_default'])
    })

# 保存分类标准
with open('config_data/classification_standards.json', 'w', encoding='utf-8') as f:
    json.dump({
        'export_time': datetime.now().isoformat(),
        'description': '分类标准配置数据 - 用于团队同步',
        'count': len(classification_data),
        'data': classification_data
    }, f, ensure_ascii=False, indent=2)

# 保存评估标准
with open('config_data/evaluation_standards.json', 'w', encoding='utf-8') as f:
    json.dump({
        'export_time': datetime.now().isoformat(),
        'description': '评估标准配置数据 - 用于团队同步',
        'count': len(evaluation_data),
        'data': evaluation_data
    }, f, ensure_ascii=False, indent=2)

# 保存摘要
with open('config_data/export_summary.json', 'w', encoding='utf-8') as f:
    json.dump({
        'export_time': datetime.now().isoformat(),
        'classification_standards_count': len(classification_data),
        'evaluation_standards_count': len(evaluation_data),
        'total_records': len(classification_data) + len(evaluation_data),
        'files': [
            'classification_standards.json',
            'evaluation_standards.json'
        ],
        'description': 'AI评估系统配置数据导出摘要'
    }, f, ensure_ascii=False, indent=2)

conn.close()
print(f"✅ 配置数据导出完成！")
print(f"📋 分类标准: {len(classification_data)} 条")
print(f"📊 评估标准: {len(evaluation_data)} 条")
print(f"📁 输出目录: config_data/") 