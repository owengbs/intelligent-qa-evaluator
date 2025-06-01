import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import traceback

# 导入配置
from config import config

# 导入数据库模型
from models.classification import db

# 导入服务类
from services.evaluation_service import EvaluationService
from services.classification_service_sqlite import ClassificationService
from services.evaluation_standard_service import EvaluationStandardService
from services.evaluation_history_service import EvaluationHistoryService
from utils.logger import get_logger

# 获取环境变量
env = os.environ.get('FLASK_ENV', 'development')

# 创建Flask应用
app = Flask(__name__)

# 加载配置
app.config.from_object(config[env])

# 启用CORS
CORS(app)

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
        
        logger.info(f"开始评估 - 用户问题长度: {len(user_input)}, 模型回答长度: {len(model_answer)}, 参考答案长度: {len(reference_answer)}, 问题时间: {question_time}, 评估标准长度: {len(evaluation_criteria)}")
        
        # 首先进行分类
        classification_result = classification_service.classify_user_input(user_input)
        logger.info(f"分类结果: {classification_result.get('level1', 'N/A')} -> {classification_result.get('level2', 'N/A')} -> {classification_result.get('level3', 'N/A')}")
        
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
        
        # 添加分类信息到评估结果
        if classification_result:
            result['classification'] = classification_result
        
        # 添加模型使用信息
        result['model_used'] = 'deepseek-chat'  # 记录使用的模型
        
        # 保存评估结果到历史记录
        try:
            # 准备保存的数据
            save_data = {
                'user_input': user_input,
                'model_answer': model_answer,
                'reference_answer': reference_answer,
                'question_time': question_time,
                'evaluation_criteria_used': evaluation_criteria,
                'score': result.get('score'),
                'dimensions': result.get('dimensions', {}),
                'reasoning': result.get('reasoning'),
                'evaluation_time_seconds': result.get('evaluation_time_seconds'),
                'model_used': result.get('model_used'),
                'raw_response': result.get('raw_response')
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

# ==================== 错误处理 ==================== 

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'API接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    logger.info("启动问答评估服务...")
    app.run(host='0.0.0.0', port=5001, debug=True) 