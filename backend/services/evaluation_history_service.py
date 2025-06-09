"""
评估历史管理服务类
"""
import json
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func, desc, asc, or_
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
                'uploaded_images': evaluation_data.get('uploaded_images', []),  # 添加图片信息
                # 添加badcase相关字段
                'is_badcase': evaluation_data.get('is_badcase', False),
                'ai_is_badcase': evaluation_data.get('ai_is_badcase', False),
                'human_is_badcase': evaluation_data.get('human_is_badcase', False),
                'badcase_reason': evaluation_data.get('badcase_reason', '')
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
                    # 验证start_date是字符串且不是JSON
                    if isinstance(start_date, str) and not start_date.strip().startswith('{'):
                        start_dt = datetime.fromisoformat(start_date)
                        query = query.filter(EvaluationHistory.created_at >= start_dt)
                    else:
                        self.logger.warning(f"无效的开始日期格式: {start_date}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"无效的开始日期格式: {start_date}, 错误: {e}")
            
            if end_date:
                try:
                    # 验证end_date是字符串且不是JSON
                    if isinstance(end_date, str) and not end_date.strip().startswith('{'):
                        end_dt = datetime.fromisoformat(end_date)
                        query = query.filter(EvaluationHistory.created_at <= end_dt)
                    else:
                        self.logger.warning(f"无效的结束日期格式: {end_date}")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"无效的结束日期格式: {end_date}, 错误: {e}")
            
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
            
            # 格式化结果 - 安全处理每个记录的转换
            items = []
            for item in pagination.items:
                try:
                    items.append(item.to_dict())
                except Exception as e:
                    self.logger.warning(f"转换记录到字典时出错 (ID: {getattr(item, 'id', 'unknown')}): {str(e)}")
                    # 跳过有问题的记录，继续处理其他记录
                    continue
            
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
            
            try:
                data = history.to_dict()
            except Exception as e:
                self.logger.warning(f"转换记录到字典时出错 (ID: {history.id}): {str(e)}")
                # 返回基本信息而不是完整的字典
                data = {
                    'id': history.id,
                    'user_input': getattr(history, 'user_input', ''),
                    'model_answer': getattr(history, 'model_answer', ''),
                    'total_score': getattr(history, 'total_score', 0),
                    'error': f'记录格式错误: {str(e)}'
                }
            
            return {
                'success': True,
                'data': data
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
            
            # 更新badcase相关字段
            if 'human_is_badcase' in human_data:
                history.human_is_badcase = human_data['human_is_badcase']
                # 更新总的badcase状态（AI或人工任一判断为badcase即为badcase）
                history.is_badcase = history.ai_is_badcase or history.human_is_badcase
            
            if 'badcase_reason' in human_data:
                history.badcase_reason = human_data['badcase_reason']
            
            # 设置评估者和时间
            history.human_evaluation_by = evaluator_name
            history.human_evaluation_time = datetime.utcnow()
            history.is_human_modified = True
            
            # 更新updated_at字段
            history.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            self.logger.info(f"成功更新人工评估，记录ID: {history_id}, 评估者: {evaluator_name}")
            
            try:
                data = history.to_dict()
            except Exception as e:
                self.logger.warning(f"转换更新后的记录到字典时出错 (ID: {history.id}): {str(e)}")
                data = {'id': history.id, 'error': f'记录格式错误: {str(e)}'}
            
            return {
                'success': True,
                'message': '人工评估更新成功',
                'data': data
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
        获取维度统计信息 - 分别统计AI评估和人工评估的结果
        
        Returns:
            dict: 维度统计信息，包含AI和人工评估的分离数据
        """
        try:
            # 获取所有有维度数据的评估记录（包括AI评估和人工评估）
            evaluations = EvaluationHistory.query.filter(
                or_(
                    EvaluationHistory.dimensions_json.isnot(None),
                    EvaluationHistory.human_dimensions_json.isnot(None)
                ),
                EvaluationHistory.classification_level2.isnot(None)
            ).all()
            
            # 获取标准配置
            try:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
                from database_operations import db_ops
                standards_result = db_ops.get_all_category_standards()
                standards_data = standards_result.get('data', {}) if standards_result.get('success') else {}
            except Exception as e:
                self.logger.warning(f"获取标准配置失败，使用旧逻辑: {str(e)}")
                standards_data = {}
            
            # 分别按分类组织AI和人工评估数据
            ai_category_stats = {}
            human_category_stats = {}
            
            for evaluation in evaluations:
                try:
                    category = evaluation.classification_level2
                    
                    # 处理AI评估数据
                    if evaluation.dimensions_json:
                        if category not in ai_category_stats:
                            ai_category_stats[category] = {
                                'total_evaluations': 0,
                                'dimensions': {}
                            }
                        
                        ai_category_stats[category]['total_evaluations'] += 1
                        
                        try:
                            ai_dimensions = json.loads(evaluation.dimensions_json)
                            self.logger.debug(f"解析到AI维度数据: {ai_dimensions}")
                            
                            for dimension_key, score in ai_dimensions.items():
                                if dimension_key not in ai_category_stats[category]['dimensions']:
                                    max_score = self._get_dimension_max_score_from_standards(
                                        dimension_key, category, standards_data, evaluation.evaluation_criteria
                                    )
                                    ai_category_stats[category]['dimensions'][dimension_key] = {
                                        'scores': [],
                                        'max_possible_score': max_score
                                    }
                                ai_category_stats[category]['dimensions'][dimension_key]['scores'].append(score)
                                
                        except (json.JSONDecodeError, TypeError) as e:
                            self.logger.warning(f"解析AI维度数据失败: {str(e)}")
                    
                    # 处理人工评估数据
                    if evaluation.human_dimensions_json:
                        if category not in human_category_stats:
                            human_category_stats[category] = {
                                'total_evaluations': 0,
                                'dimensions': {}
                            }
                        
                        human_category_stats[category]['total_evaluations'] += 1
                        
                        try:
                            human_dimensions = json.loads(evaluation.human_dimensions_json)
                            self.logger.debug(f"解析到人工维度数据: {human_dimensions}")
                            
                            for dimension_key, score in human_dimensions.items():
                                if dimension_key not in human_category_stats[category]['dimensions']:
                                    max_score = self._get_dimension_max_score_from_standards(
                                        dimension_key, category, standards_data, evaluation.evaluation_criteria
                                    )
                                    human_category_stats[category]['dimensions'][dimension_key] = {
                                        'scores': [],
                                        'max_possible_score': max_score
                                    }
                                human_category_stats[category]['dimensions'][dimension_key]['scores'].append(score)
                                
                        except (json.JSONDecodeError, TypeError) as e:
                            self.logger.warning(f"解析人工维度数据失败: {str(e)}")
                            
                except Exception as e:
                    # 捕获任何在处理单个记录时发生的错误，包括fromisoformat错误
                    self.logger.warning(f"处理评估记录时出错 (ID: {getattr(evaluation, 'id', 'unknown')}): {str(e)}")
                    continue
            
            # 计算AI评估统计数据
            ai_result_stats = self._calculate_dimension_stats(ai_category_stats, standards_data, "AI")
            
            # 计算人工评估统计数据
            human_result_stats = self._calculate_dimension_stats(human_category_stats, standards_data, "人工")
            
            result = {
                'success': True,
                'data': {
                    'ai_evaluation': ai_result_stats,
                    'human_evaluation': human_result_stats,
                    'summary': {
                        'ai_total_evaluations': sum(cat.get('total_evaluations', 0) for cat in ai_result_stats.values()),
                        'human_total_evaluations': sum(cat.get('total_evaluations', 0) for cat in human_result_stats.values()),
                        'ai_categories': len(ai_result_stats),
                        'human_categories': len(human_result_stats)
                    }
                }
            }
            
            self.logger.info("成功获取分离的维度统计信息")
            return result
            
        except Exception as e:
            self.logger.error(f"获取维度统计失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取维度统计失败: {str(e)}'
            }
    
    def _calculate_dimension_stats(self, category_stats, standards_data, evaluation_type):
        """
        计算维度统计数据的通用方法
        
        Args:
            category_stats: 分类统计数据
            standards_data: 标准配置数据
            evaluation_type: 评估类型（AI或人工）
            
        Returns:
            dict: 计算后的统计数据
        """
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
                    
                    # 从标准配置中获取维度显示名称
                    dimension_name = self._get_dimension_display_name_from_standards(
                        dimension_key, category, standards_data
                    )
                    
                    result_stats[category]['dimensions'][dimension_key] = {
                        'dimension_name': dimension_name,
                        'total_evaluations': len(scores),
                        'avg_score': round(sum(scores) / len(scores), 2),
                        'max_possible_score': max_score,
                        'avg_percentage': round(sum(percentages) / len(percentages), 2),
                        'min_percentage': round(min(percentages), 2),
                        'max_percentage': round(max(percentages), 2),
                        'score_distribution': self._calculate_score_distribution(percentages),
                        'evaluation_type': evaluation_type
                    }
        
        return result_stats
    
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
    
    def _get_dimension_display_name(self, dimension_key, evaluation_criteria=None):
        """获取维度显示名称 - 数据库重构后直接返回原始名称"""
        # 数据库重构后，所有维度都已使用新维度体系保存，直接返回原始名称
        return dimension_key
    
    def _normalize_dimension_key(self, dimension_name):
        """标准化维度名称为key"""
        name_mapping = {
            '准确性': 'accuracy', '完整性': 'completeness', '流畅性': 'fluency',
            '安全性': 'safety', '相关性': 'relevance', '清晰度': 'clarity',
            '时效性': 'timeliness', '可用性': 'usability', '合规性': 'compliance',
            '数据准确性': 'data_accuracy', '数据时效性': 'data_timeliness',
            '内容完整性': 'content_completeness', '用户视角': 'user_perspective',
            '用户体验': 'user_experience', '可操作性': 'operability'
        }
        
        # 精确匹配
        if dimension_name.strip() in name_mapping:
            return name_mapping[dimension_name.strip()]
        
        # 模糊匹配 - 检查是否包含关键词
        for cn_name, en_key in name_mapping.items():
            if cn_name in dimension_name or dimension_name in cn_name:
                return en_key
        
        # 返回标准化的英文key
        return dimension_name.strip().lower().replace(' ', '_').replace('/', '_')
    
    def _get_dimension_max_score_from_standards(self, dimension_key, category, standards_data, fallback_criteria=None):
        """从标准配置中获取维度最大分数"""
        # 优先从标准配置中获取
        if category in standards_data:
            for dimension in standards_data[category]:
                if dimension.get('name') == dimension_key:
                    # 从evaluation_criteria中计算最大分数
                    criteria = dimension.get('evaluation_criteria', [])
                    if criteria:
                        max_score = max(c.get('score', 0) for c in criteria)
                        self.logger.debug(f"从标准配置获取维度 {dimension_key} 最大分数: {max_score}")
                        return max_score
        
        # 回退：从evaluation_criteria文本中解析最大分数
        if fallback_criteria:
            max_score = self._parse_max_score_from_criteria_text(dimension_key, fallback_criteria)
            if max_score > 0:
                self.logger.debug(f"从评估标准文本解析维度 {dimension_key} 最大分数: {max_score}")
                return max_score
        
        # 最后回退：使用新维度体系的默认分数
        default_scores = {
            '数据准确性': 2,
            '数据时效性': 2, 
            '内容完整性': 2,
            '用户视角': 2
        }
        
        default_score = default_scores.get(dimension_key, 2)
        self.logger.debug(f"使用默认分数，维度 {dimension_key}: {default_score}")
        return default_score
    
    def _parse_max_score_from_criteria_text(self, dimension_key, criteria_text):
        """从评估标准文本中解析最大分数"""
        import re
        
        # 查找包含维度名称的行
        lines = criteria_text.split('\n')
        for line in lines:
            if dimension_key in line:
                # 匹配 "（最高X分）" 模式
                score_match = re.search(r'（最高(\d+)分）', line)
                if score_match:
                    return int(score_match.group(1))
                
                # 匹配其他可能的分数模式
                score_match = re.search(r'(\d+)分\)', line)
                if score_match:
                    return int(score_match.group(1))
        
        return 0
    
    def _get_dimension_display_name_from_standards(self, dimension_key, category, standards_data):
        """从标准配置中获取维度显示名称 - 数据库重构后直接返回原始名称"""
        # 数据库重构后，所有维度都已使用新维度体系保存，直接返回原始名称
        return dimension_key

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
    
    def get_badcase_statistics(self):
        """
        获取badcase统计信息
        
        Returns:
            dict: badcase统计结果
        """
        try:
            # 总体badcase统计
            total_records = EvaluationHistory.query.count()
            total_badcases = EvaluationHistory.query.filter_by(is_badcase=True).count()
            ai_badcases = EvaluationHistory.query.filter_by(ai_is_badcase=True).count()
            human_badcases = EvaluationHistory.query.filter_by(human_is_badcase=True).count()
            
            # 按分类统计badcase
            category_stats = {}
            categories = db.session.query(EvaluationHistory.classification_level2).distinct().all()
            
            for (category,) in categories:
                if category:
                    category_total = EvaluationHistory.query.filter_by(classification_level2=category).count()
                    category_badcases = EvaluationHistory.query.filter(
                        EvaluationHistory.classification_level2 == category,
                        EvaluationHistory.is_badcase == True
                    ).count()
                    
                    category_stats[category] = {
                        'total_records': category_total,
                        'badcase_count': category_badcases,
                        'badcase_percentage': round((category_badcases / category_total * 100), 2) if category_total > 0 else 0.0
                    }
            
            # 计算总体百分比
            total_badcase_percentage = round((total_badcases / total_records * 100), 2) if total_records > 0 else 0.0
            ai_badcase_percentage = round((ai_badcases / total_records * 100), 2) if total_records > 0 else 0.0
            human_badcase_percentage = round((human_badcases / total_records * 100), 2) if total_records > 0 else 0.0
            
            result = {
                'success': True,
                'data': {
                    'overall': {
                        'total_records': total_records,
                        'total_badcases': total_badcases,
                        'ai_badcases': ai_badcases,
                        'human_badcases': human_badcases,
                        'total_badcase_percentage': total_badcase_percentage,
                        'ai_badcase_percentage': ai_badcase_percentage,
                        'human_badcase_percentage': human_badcase_percentage
                    },
                    'by_category': category_stats
                }
            }
            
            self.logger.info(f"获取badcase统计成功: 总记录{total_records}条，badcase{total_badcases}条({total_badcase_percentage}%)")
            return result
            
        except Exception as e:
            self.logger.error(f"获取badcase统计失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取badcase统计失败: {str(e)}'
            }
    
    def get_badcase_records(self, page=1, per_page=20, badcase_type=None, classification_level2=None):
        """
        获取badcase记录列表
        
        Args:
            page: 页码
            per_page: 每页记录数
            badcase_type: badcase类型 ('ai', 'human', 'all')
            classification_level2: 二级分类筛选
            
        Returns:
            dict: badcase记录列表
        """
        try:
            # 构建查询条件
            query = EvaluationHistory.query.filter_by(is_badcase=True)
            
            # 按badcase类型筛选
            if badcase_type == 'ai':
                query = query.filter_by(ai_is_badcase=True)
            elif badcase_type == 'human':
                query = query.filter_by(human_is_badcase=True)
            # badcase_type == 'all' 或者为空时，不添加额外筛选条件
            
            # 按分类筛选
            if classification_level2:
                query = query.filter_by(classification_level2=classification_level2)
            
            # 按创建时间降序排列
            query = query.order_by(EvaluationHistory.created_at.desc())
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            # 转换为字典格式
            records = [record.to_dict() for record in pagination.items]
            
            result = {
                'success': True,
                'data': {
                    'items': records,
                    'pagination': {
                        'page': pagination.page,
                        'per_page': pagination.per_page,
                        'total': pagination.total,
                        'pages': pagination.pages,
                        'has_prev': pagination.has_prev,
                        'has_next': pagination.has_next
                    }
                }
            }
            
            self.logger.info(f"获取badcase记录成功: 第{page}页，每页{per_page}条，共{pagination.total}条")
            return result
            
        except Exception as e:
            self.logger.error(f"获取badcase记录失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取badcase记录失败: {str(e)}'
            }
    
    def get_badcase_reasons_by_category(self, category):
        """
        获取指定分类下所有badcase的原因汇总
        
        Args:
            category: 分类名称
            
        Returns:
            dict: badcase原因列表
        """
        try:
            # 查询该分类下所有badcase记录的原因
            badcase_records = EvaluationHistory.query.filter(
                EvaluationHistory.classification_level2 == category,
                EvaluationHistory.is_badcase == True
            ).all()
            
            reasons = []
            for record in badcase_records:
                # 收集AI判断的badcase原因
                if record.ai_is_badcase and record.ai_badcase_reason:
                    reasons.append({
                        'type': 'ai',
                        'reason': record.ai_badcase_reason,
                        'record_id': record.id,
                        'question': record.question_text[:100] + '...' if len(record.question_text) > 100 else record.question_text
                    })
                
                # 收集人工标记的badcase原因
                if record.human_is_badcase and record.human_badcase_reason:
                    reasons.append({
                        'type': 'human',
                        'reason': record.human_badcase_reason,
                        'record_id': record.id,
                        'question': record.question_text[:100] + '...' if len(record.question_text) > 100 else record.question_text
                    })
            
            result = {
                'success': True,
                'data': {
                    'category': category,
                    'total_badcases': len(badcase_records),
                    'total_reasons': len(reasons),
                    'reasons': reasons
                }
            }
            
            self.logger.info(f"获取分类 {category} 的badcase原因成功: {len(reasons)}条原因")
            return result
            
        except Exception as e:
            self.logger.error(f"获取分类badcase原因失败: {str(e)}")
            return {
                'success': False,
                'message': f'获取分类badcase原因失败: {str(e)}'
            } 