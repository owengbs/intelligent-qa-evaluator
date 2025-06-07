#!/usr/bin/env python3
"""
评估维度管理服务
"""

import json
from models.classification import db
from models.evaluation_dimension import EvaluationDimension, CategoryDimensionMapping


class EvaluationDimensionService:
    """评估维度管理服务"""
    
    @staticmethod
    def get_all_dimensions(layer=None, category=None, is_active=None):
        """获取所有评估维度"""
        query = EvaluationDimension.query
        
        if layer:
            query = query.filter(EvaluationDimension.layer == layer)
        if category:
            query = query.filter(EvaluationDimension.category == category)
        if is_active is not None:
            query = query.filter(EvaluationDimension.is_active == is_active)
        
        dimensions = query.order_by(EvaluationDimension.sort_order.asc(), EvaluationDimension.id.asc()).all()
        return [dimension.to_dict() for dimension in dimensions]
    
    @staticmethod
    def get_dimension_by_id(dimension_id):
        """根据ID获取评估维度"""
        dimension = EvaluationDimension.query.get(dimension_id)
        return dimension.to_dict() if dimension else None
    
    @staticmethod
    def create_dimension(data):
        """创建新的评估维度"""
        try:
            dimension = EvaluationDimension.from_dict(data)
            db.session.add(dimension)
            db.session.commit()
            return dimension.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_dimension(dimension_id, data):
        """更新评估维度"""
        try:
            dimension = EvaluationDimension.query.get(dimension_id)
            if not dimension:
                return None
            
            # 更新字段
            dimension.name = data.get('name', dimension.name)
            dimension.layer = data.get('layer', dimension.layer)
            dimension.definition = data.get('definition', dimension.definition)
            dimension.examples = data.get('examples', dimension.examples)
            dimension.category = data.get('category', dimension.category)
            dimension.sort_order = data.get('sort_order', dimension.sort_order)
            dimension.is_active = data.get('is_active', dimension.is_active)
            
            # 更新测评标准
            if 'evaluation_criteria' in data:
                evaluation_criteria_json = json.dumps(data['evaluation_criteria'], ensure_ascii=False)
                dimension.evaluation_criteria_json = evaluation_criteria_json
            
            db.session.commit()
            return dimension.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def delete_dimension(dimension_id):
        """删除评估维度"""
        try:
            dimension = EvaluationDimension.query.get(dimension_id)
            if not dimension:
                return False
            
            # 删除关联的分类映射
            CategoryDimensionMapping.query.filter_by(dimension_id=dimension_id).delete()
            
            # 删除维度
            db.session.delete(dimension)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_dimensions_by_layer():
        """按层次分组获取维度"""
        dimensions = EvaluationDimension.query.filter_by(is_active=True).order_by(
            EvaluationDimension.sort_order.asc(), 
            EvaluationDimension.id.asc()
        ).all()
        
        grouped = {}
        for dimension in dimensions:
            layer = dimension.layer
            if layer not in grouped:
                grouped[layer] = []
            grouped[layer].append(dimension.to_dict())
        
        return grouped


class CategoryDimensionService:
    """分类与维度关联管理服务"""
    
    @staticmethod
    def get_category_dimensions(level2_category):
        """获取某个分类关联的所有维度"""
        mappings = CategoryDimensionMapping.query.filter_by(
            level2_category=level2_category
        ).all()
        
        return [mapping.to_dict() for mapping in mappings]
    
    @staticmethod
    def set_category_dimensions(level2_category, dimension_ids):
        """设置某个分类关联的维度"""
        try:
            # 删除原有关联
            CategoryDimensionMapping.query.filter_by(level2_category=level2_category).delete()
            
            # 添加新关联
            for dimension_id in dimension_ids:
                mapping = CategoryDimensionMapping(
                    level2_category=level2_category,
                    dimension_id=dimension_id
                )
                db.session.add(mapping)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def add_category_dimension(level2_category, dimension_id, weight=1.0):
        """为某个分类添加维度"""
        try:
            # 检查是否已存在
            existing = CategoryDimensionMapping.query.filter_by(
                level2_category=level2_category,
                dimension_id=dimension_id
            ).first()
            
            if existing:
                return existing.to_dict()
            
            mapping = CategoryDimensionMapping(
                level2_category=level2_category,
                dimension_id=dimension_id,
                weight=weight
            )
            db.session.add(mapping)
            db.session.commit()
            return mapping.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def remove_category_dimension(level2_category, dimension_id):
        """移除某个分类的维度关联"""
        try:
            mapping = CategoryDimensionMapping.query.filter_by(
                level2_category=level2_category,
                dimension_id=dimension_id
            ).first()
            
            if mapping:
                db.session.delete(mapping)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_all_category_mappings():
        """获取所有分类与维度的关联关系"""
        mappings = CategoryDimensionMapping.query.all()
        
        # 按分类分组
        grouped = {}
        for mapping in mappings:
            category = mapping.level2_category
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(mapping.to_dict())
        
        return grouped 