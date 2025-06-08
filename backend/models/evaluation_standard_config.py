from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class EvaluationStandardConfig(Base):
    """评估标准配置表"""
    __tablename__ = 'evaluation_standard_config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, comment='二级分类名称')
    dimension_id = Column(Integer, ForeignKey('evaluation_dimensions.id'), nullable=False, comment='维度ID')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 外键关系
    dimension = relationship("EvaluationDimension", back_populates="standard_configs")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'category': self.category,
            'dimension_id': self.dimension_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'dimension': self.dimension.to_dict() if self.dimension else None
        } 