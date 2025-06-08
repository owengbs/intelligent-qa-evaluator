#!/usr/bin/env python3
"""
数据库操作工具
"""

import sqlite3
import json
from datetime import datetime

class DatabaseOperations:
    """数据库操作类"""
    
    def __init__(self, db_path="/data/macxin/intelligent-qa-evaluator/backend/database/qa_evaluation.db"):
        self.db_path = db_path
    
    def save_category_standards(self, category, dimension_ids):
        """
        保存分类的标准配置
        
        Args:
            category (str): 二级分类名称
            dimension_ids (list): 选择的维度ID列表
        
        Returns:
            dict: 操作结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除该分类下的现有配置
            cursor.execute("DELETE FROM category_dimension_mappings WHERE level2_category = ?", (category,))
            
            # 添加新的配置
            for dimension_id in dimension_ids:
                cursor.execute("""
                    INSERT INTO category_dimension_mappings 
                    (level2_category, dimension_id, weight, created_at) 
                    VALUES (?, ?, 1.0, ?)
                """, (category, dimension_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'message': f'标准配置保存成功，共配置{len(dimension_ids)}个维度',
                'data': {
                    'category': category,
                    'dimension_count': len(dimension_ids)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'保存失败: {str(e)}'
            }
    
    def get_category_standards(self, category):
        """
        获取分类的标准配置
        
        Args:
            category (str): 二级分类名称
        
        Returns:
            dict: 查询结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取映射关系和维度信息
            cursor.execute("""
                SELECT m.id, m.level2_category, m.dimension_id, m.weight, m.created_at,
                       d.name, d.layer, d.definition, d.evaluation_criteria_json, 
                       d.examples, d.category, d.sort_order, d.is_active, 
                       d.created_at as dim_created_at, d.updated_at as dim_updated_at
                FROM category_dimension_mappings m
                LEFT JOIN evaluation_dimensions d ON m.dimension_id = d.id
                WHERE m.level2_category = ?
                ORDER BY d.sort_order, d.id
            """, (category,))
            
            rows = cursor.fetchall()
            conn.close()
            
            standards = []
            for row in rows:
                if row[5]:  # 如果维度存在
                    # 解析评测标准JSON
                    evaluation_criteria = []
                    if row[8]:  # evaluation_criteria_json
                        try:
                            evaluation_criteria = json.loads(row[8])
                        except (json.JSONDecodeError, TypeError):
                            evaluation_criteria = []
                    
                    standard_data = {
                        'id': row[2],  # dimension_id
                        'name': row[5],
                        'layer': row[6],
                        'definition': row[7],
                        'evaluation_criteria': evaluation_criteria,
                        'examples': row[9],
                        'category': row[10],
                        'sort_order': row[11],
                        'is_active': row[12],
                        'created_at': row[13],
                        'updated_at': row[14],
                        'weight': row[3]
                    }
                    standards.append(standard_data)
            
            return {
                'success': True,
                'data': standards,
                'total': len(standards)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'data': []
            }
    
    def get_all_category_standards(self):
        """
        获取所有分类的标准配置
        
        Returns:
            dict: 查询结果
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有映射关系和维度信息
            cursor.execute("""
                SELECT m.id, m.level2_category, m.dimension_id, m.weight, m.created_at,
                       d.name, d.layer, d.definition, d.evaluation_criteria_json, 
                       d.examples, d.category, d.sort_order, d.is_active, 
                       d.created_at as dim_created_at, d.updated_at as dim_updated_at
                FROM category_dimension_mappings m
                LEFT JOIN evaluation_dimensions d ON m.dimension_id = d.id
                ORDER BY m.level2_category, d.sort_order, d.id
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            # 按分类分组
            category_standards = {}
            for row in rows:
                if row[5]:  # 如果维度存在
                    category = row[1]  # level2_category
                    if category not in category_standards:
                        category_standards[category] = []
                    
                    # 解析评测标准JSON
                    evaluation_criteria = []
                    if row[8]:  # evaluation_criteria_json
                        try:
                            evaluation_criteria = json.loads(row[8])
                        except (json.JSONDecodeError, TypeError):
                            evaluation_criteria = []
                    
                    standard_data = {
                        'id': row[2],  # dimension_id
                        'name': row[5],
                        'layer': row[6],
                        'definition': row[7],
                        'evaluation_criteria': evaluation_criteria,
                        'examples': row[9],
                        'category': row[10],
                        'sort_order': row[11],
                        'is_active': row[12],
                        'created_at': row[13],
                        'updated_at': row[14],
                        'weight': row[3]
                    }
                    category_standards[category].append(standard_data)
            
            return {
                'success': True,
                'data': category_standards
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'获取失败: {str(e)}',
                'data': {}
            }

    def format_for_evaluation_template(self, category):
        """
        为评估模板格式化标准配置
        
        Args:
            category (str): 二级分类名称
        
        Returns:
            dict: 格式化后的评估模板
        """
        try:
            result = self.get_category_standards(category)
            if not result['success']:
                return result
            
            standards = result['data']
            if not standards:
                return {
                    'success': False,
                    'message': f'分类"{category}"未配置评估标准'
                }
            
            # 格式化为评估模板格式
            dimensions = []
            total_max_score = 0
            
            for standard in standards:
                # 计算该维度的最大分数
                max_score = 0
                if standard.get('evaluation_criteria'):
                    for criteria in standard['evaluation_criteria']:
                        score = criteria.get('score', 0)
                        if isinstance(score, (int, float)) and score > max_score:
                            max_score = score
                
                # 格式化为评估模板维度
                dimension = {
                    'name': standard['name'],
                    'reference_standard': standard['definition'] or '',
                    'scoring_principle': self._format_scoring_principle(
                        standard.get('evaluation_criteria', [])
                    ),
                    'max_score': max_score,
                    'layer': standard.get('layer', ''),
                    'examples': standard.get('examples', '')
                }
                
                dimensions.append(dimension)
                total_max_score += max_score
            
            template = {
                'category': category,
                'dimensions': dimensions,
                'total_max_score': total_max_score,
                'dimension_count': len(dimensions)
            }
            
            return {
                'success': True,
                'data': template
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'格式化失败: {str(e)}'
            }
    
    def _format_scoring_principle(self, evaluation_criteria):
        """
        格式化评测标准为打分原则
        
        Args:
            evaluation_criteria (list): 评测标准列表
        
        Returns:
            str: 格式化后的打分原则
        """
        if not evaluation_criteria:
            return '请根据具体情况进行评分'
        
        principles = []
        for criteria in evaluation_criteria:
            level = criteria.get('level', '')
            score = criteria.get('score', 0)
            description = criteria.get('description', '')
            
            if level and description:
                principles.append(f"{level}({score}分): {description}")
        
        return '; '.join(principles) if principles else '请根据具体情况进行评分'

# 创建全局实例
db_ops = DatabaseOperations() 