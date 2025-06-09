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


class ClassificationResult(db.Model):
    """分类结果数据模型"""
    __tablename__ = 'classification_results'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_input = db.Column(db.Text, nullable=False, comment='用户输入')
    level1 = db.Column(db.String(100), nullable=False, comment='一级分类')
    level2 = db.Column(db.String(100), nullable=False, comment='二级分类') 
    level3 = db.Column(db.String(100), nullable=False, comment='三级分类')
    level1_definition = db.Column(db.Text, comment='一级分类定义')
    level2_definition = db.Column(db.Text, comment='二级分类定义')
    level3_definition = db.Column(db.Text, comment='三级分类定义')
    confidence = db.Column(db.Float, default=0.0, comment='置信度')
    reasoning = db.Column(db.Text, comment='分类理由')
    classification_time_seconds = db.Column(db.Float, default=0.0, comment='分类耗时(秒)')
    model_used = db.Column(db.String(100), comment='使用的模型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_input': self.user_input,
            'level1': self.level1,
            'level2': self.level2,
            'level3': self.level3,
            'level1_definition': self.level1_definition,
            'level2_definition': self.level2_definition,
            'level3_definition': self.level3_definition,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'classification_time_seconds': self.classification_time_seconds,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ClassificationHistory(db.Model):
    """分类历史数据模型"""
    __tablename__ = 'classification_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_input = db.Column(db.Text, nullable=False, comment='用户输入')
    classification_result = db.Column(db.Text, comment='分类结果(JSON格式)')
    confidence = db.Column(db.Float, default=0.0, comment='置信度')
    classification_time = db.Column(db.Float, comment='分类耗时(秒)')
    model_used = db.Column(db.String(100), comment='使用的模型')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    
    def to_dict(self):
        """转换为字典格式"""
        classification_data = {}
        if self.classification_result:
            try:
                classification_data = json.loads(self.classification_result)
            except (json.JSONDecodeError, TypeError):
                classification_data = {}
        
        return {
            'id': self.id,
            'user_input': self.user_input,
            'classification_result': classification_data,
            'confidence': self.confidence,
            'classification_time': self.classification_time,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ClassificationHistory {self.id}: {self.user_input[:50]}...>'


class EvaluationStandard(db.Model):
    """评估标准数据模型"""
    __tablename__ = 'evaluation_standards'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    level2_category = db.Column(db.String(100), nullable=False, comment='二级分类名称')
    dimension = db.Column(db.String(100), nullable=False, comment='评估维度')
    reference_standard = db.Column(db.Text, nullable=False, comment='参考标准')
    scoring_principle = db.Column(db.Text, nullable=False, comment='打分原则')
    max_score = db.Column(db.Integer, default=5, comment='最高分数')
    weight = db.Column(db.Float, default=1.0, comment='权重')
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
            'weight': self.weight,
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
            weight=data.get('weight', 1.0),
            is_default=data.get('is_default', False)
        )
    
    def __repr__(self):
        return f'<EvaluationStandard {self.level2_category}-{self.dimension}>'


class EvaluationHistory(db.Model):
    """评估历史数据模型"""
    __tablename__ = 'evaluation_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_input = db.Column(db.Text, nullable=False, comment='用户问题')
    model_answer = db.Column(db.Text, nullable=False, comment='模型回答')
    reference_answer = db.Column(db.Text, comment='参考答案')
    question_time = db.Column(db.DateTime, comment='问题提出时间')
    evaluation_criteria = db.Column(db.Text, comment='评估标准')
    total_score = db.Column(db.Float, nullable=False, comment='总分')
    dimensions_json = db.Column(db.Text, comment='各维度分数(JSON格式)')
    reasoning = db.Column(db.Text, comment='评分理由')
    classification_level1 = db.Column(db.String(100), comment='一级分类')
    classification_level2 = db.Column(db.String(100), comment='二级分类')
    classification_level3 = db.Column(db.String(100), comment='三级分类')
    evaluation_time_seconds = db.Column(db.Float, comment='评估耗时(秒)')
    model_used = db.Column(db.String(100), comment='使用的模型')
    raw_response = db.Column(db.Text, comment='原始LLM响应')
    uploaded_images_json = db.Column(db.Text, comment='上传的图片信息(JSON格式)')
    
    # 人工评估相关字段
    human_total_score = db.Column(db.Float, comment='人工修改后的总分')
    human_dimensions_json = db.Column(db.Text, comment='人工修改后的各维度分数(JSON格式)')
    human_reasoning = db.Column(db.Text, comment='人工评估意见')
    human_evaluation_by = db.Column(db.String(100), comment='人工评估者')
    human_evaluation_time = db.Column(db.DateTime, comment='人工评估时间')
    is_human_modified = db.Column(db.Boolean, default=False, comment='是否经过人工修改')
    
    # Badcase相关字段
    is_badcase = db.Column(db.Boolean, default=False, comment='是否为badcase')
    ai_is_badcase = db.Column(db.Boolean, default=False, comment='AI判断是否为badcase')
    human_is_badcase = db.Column(db.Boolean, default=False, comment='人工判断是否为badcase')
    badcase_reason = db.Column(db.Text, comment='badcase原因说明')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def to_dict(self):
        """转换为字典格式"""
        dimensions = {}
        if self.dimensions_json:
            try:
                dimensions = json.loads(self.dimensions_json)
            except (json.JSONDecodeError, TypeError):
                dimensions = {}
        
        human_dimensions = {}
        if self.human_dimensions_json:
            try:
                human_dimensions = json.loads(self.human_dimensions_json)
            except (json.JSONDecodeError, TypeError):
                human_dimensions = {}
        
        uploaded_images = []
        if self.uploaded_images_json:
            try:
                uploaded_images = json.loads(self.uploaded_images_json)
            except (json.JSONDecodeError, TypeError):
                uploaded_images = []
        
        # 安全地处理日期字段
        def safe_datetime_format(dt_field):
            if dt_field is None:
                return None
            try:
                if hasattr(dt_field, 'isoformat'):
                    return dt_field.isoformat()
                elif isinstance(dt_field, (int, float)):
                    # 如果是数字，尝试转换为datetime再格式化
                    from datetime import datetime
                    return datetime.fromtimestamp(dt_field).isoformat()
                elif isinstance(dt_field, str):
                    # 如果已经是字符串，直接返回
                    return dt_field
                else:
                    return str(dt_field)
            except (ValueError, OSError, TypeError):
                return str(dt_field) if dt_field is not None else None
        
        return {
            'id': self.id,
            'user_input': self.user_input,
            'model_answer': self.model_answer,
            'reference_answer': self.reference_answer,
            'question_time': safe_datetime_format(self.question_time),
            'evaluation_criteria': self.evaluation_criteria,
            'total_score': self.total_score,
            'dimensions': dimensions,
            'reasoning': self.reasoning,
            'classification_level1': self.classification_level1,
            'classification_level2': self.classification_level2,
            'classification_level3': self.classification_level3,
            'evaluation_time_seconds': self.evaluation_time_seconds,
            'model_used': self.model_used,
            'raw_response': self.raw_response,
            'uploaded_images': uploaded_images,
            
            # 人工评估字段
            'human_total_score': self.human_total_score,
            'human_dimensions': human_dimensions,
            'human_reasoning': self.human_reasoning,
            'human_evaluation_by': self.human_evaluation_by,
            'human_evaluation_time': safe_datetime_format(self.human_evaluation_time),
            'is_human_modified': self.is_human_modified,
            
            # Badcase字段
            'is_badcase': self.is_badcase,
            'ai_is_badcase': self.ai_is_badcase,
            'human_is_badcase': self.human_is_badcase,
            'badcase_reason': self.badcase_reason,
            
            'created_at': safe_datetime_format(self.created_at),
            'updated_at': safe_datetime_format(self.updated_at)
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        # 处理dimensions数据
        dimensions_json = None
        if 'dimensions' in data and data['dimensions']:
            dimensions_json = json.dumps(data['dimensions'], ensure_ascii=False)
        
        # 处理human_dimensions数据
        human_dimensions_json = None
        if 'human_dimensions' in data and data['human_dimensions']:
            human_dimensions_json = json.dumps(data['human_dimensions'], ensure_ascii=False)
        
        # 处理uploaded_images数据
        uploaded_images_json = None
        if 'uploaded_images' in data and data['uploaded_images']:
            uploaded_images_json = json.dumps(data['uploaded_images'], ensure_ascii=False)
        
        # 处理question_time
        question_time = None
        if 'question_time' in data and data['question_time']:
            if isinstance(data['question_time'], str):
                # 验证不是JSON字符串
                if not data['question_time'].strip().startswith('{'):
                    try:
                        question_time = datetime.fromisoformat(data['question_time'].replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            question_time = datetime.strptime(data['question_time'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            question_time = None
            elif isinstance(data['question_time'], datetime):
                question_time = data['question_time']
        
        # 处理human_evaluation_time
        human_evaluation_time = None
        if 'human_evaluation_time' in data and data['human_evaluation_time']:
            if isinstance(data['human_evaluation_time'], str):
                # 验证不是JSON字符串
                if not data['human_evaluation_time'].strip().startswith('{'):
                    try:
                        human_evaluation_time = datetime.fromisoformat(data['human_evaluation_time'].replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            human_evaluation_time = datetime.strptime(data['human_evaluation_time'], '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            human_evaluation_time = None
            elif isinstance(data['human_evaluation_time'], datetime):
                human_evaluation_time = data['human_evaluation_time']
        
        return cls(
            user_input=data.get('user_input'),
            model_answer=data.get('model_answer'),
            reference_answer=data.get('reference_answer'),
            question_time=question_time,
            evaluation_criteria=data.get('evaluation_criteria'),
            total_score=data.get('total_score', 0.0),
            dimensions_json=dimensions_json,
            reasoning=data.get('reasoning'),
            classification_level1=data.get('classification_level1'),
            classification_level2=data.get('classification_level2'),
            classification_level3=data.get('classification_level3'),
            evaluation_time_seconds=data.get('evaluation_time_seconds'),
            model_used=data.get('model_used'),
            raw_response=data.get('raw_response'),
            uploaded_images_json=uploaded_images_json,
            
            # 人工评估字段
            human_total_score=data.get('human_total_score'),
            human_dimensions_json=human_dimensions_json,
            human_reasoning=data.get('human_reasoning'),
            human_evaluation_by=data.get('human_evaluation_by'),
            human_evaluation_time=human_evaluation_time,
            is_human_modified=data.get('is_human_modified', False),
            
            # Badcase字段
            is_badcase=data.get('is_badcase', False),
            ai_is_badcase=data.get('ai_is_badcase', False),
            human_is_badcase=data.get('human_is_badcase', False),
            badcase_reason=data.get('badcase_reason', '')
        )
    
    def __repr__(self):
        return f'<EvaluationHistory {self.id}: {self.total_score}/10>' 