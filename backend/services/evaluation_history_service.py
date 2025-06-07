"""
评估历史管理服务类
"""
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc
from models.classification import db, EvaluationHistory
from utils.logger import get_logger

class EvaluationHistoryService:
    """评估历史管理服务类"""
    
    def __init__(self, app=None):
        self.logger = get_logger(__name__)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化Flask应用"""
        self.app = app
    
    def save_evaluation_result(self, evaluation_data, classification_result=None):
        """
        保存评估结果到历史记录（带重复检测）
        
        Args:
            evaluation_data: 评估结果数据
            classification_result: 分类结果数据（可选）
            
        Returns:
            dict: 保存结果
        """
        try:
            # ====== 新增：重复记录检测 ======
            user_input = evaluation_data.get('user_input')
            model_answer = evaluation_data.get('model_answer')
            
            if user_input and model_answer:
                # 检查最近5分钟内是否有相同内容的记录
                five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
                existing_record = EvaluationHistory.query.filter(
                    EvaluationHistory.user_input == user_input,
                    EvaluationHistory.model_answer == model_answer,
                    EvaluationHistory.created_at >= five_minutes_ago
                ).first()
                
                if existing_record:
                    self.logger.warning(f"检测到重复记录，返回现有记录ID: {existing_record.id}")
                    return {
                        'success': True,
                        'message': '检测到重复记录，返回现有记录',
                        'history_id': existing_record.id,
                        'data': existing_record.to_dict(),
                        'is_duplicate': True
                    }
            # ====== 重复检测结束 ======
            
            # 创建评估历史记录
            history_data = {
                'user_input': evaluation_data.get('user_input'),
                'model_answer': evaluation_data.get('model_answer'),
                'reference_answer': evaluation_data.get('reference_answer'),
                'question_time': evaluation_data.get('question_time'),
                # 兼容前端发送的字段名
                'evaluation_criteria': evaluation_data.get('evaluation_criteria') or evaluation_data.get('evaluation_criteria_used'),
                # 兼容前端发送的字段名
                'total_score': evaluation_data.get('total_score') or evaluation_data.get('score', 0.0),
                'dimensions': evaluation_data.get('dimensions', {}),
                'reasoning': evaluation_data.get('reasoning'),
                'evaluation_time_seconds': evaluation_data.get('evaluation_time_seconds'),
                'model_used': evaluation_data.get('model_used'),
                'raw_response': evaluation_data.get('raw_response'),
                'uploaded_images': evaluation_data.get('uploaded_images', [])  # 添加图片信息
            }
            
            # 如果有分类结果，添加分类信息
            if classification_result:
                history_data.update({
                    'classification_level1': classification_result.get('level1'),
                    'classification_level2': classification_result.get('level2'),
                    'classification_level3': classification_result.get('level3')
                })
            
            # 创建数据库记录
            history_record = EvaluationHistory.from_dict(history_data)
            
            # 保存到数据库
            db.session.add(history_record)
            db.session.commit()
            
            self.logger.info(f"成功保存评估历史记录，ID: {history_record.id}")
            
            return {
                'success': True,
                'message': '评估历史保存成功',
                'history_id': history_record.id,
                'data': history_record.to_dict()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"保存评估历史失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'保存评估历史失败: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"保存评估历史时发生错误: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'保存评估历史时发生错误: {str(e)}'
            }
    
    def get_evaluation_history(self, page=1, per_page=20, classification_level2=None, 
                              start_date=None, end_date=None, sort_by='created_at', 
                              sort_order='desc'):
        """
        获取评估历史记录（分页）
        
        Args:
            page: 页码
            per_page: 每页数量
            classification_level2: 二级分类筛选
            start_date: 开始日期
            end_date: 结束日期
            sort_by: 排序字段
            sort_order: 排序方向 (asc/desc)
            
        Returns:
            dict: 分页的评估历史数据
        """
        try:
            # 构建查询
            query = EvaluationHistory.query
            
            # 添加筛选条件
            if classification_level2:
                query = query.filter(EvaluationHistory.classification_level2 == classification_level2)
            
            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(EvaluationHistory.created_at >= start_dt)
                except ValueError:
                    self.logger.warning(f"无效的开始日期格式: {start_date}")
            
            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(EvaluationHistory.created_at <= end_dt)
                except ValueError:
                    self.logger.warning(f"无效的结束日期格式: {end_date}")
            
            # 添加排序
            if hasattr(EvaluationHistory, sort_by):
                sort_column = getattr(EvaluationHistory, sort_by)
                if sort_order.lower() == 'desc':
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(EvaluationHistory.created_at))
            
            # 执行分页查询
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # 格式化结果
            items = [item.to_dict() for item in pagination.items]
            
            result = {
                'success': True,
                'data': {
                    'items': items,
                    'pagination': {
                        'page': pagination.page,
                        'per_page': pagination.per_page,
                        'total': pagination.total,
                        'pages': pagination.pages,
                        'has_prev': pagination.has_prev,
                        'has_next': pagination.has_next,
                        'prev_num': pagination.prev_num,
                        'next_num': pagination.next_num
                    }
                }
            }
            
            self.logger.info(f"成功获取评估历史，页码: {page}, 总数: {pagination.total}")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取评估历史失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取评估历史失败: {str(e)}'
            }
    
    def get_evaluation_by_id(self, history_id):
        """
        根据ID获取单个评估记录
        
        Args:
            history_id: 评估历史ID
            
        Returns:
            dict: 评估记录数据
        """
        try:
            history = EvaluationHistory.query.get(history_id)
            
            if not history:
                return {
                    'success': False,
                    'message': '评估记录不存在'
                }
            
            return {
                'success': True,
                'data': history.to_dict()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取评估记录失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取评估记录失败: {str(e)}'
            }
    
    def delete_evaluation(self, history_id):
        """
        删除评估记录
        
        Args:
            history_id: 评估历史ID
            
        Returns:
            dict: 删除结果
        """
        try:
            history = EvaluationHistory.query.get(history_id)
            
            if not history:
                return {
                    'success': False,
                    'message': '评估记录不存在'
                }
            
            db.session.delete(history)
            db.session.commit()
            
            self.logger.info(f"成功删除评估历史记录，ID: {history_id}")
            
            return {
                'success': True,
                'message': '评估记录删除成功'
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"删除评估记录失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'删除评估记录失败: {str(e)}'
            }
    
    def update_human_evaluation(self, history_id, human_data, evaluator_name='匿名用户'):
        """
        更新人工评估结果
        
        Args:
            history_id: 评估历史ID
            human_data: 人工评估数据
            evaluator_name: 评估者姓名
            
        Returns:
            dict: 更新结果
        """
        try:
            history = EvaluationHistory.query.get(history_id)
            
            if not history:
                return {
                    'success': False,
                    'message': '评估记录不存在'
                }
            
            # 更新人工评估字段
            if 'human_total_score' in human_data:
                history.human_total_score = human_data['human_total_score']
            
            if 'human_dimensions' in human_data and human_data['human_dimensions']:
                history.human_dimensions_json = json.dumps(human_data['human_dimensions'], ensure_ascii=False)
            
            if 'human_reasoning' in human_data:
                history.human_reasoning = human_data['human_reasoning']
            
            # 设置评估者和时间
            history.human_evaluation_by = evaluator_name
            history.human_evaluation_time = datetime.utcnow()
            history.is_human_modified = True
            
            # 更新updated_at字段
            history.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"成功更新人工评估，记录ID: {history_id}, 评估者: {evaluator_name}")
            
            return {
                'success': True,
                'message': '人工评估更新成功',
                'data': history.to_dict()
            }
            
        except SQLAlchemyError as e:
            self.logger.error(f"更新人工评估失败: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'更新人工评估失败: {str(e)}'
            }
        except Exception as e:
            self.logger.error(f"更新人工评估时发生错误: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'message': f'更新人工评估时发生错误: {str(e)}'
            }
    
    def get_evaluation_statistics(self):
        """
        获取评估统计信息
        
        Returns:
            dict: 统计信息
        """
        try:
            # 基础统计
            total_evaluations = EvaluationHistory.query.count()
            
            # 分类统计
            classification_stats = db.session.query(
                EvaluationHistory.classification_level2,
                func.count(EvaluationHistory.id).label('count'),
                func.avg(EvaluationHistory.total_score).label('avg_score'),
                func.min(EvaluationHistory.total_score).label('min_score'),
                func.max(EvaluationHistory.total_score).label('max_score')
            ).filter(
                EvaluationHistory.classification_level2.isnot(None)
            ).group_by(
                EvaluationHistory.classification_level2
            ).all()
            
            # 最近7天的评估趋势
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_trend = db.session.query(
                func.date(EvaluationHistory.created_at).label('date'),
                func.count(EvaluationHistory.id).label('count'),
                func.avg(EvaluationHistory.total_score).label('avg_score')
            ).filter(
                EvaluationHistory.created_at >= seven_days_ago
            ).group_by(
                func.date(EvaluationHistory.created_at)
            ).order_by(
                func.date(EvaluationHistory.created_at)
            ).all()
            
            # 格式化分类统计
            classification_data = []
            for stat in classification_stats:
                classification_data.append({
                    'category': stat.classification_level2,
                    'count': stat.count,
                    'avg_score': round(stat.avg_score, 2) if stat.avg_score else 0,
                    'min_score': stat.min_score if stat.min_score else 0,
                    'max_score': stat.max_score if stat.max_score else 0
                })
            
            # 格式化趋势数据
            trend_data = []
            for trend in recent_trend:
                # SQLite的func.date()返回字符串，直接使用
                date_str = trend.date if isinstance(trend.date, str) else trend.date.isoformat()
                trend_data.append({
                    'date': date_str,
                    'count': trend.count,
                    'avg_score': round(trend.avg_score, 2) if trend.avg_score else 0
                })
            
            result = {
                'success': True,
                'data': {
                    'total_evaluations': total_evaluations,
                    'classification_stats': classification_data,
                    'recent_trend': trend_data
                }
            }
            
            self.logger.info("成功获取评估统计信息")
            return result
            
        except SQLAlchemyError as e:
            self.logger.error(f"获取评估统计失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取评估统计失败: {str(e)}'
            }
    
    def get_dimension_statistics(self):
        """
        获取维度统计信息 - 各个二级分类下各维度的评分百分比
        
        Returns:
            dict: 维度统计信息
        """
        try:
            # 获取所有有维度数据的评估记录
            evaluations = EvaluationHistory.query.filter(
                EvaluationHistory.dimensions_json.isnot(None),
                EvaluationHistory.classification_level2.isnot(None)
            ).all()
            
            # 按分类组织数据
            category_stats = {}
            
            for evaluation in evaluations:
                category = evaluation.classification_level2
                
                if category not in category_stats:
                    category_stats[category] = {
                        'total_evaluations': 0,
                        'dimensions': {}
                    }
                
                category_stats[category]['total_evaluations'] += 1
                
                # 解析维度数据
                try:
                    dimensions = json.loads(evaluation.dimensions_json)
                    
                    for dimension_key, score in dimensions.items():
                        if dimension_key not in category_stats[category]['dimensions']:
                            category_stats[category]['dimensions'][dimension_key] = {
                                'scores': [],
                                'max_possible_score': self._get_dimension_max_score(
                                    dimension_key, evaluation.evaluation_criteria
                                )
                            }
                        
                        category_stats[category]['dimensions'][dimension_key]['scores'].append(score)
                        
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.warning(f"解析维度数据失败: {str(e)}")
                    continue
            
            # 计算统计数据
            result_stats = {}
            
            for category, data in category_stats.items():
                result_stats[category] = {
                    'total_evaluations': data['total_evaluations'],
                    'dimensions': {}
                }
                
                for dimension_key, dimension_data in data['dimensions'].items():
                    scores = dimension_data['scores']
                    max_score = dimension_data['max_possible_score']
                    
                    if scores and max_score > 0:
                        # 计算百分比分数
                        percentages = [(score / max_score) * 100 for score in scores]
                        
                        result_stats[category]['dimensions'][dimension_key] = {
                            'dimension_name': self._get_dimension_display_name(dimension_key),
                            'total_evaluations': len(scores),
                            'avg_score': round(sum(scores) / len(scores), 2),
                            'max_possible_score': max_score,
                            'avg_percentage': round(sum(percentages) / len(percentages), 2),
                            'min_percentage': round(min(percentages), 2),
                            'max_percentage': round(max(percentages), 2),
                            'score_distribution': self._calculate_score_distribution(percentages)
                        }
            
            result = {
                'success': True,
                'data': result_stats
            }
            
            self.logger.info("成功获取维度统计信息")
            return result
            
        except Exception as e:
            self.logger.error(f"获取维度统计失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取维度统计失败: {str(e)}'
            }
    
    def _get_dimension_max_score(self, dimension_key, evaluation_criteria):
        """从评估标准中解析维度最大分数"""
        if not evaluation_criteria:
            # 默认分数映射
            default_scores = {
                'accuracy': 4, 'completeness': 3, 'fluency': 2, 'safety': 1,
                'relevance': 3, 'clarity': 2, 'timeliness': 3, 
                'usability': 3, 'compliance': 2
            }
            return default_scores.get(dimension_key, 5)
        
        # 解析评估标准文本
        lines = evaluation_criteria.split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 3:
                dimension_name = parts[0].strip()
                scoring_rule = parts[2].strip()
                
                # 检查是否匹配当前维度
                if (dimension_name.lower() == dimension_key.lower() or 
                    self._normalize_dimension_key(dimension_name) == dimension_key):
                    
                    # 提取最大分数
                    import re
                    score_match = re.search(r'(\d+)-(\d+)分|(\d+)分', scoring_rule)
                    if score_match:
                        return int(score_match.group(2) or score_match.group(3) or score_match.group(1))
        
        return 5  # 默认值
    
    def _get_dimension_display_name(self, dimension_key):
        """获取维度显示名称"""
        display_names = {
            'accuracy': '准确性',
            'completeness': '完整性',
            'fluency': '流畅性',
            'safety': '安全性',
            'relevance': '相关性',
            'clarity': '清晰度',
            'timeliness': '时效性',
            'usability': '可用性',
            'compliance': '合规性'
        }
        return display_names.get(dimension_key, dimension_key.capitalize())
    
    def _normalize_dimension_key(self, dimension_name):
        """标准化维度名称为key"""
        name_mapping = {
            '准确性': 'accuracy', '完整性': 'completeness', '流畅性': 'fluency',
            '安全性': 'safety', '相关性': 'relevance', '清晰度': 'clarity',
            '时效性': 'timeliness', '可用性': 'usability', '合规性': 'compliance'
        }
        return name_mapping.get(dimension_name.strip(), dimension_name.lower())
    
    def _calculate_score_distribution(self, percentages):
        """计算分数分布"""
        distribution = {
            'excellent': 0,  # 80-100%
            'good': 0,       # 60-79%
            'fair': 0,       # 40-59%
            'poor': 0        # 0-39%
        }
        
        for percentage in percentages:
            if percentage >= 80:
                distribution['excellent'] += 1
            elif percentage >= 60:
                distribution['good'] += 1
            elif percentage >= 40:
                distribution['fair'] += 1
            else:
                distribution['poor'] += 1
        
        total = len(percentages)
        if total > 0:
            for key in distribution:
                distribution[key] = round((distribution[key] / total) * 100, 1)
        
        return distribution 