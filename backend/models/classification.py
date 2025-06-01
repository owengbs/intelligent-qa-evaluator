"""
分类标准和评估标准数据模型
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ClassificationStandard(db.Model):
    """分类标准数据模型"""
    __tablename__ = 'classification_standards'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level1 = db.Column(db.String(100), nullable=False, comment='一级分类')
    level1_definition = db.Column(db.Text, comment='一级分类定义')
    level2 = db.Column(db.String(100), nullable=False, comment='二级分类')
    level3 = db.Column(db.String(100), nullable=False, comment='三级分类')
    level3_definition = db.Column(db.Text, comment='三级分类定义')
    examples = db.Column(db.Text, comment='问题示例')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认标准')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'level1': self.level1,
            'level1_definition': self.level1_definition,
            'level2': self.level2,
            'level3': self.level3,
            'level3_definition': self.level3_definition,
            'examples': self.examples,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            level1=data.get('level1'),
            level1_definition=data.get('level1_definition'),
            level2=data.get('level2'),
            level3=data.get('level3'),
            level3_definition=data.get('level3_definition'),
            examples=data.get('examples'),
            is_default=data.get('is_default', False)
        )
    
    def __repr__(self):
        return f'<ClassificationStandard {self.level1}->{self.level2}->{self.level3}>'


class EvaluationStandard(db.Model):
    """评估标准数据模型"""
    __tablename__ = 'evaluation_standards'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level2_category = db.Column(db.String(100), nullable=False, comment='二级分类名称')
    dimension = db.Column(db.String(100), nullable=False, comment='评估维度')
    reference_standard = db.Column(db.Text, nullable=False, comment='参考标准')
    scoring_principle = db.Column(db.Text, nullable=False, comment='打分原则')
    max_score = db.Column(db.Integer, default=5, comment='最高分数')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认标准')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'level2_category': self.level2_category,
            'dimension': self.dimension,
            'reference_standard': self.reference_standard,
            'scoring_principle': self.scoring_principle,
            'max_score': self.max_score,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            level2_category=data.get('level2_category'),
            dimension=data.get('dimension'),
            reference_standard=data.get('reference_standard'),
            scoring_principle=data.get('scoring_principle'),
            max_score=data.get('max_score', 5),
            is_default=data.get('is_default', False)
        )
    
    def __repr__(self):
        return f'<EvaluationStandard {self.level2_category}-{self.dimension}>'


class ClassificationHistory(db.Model):
    """分类历史记录"""
    __tablename__ = 'classification_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_input = db.Column(db.Text, nullable=False, comment='用户输入')
    classification_result = db.Column(db.Text, nullable=False, comment='分类结果JSON')
    confidence = db.Column(db.Float, comment='置信度')
    classification_time = db.Column(db.Float, comment='分类耗时(秒)')
    model_used = db.Column(db.String(100), comment='使用的模型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_input': self.user_input,
            'classification_result': json.loads(self.classification_result) if self.classification_result else {},
            'confidence': self.confidence,
            'classification_time': self.classification_time,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ClassificationHistory {self.id}>' 