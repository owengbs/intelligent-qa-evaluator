#!/usr/bin/env python3
"""
评估标准配置服务
"""

import json
from models.classification import db
from models.evaluation_dimension import EvaluationDimension, CategoryDimensionMapping
from datetime import datetime

class EvaluationStandardConfigService:
    """评估标准配置服务"""
    
    @staticmethod
    def save_category_standards(category, dimension_ids):
        """
        保存分类的标准配置
        
        Args:
            category (str): 二级分类名称
            dimension_ids (list): 选择的维度ID列表
        
        Returns:
            dict: 操作结果
        """
        try:
            # 删除该分类下的现有配置
            CategoryDimensionMapping.query.filter_by(level2_category=category).delete()
            
            # 添加新的配置
            for dimension_id in dimension_ids:
                # 验证维度是否存在
                dimension = EvaluationDimension.query.get(dimension_id)
                if not dimension:
                    continue
                    
                mapping = CategoryDimensionMapping(
                    level2_category=category,
                    dimension_id=dimension_id,
                    weight=1.0
                )
                db.session.add(mapping)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'标准配置保存成功，共配置{len(dimension_ids)}个维度',
                'data': {
                    'category': category,
                    'dimension_count': len(dimension_ids)
                }
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'保存失败: {str(e)}'
            }
    
    @staticmethod
    def get_category_standards(category):
        """
        获取分类的标准配置
        
        Args:
            category (str): 二级分类名称
        
        Returns:
            dict: 查询结果
        """
        try:
            mappings = CategoryDimensionMapping.query.filter_by(
                level2_category=category
            ).join(EvaluationDimension).all()
            
            standards = []
            for mapping in mappings:
                if mapping.dimension:
                    standard_data = mapping.dimension.to_dict()
                    standard_data['category'] = category  # 添加分类信息
                    standard_data['weight'] = mapping.weight
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
    
    @staticmethod
    def get_all_category_standards():
        """
        获取所有分类的标准配置
        
        Returns:
            dict: 查询结果
        """
        try:
            mappings = CategoryDimensionMapping.query.join(EvaluationDimension).all()
            
            # 按分类分组
            category_standards = {}
            for mapping in mappings:
                if mapping.dimension:
                    category = mapping.level2_category
                    if category not in category_standards:
                        category_standards[category] = []
                    
                    standard_data = mapping.dimension.to_dict()
                    standard_data['category'] = category
                    standard_data['weight'] = mapping.weight
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
    
    @staticmethod
    def format_for_evaluation_template(category):
        """
        为评估模板格式化标准配置
        
        Args:
            category (str): 二级分类名称
        
        Returns:
            dict: 格式化后的评估模板
        """
        try:
            result = EvaluationStandardConfigService.get_category_standards(category)
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
                    'scoring_principle': EvaluationStandardConfigService._format_scoring_principle(
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
    
    @staticmethod
    def _format_scoring_principle(evaluation_criteria):
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