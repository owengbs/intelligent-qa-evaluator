#!/usr/bin/env python3
"""
评估维度数据模型
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from models.classification import db

class EvaluationDimension(db.Model):
    """评估维度数据模型"""
    __tablename__ = 'evaluation_dimensions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='维度名称')
    layer = db.Column(db.String(50), nullable=False, comment='层次(第一层/第二层/第三层/其他服务场景)')
    definition = db.Column(db.Text, comment='维度定义')
    
    # 测评标准JSON格式存储: [{"level": "强", "score": 2, "description": "..."}, ...]
    evaluation_criteria_json = db.Column(db.Text, comment='测评标准(JSON格式)')
    
    examples = db.Column(db.Text, comment='示例说明')
    category = db.Column(db.String(100), comment='所属类别(金融场景/其他服务场景)')
    
    # 排序和状态
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        evaluation_criteria = []
        if self.evaluation_criteria_json:
            try:
                evaluation_criteria = json.loads(self.evaluation_criteria_json)
            except (json.JSONDecodeError, TypeError):
                evaluation_criteria = []
        
        return {
            'id': self.id,
            'name': self.name,
            'layer': self.layer,
            'definition': self.definition,
            'evaluation_criteria': evaluation_criteria,
            'examples': self.examples,
            'category': self.category,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        # 处理evaluation_criteria数据
        evaluation_criteria_json = None
        if 'evaluation_criteria' in data and data['evaluation_criteria']:
            evaluation_criteria_json = json.dumps(data['evaluation_criteria'], ensure_ascii=False)
        
        return cls(
            name=data.get('name'),
            layer=data.get('layer'),
            definition=data.get('definition'),
            evaluation_criteria_json=evaluation_criteria_json,
            examples=data.get('examples'),
            category=data.get('category'),
            sort_order=data.get('sort_order', 0),
            is_active=data.get('is_active', True)
        )
    
    def __repr__(self):
        return f'<EvaluationDimension {self.name} ({self.layer})>'


class CategoryDimensionMapping(db.Model):
    """分类与维度关联映射表"""
    __tablename__ = 'category_dimension_mappings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level2_category = db.Column(db.String(100), nullable=False, comment='二级分类名称')
    dimension_id = db.Column(db.Integer, db.ForeignKey('evaluation_dimensions.id'), nullable=False, comment='维度ID')
    
    # 该维度在此分类下的权重或重要性
    weight = db.Column(db.Float, default=1.0, comment='权重')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    # 建立关系
    dimension = db.relationship('EvaluationDimension', backref='category_mappings')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'level2_category': self.level2_category,
            'dimension_id': self.dimension_id,
            'dimension': self.dimension.to_dict() if self.dimension else None,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            level2_category=data.get('level2_category'),
            dimension_id=data.get('dimension_id'),
            weight=data.get('weight', 1.0)
        )
    
    def __repr__(self):
        return f'<CategoryDimensionMapping {self.level2_category} -> {self.dimension_id}>' 