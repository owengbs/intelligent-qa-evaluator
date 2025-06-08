#!/usr/bin/env python3
"""
评估标准配置API路由
"""

from flask import Blueprint, request, jsonify
from services.evaluation_standard_config_service import EvaluationStandardConfigService

# 创建蓝图
evaluation_standard_config_bp = Blueprint('evaluation_standard_config', __name__)

@evaluation_standard_config_bp.route('/standard-config/<category>', methods=['GET'])
def get_category_standards(category):
    """
    获取指定分类的标准配置
    
    Args:
        category (str): 二级分类名称
    
    Returns:
        JSON: 标准配置数据
    """
    try:
        result = EvaluationStandardConfigService.get_category_standards(category)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取标准配置失败: {str(e)}'
        }), 500

@evaluation_standard_config_bp.route('/standard-config', methods=['GET'])
def get_all_category_standards():
    """
    获取所有分类的标准配置
    
    Returns:
        JSON: 所有分类的标准配置数据
    """
    try:
        result = EvaluationStandardConfigService.get_all_category_standards()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取标准配置失败: {str(e)}'
        }), 500

@evaluation_standard_config_bp.route('/standard-config/<category>', methods=['POST'])
def save_category_standards(category):
    """
    保存指定分类的标准配置
    
    Args:
        category (str): 二级分类名称
    
    Request Body:
        {
            "dimension_ids": [1, 2, 3]  # 选择的维度ID列表
        }
    
    Returns:
        JSON: 保存结果
    """
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
        
        result = EvaluationStandardConfigService.save_category_standards(
            category, dimension_ids
        )
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存标准配置失败: {str(e)}'
        }), 500

@evaluation_standard_config_bp.route('/evaluation-template/<category>', methods=['GET'])
def get_evaluation_template(category):
    """
    获取指定分类的评估模板（用于评估中心）
    
    Args:
        category (str): 二级分类名称
    
    Returns:
        JSON: 格式化后的评估模板数据
    """
    try:
        result = EvaluationStandardConfigService.format_for_evaluation_template(category)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取评估模板失败: {str(e)}'
        }), 500 