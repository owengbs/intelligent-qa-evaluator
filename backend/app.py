from flask import Flask, request, jsonify
from flask_cors import CORS
from services.evaluation_service import EvaluationService
from utils.logger import get_logger
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化日志和服务
logger = get_logger(__name__)
evaluation_service = EvaluationService()

@app.route('/api/evaluate', methods=['POST'])
def evaluate_qa():
    """
    问答质量评估API端点
    接收用户输入、模型回答、参考答案、问题时间和评分规则，返回评分结果
    """
    try:
        logger.info("收到评估请求")
        
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['userQuery', 'modelResponse', 'referenceAnswer', 'scoringPrompt', 'questionTime', 'evaluationCriteria']
        for field in required_fields:
            if not data.get(field):
                logger.warning(f"缺少必要字段: {field}")
                return jsonify({'error': f'缺少必要字段: {field}'}), 400
        
        logger.info(f"开始评估 - 用户问题长度: {len(data['userQuery'])}, 模型回答长度: {len(data['modelResponse'])}, 问题时间: {data.get('questionTime', 'N/A')}, 评估标准长度: {len(data.get('evaluationCriteria', ''))}")
        
        # 调用评估服务
        result = evaluation_service.evaluate_response(
            user_query=data['userQuery'],
            model_response=data['modelResponse'], 
            reference_answer=data['referenceAnswer'],
            scoring_prompt=data['scoringPrompt'],
            question_time=data['questionTime'],
            evaluation_criteria=data['evaluationCriteria']
        )
        
        logger.info(f"评估完成 - 总分: {result.get('score', 'N/A')}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"评估过程中发生错误: {str(e)}")
        return jsonify({'error': f'评估失败: {str(e)}'}), 500

@app.route('/api/validate-prompt', methods=['POST'])
def validate_prompt():
    """
    验证prompt模板中的变量是否正确
    """
    try:
        logger.info("收到prompt验证请求")
        
        # 获取请求数据
        data = request.get_json()
        
        if not data.get('scoringPrompt'):
            logger.warning("缺少scoringPrompt字段")
            return jsonify({'error': '缺少scoringPrompt字段'}), 400
        
        # 调用验证服务
        validation_result = evaluation_service.validate_prompt_variables(data['scoringPrompt'])
        
        logger.info(f"prompt验证完成 - 有效性: {validation_result['is_valid']}")
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"prompt验证过程中发生错误: {str(e)}")
        return jsonify({'error': f'验证失败: {str(e)}'}), 500

@app.route('/api/variable-info', methods=['GET'])
def get_variable_info():
    """
    获取支持的变量信息
    """
    try:
        variable_info = {
            'required_variables': [
                {
                    'standard_name': 'user_input',
                    'alternatives': evaluation_service.variable_mapping['user_input'],
                    'description': '用户的原始问题'
                },
                {
                    'standard_name': 'model_answer', 
                    'alternatives': evaluation_service.variable_mapping['model_answer'],
                    'description': '待评估的模型回答'
                },
                {
                    'standard_name': 'reference_answer',
                    'alternatives': evaluation_service.variable_mapping['reference_answer'], 
                    'description': '标准参考答案'
                },
                {
                    'standard_name': 'question_time',
                    'alternatives': evaluation_service.variable_mapping['question_time'], 
                    'description': '问题提出时间'
                },
                {
                    'standard_name': 'evaluation_criteria',
                    'alternatives': evaluation_service.variable_mapping['evaluation_criteria'], 
                    'description': '详细的评估标准和评分规则'
                }
            ],
            'usage_example': "评估标准:\n{evaluation_criteria}\n\n问题时间: {question_time}\n用户输入: {user_input}\n模型回答: {model_answer}\n参考答案: {reference_answer}"
        }
        
        return jsonify(variable_info)
        
    except Exception as e:
        logger.error(f"获取变量信息时发生错误: {str(e)}")
        return jsonify({'error': f'获取变量信息失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'service': 'qa-evaluator'})

if __name__ == '__main__':
    logger.info("启动问答评估服务...")
    app.run(debug=True, host='0.0.0.0', port=5001) 