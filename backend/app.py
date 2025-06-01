import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# 导入配置
from config import config

# 导入数据库模型
from models.classification import db

# 导入服务类
from services.evaluation_service import EvaluationService
from services.classification_service_sqlite import ClassificationService
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
            
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'ok',
        'message': '问答评估服务运行正常',
        'timestamp': datetime.now().isoformat(),
        'database': 'sqlite',
        'version': '2.0.0'
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
        question_time = data.get('question_time', datetime.now().isoformat())
        evaluation_criteria = data.get('evaluation_criteria', '请评估答案的准确性、相关性和有用性')
        
        logger.info(f"开始评估 - 用户问题长度: {len(user_input)}, 模型回答长度: {len(model_answer)}, 问题时间: {question_time}, 评估标准长度: {len(evaluation_criteria)}")
        
        # 首先进行分类
        classification_result = classification_service.classify_user_input(user_input)
        logger.info(f"分类结果: {classification_result.get('level1', 'N/A')} -> {classification_result.get('level2', 'N/A')} -> {classification_result.get('level3', 'N/A')}")
        
        # 根据分类结果选择对应的prompt模板
        prompt_template = classification_service.get_prompt_template_by_classification(classification_result)
        
        # 进行评估
        result = evaluation_service.evaluate_qa(
            user_input=user_input,
            model_answer=model_answer,
            evaluation_criteria=evaluation_criteria,
            question_time=question_time,
            prompt_template=prompt_template
        )
        
        # 添加分类信息到结果中
        result['classification'] = {
            'level1': classification_result.get('level1'),
            'level2': classification_result.get('level2'),
            'level3': classification_result.get('level3'),
            'confidence': classification_result.get('confidence'),
            'classification_time': classification_result.get('classification_time_seconds')
        }
        
        logger.info(f"评估完成 - 总分: {result.get('total_score', 'N/A')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"评估失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/classify', methods=['POST'])
def classify():
    """分类用户输入"""
    try:
        logger.info("收到分类请求")
        
        data = request.get_json()
        
        if 'userQuery' not in data:
            return jsonify({'error': '缺少用户查询'}), 400
            
        user_query = data['userQuery']
        
        # 调用分类服务
        result = classification_service.classify_user_input(user_query)
        
        logger.info(f"分类完成 - 结果: {result.get('level1', 'N/A')}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"分类失败: {e}")
        return jsonify({'error': str(e)}), 500

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
    """根据分类获取prompt模板"""
    try:
        data = request.get_json()
        
        if 'classification' not in data:
            return jsonify({'error': '缺少分类信息'}), 400
            
        classification = data['classification']
        
        # 调用分类服务获取prompt模板
        prompt_template = classification_service.get_prompt_template_by_classification(classification)
        
        return jsonify({
            'prompt_template': prompt_template,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取prompt模板失败: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("启动问答评估服务...")
    app.run(host='0.0.0.0', port=5001, debug=True) 