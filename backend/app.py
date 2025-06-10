import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import traceback
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入配置
from config import config

# 导入数据库模型
from models.classification import db

# 导入服务类
from services.evaluation_service import EvaluationService
from services.classification_service_sqlite import ClassificationService
from services.evaluation_standard_service import EvaluationStandardService
from services.evaluation_history_service import EvaluationHistoryService
from services.ai_assistant import ai_assistant
from utils.logger import get_logger

# 导入路由蓝图
from routes.upload_routes import upload_bp
from routes.evaluation_dimension_routes import evaluation_dimension_bp
from routes.evaluation_standard_config_routes import evaluation_standard_config_bp

# 创建Flask应用
app = Flask(__name__)

# 加载配置 - 直接使用config对象而不是config[env]
app.config.from_object(config)

# 启用CORS
CORS(app)

# 注册蓝图
app.register_blueprint(upload_bp)
app.register_blueprint(evaluation_dimension_bp)
app.register_blueprint(evaluation_standard_config_bp)

# 获取日志记录器
logger = get_logger(__name__)

# 初始化数据库
db.init_app(app)

# 创建服务实例
evaluation_service = EvaluationService()
classification_service = ClassificationService(app)
evaluation_standard_service = EvaluationStandardService(app)
evaluation_history_service = EvaluationHistoryService(app)

# 创建数据库表
with app.app_context():
    try:
        db.create_all()
        logger.info("数据库表创建完成")
        
        # 检查是否需要初始化默认数据
        from models.classification import ClassificationStandard
        default_count = ClassificationStandard.query.filter_by(is_default=True).count()
        
        if default_count == 0:
            logger.info("未发现默认分类标准，开始初始化...")
            # 运行数据库初始化
            from database.init_db import init_database
            init_database()
        
        # 初始化评估标准数据
        evaluation_standard_service.init_default_evaluation_standards()
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1.0'
    })

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """API健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.1.0',
        'api_status': 'active'
    })

@app.route('/api/variable-info', methods=['GET'])
def get_variable_info():
    """获取可用变量信息"""
    try:
        variable_info = evaluation_service.get_variable_info()
        return jsonify(variable_info)
    except Exception as e:
        logger.error(f"获取变量信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """评估问答质量"""
    try:
        logger.info("收到评估请求")
        
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['user_input', 'model_answer']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必需字段: {field}'}), 400
        
        user_input = data['user_input']
        model_answer = data['model_answer']
        reference_answer = data.get('reference_answer', '')  # 参考答案，可选
        question_time = data.get('question_time', datetime.now().isoformat())
        evaluation_criteria = data.get('evaluation_criteria', '请评估答案的准确性、相关性和有用性')
        scoring_prompt = data.get('scoring_prompt')  # 自定义的评分prompt
        uploaded_images = data.get('uploaded_images', [])  # 上传的图片信息
        
        logger.info(f"开始评估 - 用户问题长度: {len(user_input)}, 模型回答长度: {len(model_answer)}, 参考答案长度: {len(reference_answer)}, 问题时间: {question_time}, 评估标准长度: {len(evaluation_criteria)}, 图片数量: {len(uploaded_images)}")
        
        # 首先进行分类
        classification_result = classification_service.classify_user_input(user_input)
        logger.info(f"分类结果: {classification_result.get('level1', 'N/A')} -> {classification_result.get('level2', 'N/A')} -> {classification_result.get('level3', 'N/A')}")
        
        # 获取分类对应的新维度体系评估标准
        new_evaluation_criteria = None
        if classification_result and classification_result.get('level2'):
            try:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
                from database_operations import db_ops
                template_result = db_ops.format_for_evaluation_template(classification_result.get('level2'))
                if template_result['success'] and template_result['data']:
                    template_data = template_result['data']
                    # 构建基于新维度体系的评估标准
                    criteria_parts = []
                    for dimension in template_data.get('dimensions', []):
                        dim_name = dimension.get('name')
                        reference_standard = dimension.get('reference_standard')
                        scoring_principle = dimension.get('scoring_principle')
                        max_score = dimension.get('max_score', 2)
                        
                        criteria_parts.append(f"{dim_name}（最高{max_score}分）：\n定义：{reference_standard}\n评分原则：{scoring_principle}")
                    
                    if criteria_parts:
                        new_evaluation_criteria = "\n\n".join(criteria_parts)
                        logger.info(f"使用新维度体系评估标准，包含 {len(template_data.get('dimensions', []))} 个维度")
            except Exception as e:
                logger.warning(f"获取新维度体系评估标准失败，将使用默认标准: {str(e)}")
        
        # 如果有新的评估标准，使用新标准；否则使用原评估标准
        if new_evaluation_criteria:
            evaluation_criteria = new_evaluation_criteria
        
        # 选择prompt模板：优先使用自定义的scoring_prompt，否则使用分类对应的prompt_template
        if scoring_prompt:
            prompt_template = scoring_prompt
            logger.info("使用自定义的scoring_prompt作为评估模板")
        else:
            prompt_template = classification_service.get_prompt_template_by_classification(classification_result)
            logger.info("使用分类对应的prompt_template作为评估模板")
        
        # 调用评估服务
        result = evaluation_service.evaluate_response(
            user_query=user_input,
            model_response=model_answer,
            reference_answer=reference_answer,
            scoring_prompt=prompt_template,
            question_time=question_time,
            evaluation_criteria=evaluation_criteria
        )
        
        # 计算加权平均总分
        if result.get('dimensions') and classification_result and classification_result.get('level2'):
            try:
                weighted_score = evaluation_service.calculate_weighted_score(
                    result['dimensions'], 
                    classification_result['level2']
                )
                result['score'] = weighted_score / 10.0  # 转换为10分制显示，但内部存储为百分比
                result['weighted_score'] = weighted_score  # 保存百分比形式的分数
                logger.info(f"计算加权平均分数: {weighted_score:.2f}% -> 显示分数: {result['score']:.2f}/10")
            except Exception as e:
                logger.error(f"计算加权平均分数失败: {str(e)}")
                # 使用原有分数作为备用
        
        # 添加分类信息到评估结果
        if classification_result:
            result['classification'] = classification_result
        
        # 添加模型使用信息
        result['model_used'] = 'deepseek-chat'  # 记录使用的模型
        
        # AI自动判断是否为badcase（基于分数阈值）
        ai_badcase_threshold = 50.0  # 低于50%认为是badcase
        result['ai_is_badcase'] = (result.get('weighted_score', 100.0) < ai_badcase_threshold)
        
        # 保存评估结果到历史记录
        try:
            # 准备保存的数据
            save_data = {
                'user_input': user_input,
                'model_answer': model_answer,
                'reference_answer': reference_answer,
                'question_time': question_time,
                'evaluation_criteria_used': evaluation_criteria,
                'score': result.get('weighted_score', result.get('score', 0)) / 10.0,  # 保存为10分制
                'dimensions': result.get('dimensions', {}),
                'reasoning': result.get('reasoning'),
                'evaluation_time_seconds': result.get('evaluation_time_seconds'),
                'model_used': result.get('model_used'),
                'raw_response': result.get('raw_response'),
                'uploaded_images': uploaded_images,  # 添加图片信息
                'ai_is_badcase': result.get('ai_is_badcase', False),  # AI判断的badcase
                'is_badcase': result.get('ai_is_badcase', False)  # 初始设置为AI判断结果
            }
            
            # 保存到历史记录
            save_result = evaluation_history_service.save_evaluation_result(
                save_data, classification_result
            )
            
            if save_result['success']:
                logger.info(f"评估结果已保存到历史记录，ID: {save_result['history_id']}")
                result['history_id'] = save_result['history_id']
            else:
                logger.warning(f"保存评估历史失败: {save_result['message']}")
                
        except Exception as save_error:
            logger.error(f"保存评估历史时发生错误: {str(save_error)}")
            # 不影响评估结果的返回
        
        logger.info(f"评估完成，总分: {result.get('score', 0)}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"评估过程中发生错误: {str(e)}")
        logger.error(f"错误追踪: {traceback.format_exc()}")
        return jsonify({'error': f'评估过程中发生错误: {str(e)}'}), 500

@app.route('/api/classify', methods=['POST'])
def classify():
    """分类用户输入"""
    try:
        logger.info("收到分类请求")
        
        data = request.get_json()
        
        if 'userQuery' not in data:
            return jsonify({'error': '缺少必需字段: userQuery'}), 400
        
        user_query = data['userQuery']
        
        logger.info(f"开始分类用户输入: {user_query[:100]}...")
        
        result = classification_service.classify_user_input(user_query)
        
        if result:
            logger.info(f"分类成功: {result.get('level1', 'N/A')} -> {result.get('level2', 'N/A')} -> {result.get('level3', 'N/A')}")
            return jsonify(result)
        else:
            logger.error("分类失败，返回空结果")
            return jsonify({'error': '分类失败'}), 500
            
    except Exception as e:
        logger.error(f"分类过程中发生错误: {str(e)}")
        logger.error(f"错误追踪: {traceback.format_exc()}")
        return jsonify({'error': f'分类过程中发生错误: {str(e)}'}), 500

@app.route('/api/classification-standards', methods=['GET'])
def get_classification_standards():
    """获取分类标准"""
    try:
        result = classification_service.get_classification_standards()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取分类标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classification-standards', methods=['POST'])
def update_classification_standards():
    """更新分类标准"""
    try:
        data = request.get_json()
        
        if 'standards' not in data:
            return jsonify({'error': '缺少分类标准数据'}), 400
            
        new_standards = data['standards']
        
        # 调用分类服务更新标准
        result = classification_service.update_classification_standards(new_standards)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"更新分类标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classification-standards/reset', methods=['POST'])
def reset_classification_standards():
    """重置分类标准为默认值"""
    try:
        result = classification_service.reset_classification_standards()
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"重置分类标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classification-history', methods=['GET'])
def get_classification_history():
    """获取分类历史记录"""
    try:
        limit = request.args.get('limit', 100, type=int)
        result = classification_service.get_classification_history(limit)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取分类历史失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-prompt-by-classification', methods=['POST'])
def get_prompt_by_classification():
    """根据分类获取对应的Prompt模板"""
    try:
        data = request.get_json()
        
        if 'classification' not in data:
            return jsonify({'error': '缺少分类信息'}), 400
            
        classification = data['classification']
        
        # 调用分类服务获取对应的prompt模板
        prompt_template = classification_service.get_prompt_template_by_classification(classification)
        
        return jsonify({
            'success': True,
            'prompt_template': prompt_template,
            'classification': classification
        })
        
    except Exception as e:
        logger.error(f"获取Prompt模板失败: {e}")
        return jsonify({'error': str(e)}), 500

# 评估标准相关API接口
@app.route('/api/evaluation-standards', methods=['GET'])
def get_evaluation_standards():
    """获取所有评估标准"""
    try:
        logger.info("获取所有评估标准")
        
        standards = evaluation_standard_service.get_all_evaluation_standards()
        
        return jsonify({
            'success': True,
            'data': standards
        })
        
    except Exception as e:
        logger.error(f"获取评估标准失败: {str(e)}")
        return jsonify({'error': f'获取评估标准失败: {str(e)}'}), 500

@app.route('/api/evaluation-standards/grouped', methods=['GET'])
def get_evaluation_standards_grouped():
    """按分类分组获取评估标准"""
    try:
        result = evaluation_standard_service.get_evaluation_standards_grouped_by_category()
        
        return jsonify({
            'success': True,
            'data': result,
            'categories': list(result.keys())
        })
        
    except Exception as e:
        logger.error(f"获取分组评估标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation-standards', methods=['POST'])
def create_evaluation_standard():
    """创建新的评估标准"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['level2_category', 'dimension', 'reference_standard', 'scoring_principle']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必要字段: {field}'}), 400
        
        result = evaluation_standard_service.create_evaluation_standard(data)
        
        return jsonify({
            'success': True,
            'message': '评估标准创建成功',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"创建评估标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation-standards/<int:standard_id>', methods=['PUT'])
def update_evaluation_standard(standard_id):
    """更新评估标准"""
    try:
        data = request.get_json()
        
        result = evaluation_standard_service.update_evaluation_standard(standard_id, data)
        
        return jsonify({
            'success': True,
            'message': '评估标准更新成功',
            'data': result
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"更新评估标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation-standards/<int:standard_id>', methods=['DELETE'])
def delete_evaluation_standard(standard_id):
    """删除评估标准"""
    try:
        evaluation_standard_service.delete_evaluation_standard(standard_id)
        
        return jsonify({
            'success': True,
            'message': '评估标准删除成功'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"删除评估标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation-standards/batch', methods=['POST'])
def batch_update_evaluation_standards():
    """批量更新评估标准"""
    try:
        data = request.get_json()
        
        if 'standards' not in data:
            return jsonify({'error': '缺少评估标准数据'}), 400
        
        standards_list = data['standards']
        updated_count = evaluation_standard_service.batch_update_evaluation_standards(standards_list)
        
        return jsonify({
            'success': True,
            'message': f'批量更新完成，共处理 {updated_count} 条评估标准',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"批量更新评估标准失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/evaluation-template/<category>', methods=['GET'])
def get_evaluation_template(category):
    """根据分类获取评估模板"""
    try:
        logger.info(f"获取评估模板请求: {category}")
        
        # 优先使用新的标准配置服务
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
            from database_operations import db_ops
            result = db_ops.format_for_evaluation_template(category)
            if result['success']:
                logger.info(f"使用新标准配置获取评估模板成功: {category}")
                return jsonify(result)
            else:
                logger.info(f"新标准配置未找到模板，尝试使用旧服务: {result.get('message', '')}")
        except Exception as new_service_error:
            logger.warning(f"新标准配置服务失败，回退到旧服务: {str(new_service_error)}")
        
        # 回退到原有的服务
        template = evaluation_standard_service.get_evaluation_template_by_category(category)
        
        if template:
            return jsonify({
                'success': True,
                'data': template
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到分类 {category} 的评估模板'
            }), 404
            
    except Exception as e:
        logger.error(f"获取评估模板失败: {str(e)}")
        return jsonify({'error': f'获取评估模板失败: {str(e)}'}), 500

# ==================== 新增：评估历史管理API ==================== 

@app.route('/api/evaluation-history', methods=['GET'])
def get_evaluation_history():
    """获取评估历史记录（分页）"""
    try:
        logger.info("获取评估历史记录")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        classification_level2 = request.args.get('classification_level2')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 调用服务获取历史记录
        result = evaluation_history_service.get_evaluation_history(
            page=page,
            per_page=per_page,
            classification_level2=classification_level2,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取评估历史失败: {str(e)}")
        return jsonify({'error': f'获取评估历史失败: {str(e)}'}), 500

@app.route('/api/evaluation-history', methods=['POST'])
def create_evaluation_history():
    """保存评估历史记录"""
    try:
        logger.info("保存评估历史记录")
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': '缺少评估数据'}), 400
        
        # 调用服务保存记录
        result = evaluation_history_service.save_evaluation_result(data)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"保存评估历史失败: {str(e)}")
        return jsonify({'error': f'保存评估历史失败: {str(e)}'}), 500

@app.route('/api/evaluation-history/<int:history_id>', methods=['GET'])
def get_evaluation_by_id(history_id):
    """根据ID获取单个评估记录"""
    try:
        logger.info(f"获取评估记录: {history_id}")
        
        result = evaluation_history_service.get_evaluation_by_id(history_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取评估记录失败: {str(e)}")
        return jsonify({'error': f'获取评估记录失败: {str(e)}'}), 500

@app.route('/api/evaluation-history/<int:history_id>', methods=['DELETE'])
def delete_evaluation(history_id):
    """删除评估记录"""
    try:
        logger.info(f"删除评估记录: {history_id}")
        
        result = evaluation_history_service.delete_evaluation(history_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"删除评估记录失败: {str(e)}")
        return jsonify({'error': f'删除评估记录失败: {str(e)}'}), 500

@app.route('/api/evaluation-history/<int:history_id>/human-evaluation', methods=['PUT'])
def update_human_evaluation(history_id):
    """更新人工评估结果"""
    try:
        logger.info(f"更新人工评估: {history_id}")
        
        data = request.get_json()
        
        # 验证必要字段
        if not data:
            return jsonify({'error': '缺少评估数据'}), 400
        
        # 获取评估者姓名（可以从请求头或session中获取，这里暂时使用默认值）
        evaluator_name = data.get('evaluator_name', '匿名用户')
        
        # 调用服务更新人工评估
        result = evaluation_history_service.update_human_evaluation(
            history_id=history_id,
            human_data=data,
            evaluator_name=evaluator_name
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"更新人工评估失败: {str(e)}")
        return jsonify({'error': f'更新人工评估失败: {str(e)}'}), 500

@app.route('/api/evaluation-statistics', methods=['GET'])
def get_evaluation_statistics():
    """获取评估统计信息"""
    try:
        logger.info("获取评估统计信息")
        
        result = evaluation_history_service.get_evaluation_statistics()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取评估统计失败: {str(e)}")
        return jsonify({'error': f'获取评估统计失败: {str(e)}'}), 500

@app.route('/api/dimension-statistics', methods=['GET'])
def get_dimension_statistics():
    """获取维度统计信息"""
    try:
        logger.info("获取维度统计信息")
        
        result = evaluation_history_service.get_dimension_statistics()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取维度统计失败: {str(e)}")
        return jsonify({'error': f'获取维度统计失败: {str(e)}'}), 500

@app.route('/api/badcase-statistics', methods=['GET'])
def get_badcase_statistics():
    """获取badcase统计信息"""
    try:
        logger.info("获取badcase统计信息")
        
        result = evaluation_history_service.get_badcase_statistics()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取badcase统计失败: {str(e)}")
        return jsonify({'error': f'获取badcase统计失败: {str(e)}'}), 500

@app.route('/api/badcase-records', methods=['GET'])
def get_badcase_records():
    """获取badcase记录列表"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        badcase_type = request.args.get('badcase_type')  # 'ai', 'human', 'all'
        classification_level2 = request.args.get('classification_level2')
        
        result = evaluation_history_service.get_badcase_records(
            page=page,
            per_page=per_page,
            badcase_type=badcase_type,
            classification_level2=classification_level2
        )
        
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"获取badcase记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取badcase记录失败: {str(e)}'
        }), 500

@app.route('/api/badcase-reasons/<category>', methods=['GET'])
def get_badcase_reasons_by_category(category):
    """获取指定分类下的badcase原因"""
    try:
        # 获取查询参数，允许指定原因类型
        reason_type = request.args.get('reason_type', 'human')  # 默认为人工评估
        
        logger.info(f"获取分类 {category} 的badcase原因 (类型: {reason_type})")
        
        result = evaluation_history_service.get_badcase_reasons_by_category(category, reason_type=reason_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取badcase原因失败: {str(e)}")
        return jsonify({'error': f'获取badcase原因失败: {str(e)}'}), 500

@app.route('/api/badcase-summary/<category>', methods=['POST'])
def generate_badcase_summary(category):
    """生成指定分类的badcase AI总结"""
    import time
    request_start_time = time.time()
    
    try:
        logger.info(f"🎯 [智能分析请求] 开始处理badcase AI总结")
        logger.info(f"   - 请求分类: {category}")
        logger.info(f"   - 请求时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"   - 客户端IP: {request.remote_addr}")
        
        # 首先获取该分类的人工评估badcase原因（用于AI总结）
        logger.info(f"📋 第一步: 获取分类 {category} 的人工评估badcase原因")
        reasons_result = evaluation_history_service.get_badcase_reasons_by_category(category, reason_type='human')
        
        if not reasons_result['success']:
            logger.warning(f"⚠️  获取badcase原因失败: {reasons_result.get('message', '未知错误')}")
            return jsonify(reasons_result), 400
        
        # 检查是否有足够的人工评估原因进行总结
        reasons_data = reasons_result['data']
        logger.info(f"📊 获取到的原因数据:")
        logger.info(f"   - 总badcase记录数: {reasons_data.get('total_badcases', 0)}")
        logger.info(f"   - 人工评估原因数: {len(reasons_data.get('reasons', []))}")
        
        if len(reasons_data['reasons']) == 0:
            logger.warning(f"⚠️  分类 {category} 下没有人工评估的badcase原因可供总结")
            return jsonify({
                'success': False,
                'message': f'分类 {category} 下没有人工评估的badcase原因可供总结'
            }), 400
        
        # 显示原因详情
        logger.info(f"📝 人工评估原因详情:")
        for i, reason in enumerate(reasons_data['reasons'][:5], 1):  # 只显示前5条
            logger.info(f"   {i}. [记录#{reason.get('record_id', '未知')}] {reason.get('reason', '无原因')[:100]}...")
        
        if len(reasons_data['reasons']) > 5:
            logger.info(f"   ... 还有 {len(reasons_data['reasons']) - 5} 条原因")
        
        # 导入AI总结服务
        logger.info(f"🤖 第二步: 启动AI总结服务")
        from services.ai_summary_service import ai_summary_service
        
        # 调用AI总结服务
        logger.info(f"🚀 第三步: 开始调用AI总结分析...")
        summary_result = ai_summary_service.summarize_badcase_reasons(category, reasons_data)
        
        # 计算处理时间
        request_end_time = time.time()
        processing_time = request_end_time - request_start_time
        
        if summary_result.get('success'):
            logger.info(f"✅ [智能分析完成] badcase AI总结生成成功")
            logger.info(f"   - 处理时长: {processing_time:.2f}秒")
            logger.info(f"   - 分析分类: {category}")
            logger.info(f"   - 总结状态: 成功")
        else:
            logger.error(f"❌ [智能分析失败] badcase AI总结生成失败")
            logger.error(f"   - 处理时长: {processing_time:.2f}秒")
            logger.error(f"   - 失败原因: {summary_result.get('message', '未知错误')}")
        
        return jsonify(summary_result)
        
    except Exception as e:
        request_end_time = time.time()
        processing_time = request_end_time - request_start_time
        
        logger.error(f"💥 [智能分析异常] badcase总结过程发生异常:")
        logger.error(f"   - 异常类型: {type(e).__name__}")
        logger.error(f"   - 异常信息: {str(e)}")
        logger.error(f"   - 处理时长: {processing_time:.2f}秒")
        logger.error(f"   - 请求分类: {category}")
        
        return jsonify({'error': f'生成badcase总结失败: {str(e)}'}), 500

@app.route('/api/evaluation-standards/<category>/weights', methods=['PUT'])
def update_dimension_weights(category):
    """更新指定分类下各维度的权重"""
    try:
        logger.info(f"更新分类 {category} 的维度权重")
        
        data = request.get_json()
        
        if not data or 'weights' not in data:
            return jsonify({'error': '缺少权重数据'}), 400
        
        weight_updates = data['weights']
        
        result = evaluation_standard_service.update_dimension_weights(category, weight_updates)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"更新维度权重失败: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== 错误处理 ==================== 

# ==================== AI助手API ==================== 

@app.route('/api/ai-assistant/ask', methods=['POST'])
def ask_ai_assistant():
    """询问AI助手"""
    try:
        logger.info("收到AI助手请求")
        
        data = request.get_json()
        
        # 验证必需字段
        if 'question' not in data:
            return jsonify({'error': '缺少必需字段: question'}), 400
        
        question = data['question'].strip()
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
        
        logger.info(f"AI助手问题: {question[:100]}...")
        
        # 调用AI助手服务
        result = ai_assistant.ask_ai(question)
        
        if result['success']:
            logger.info("✅ AI助手回答成功")
            return jsonify({
                'success': True,
                'answer': result['answer'],
                'message': result['message']
            })
        else:
            logger.error(f"❌ AI助手回答失败: {result['message']}")
            return jsonify({
                'success': False,
                'error': result['message']
            }), 500
            
    except Exception as e:
        logger.error(f"AI助手服务异常: {e}")
        traceback.print_exc()
        return jsonify({'error': f'AI助手服务异常: {str(e)}'}), 500

# ==================== 新增：标准配置管理API ==================== 

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类选项"""
    try:
        logger.info("获取分类选项")
        
        result = evaluation_history_service.get_categories()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取分类选项失败: {str(e)}")
        return jsonify({'error': f'获取分类选项失败: {str(e)}'}), 500

@app.route('/api/standard-config', methods=['GET'])
def get_all_category_standards():
    """获取所有分类的标准配置"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
        from database_operations import db_ops
        result = db_ops.get_all_category_standards()
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取标准配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取标准配置失败: {str(e)}'
        }), 500

@app.route('/api/standard-config/<category>', methods=['GET'])
def get_category_standards(category):
    """获取指定分类的标准配置"""
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
        from database_operations import db_ops
        result = db_ops.get_category_standards(category)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取分类标准配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取分类标准配置失败: {str(e)}'
        }), 500

@app.route('/api/standard-config/<category>', methods=['POST'])
def save_category_standards(category):
    """保存指定分类的标准配置"""
    try:
        data = request.get_json()
        if not data or 'dimension_ids' not in data:
            return jsonify({
                'success': False,
                'message': '请提供dimension_ids参数'
            }), 400
        
        dimension_ids = data['dimension_ids']
        if not isinstance(dimension_ids, list):
            return jsonify({
                'success': False,
                'message': 'dimension_ids必须是数组格式'
            }), 400
        
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
        from database_operations import db_ops
        result = db_ops.save_category_standards(category, dimension_ids)
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"保存分类标准配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存分类标准配置失败: {str(e)}'
        }), 500

# ==================== 错误处理 ==================== 

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    from config import config, print_config_info
    
    print_config_info()
    logger.info(f"启动问答评估服务 - {config.ENVIRONMENT}环境...")
    
    app.run(
        host=config.HOST, 
        port=config.PORT, 
        debug=config.DEBUG
    ) 