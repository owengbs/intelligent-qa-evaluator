#!/usr/bin/env python3
"""
评估维度管理API路由
"""

from flask import Blueprint, request, jsonify
from services.evaluation_dimension_service import EvaluationDimensionService, CategoryDimensionService

evaluation_dimension_bp = Blueprint('evaluation_dimension', __name__)


@evaluation_dimension_bp.route('/api/dimensions', methods=['GET'])
def get_dimensions():
    """获取评估维度列表"""
    try:
        layer = request.args.get('layer')
        category = request.args.get('category')
        is_active = request.args.get('is_active')
        
        # 处理is_active参数
        if is_active is not None:
            is_active = is_active.lower() == 'true'
        
        dimensions = EvaluationDimensionService.get_all_dimensions(
            layer=layer, 
            category=category, 
            is_active=is_active
        )
        
        return jsonify({
            'success': True,
            'data': dimensions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取维度列表失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/dimensions/grouped', methods=['GET'])
def get_dimensions_grouped():
    """按层次分组获取维度"""
    try:
        grouped_dimensions = EvaluationDimensionService.get_dimensions_by_layer()
        return jsonify({
            'success': True,
            'data': grouped_dimensions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取分组维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/dimensions/<int:dimension_id>', methods=['GET'])
def get_dimension(dimension_id):
    """获取单个评估维度"""
    try:
        dimension = EvaluationDimensionService.get_dimension_by_id(dimension_id)
        if not dimension:
            return jsonify({
                'success': False,
                'message': '维度不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': dimension
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/dimensions', methods=['POST'])
def create_dimension():
    """创建新的评估维度"""
    try:
        data = request.get_json()
        
        # 验证必要字段
        required_fields = ['name', 'layer']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        dimension = EvaluationDimensionService.create_dimension(data)
        
        return jsonify({
            'success': True,
            'data': dimension,
            'message': '维度创建成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'创建维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/dimensions/<int:dimension_id>', methods=['PUT'])
def update_dimension(dimension_id):
    """更新评估维度"""
    try:
        data = request.get_json()
        dimension = EvaluationDimensionService.update_dimension(dimension_id, data)
        
        if not dimension:
            return jsonify({
                'success': False,
                'message': '维度不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': dimension,
            'message': '维度更新成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/dimensions/<int:dimension_id>', methods=['DELETE'])
def delete_dimension(dimension_id):
    """删除评估维度"""
    try:
        success = EvaluationDimensionService.delete_dimension(dimension_id)
        
        if not success:
            return jsonify({
                'success': False,
                'message': '维度不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '维度删除成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除维度失败: {str(e)}'
        }), 500


# 分类与维度关联管理
@evaluation_dimension_bp.route('/api/categories/<level2_category>/dimensions', methods=['GET'])
def get_category_dimensions(level2_category):
    """获取某个分类关联的维度"""
    try:
        dimensions = CategoryDimensionService.get_category_dimensions(level2_category)
        return jsonify({
            'success': True,
            'data': dimensions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取分类维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/categories/<level2_category>/dimensions', methods=['POST'])
def set_category_dimensions(level2_category):
    """设置某个分类关联的维度"""
    try:
        data = request.get_json()
        dimension_ids = data.get('dimension_ids', [])
        
        success = CategoryDimensionService.set_category_dimensions(level2_category, dimension_ids)
        
        return jsonify({
            'success': success,
            'message': '分类维度设置成功' if success else '设置失败'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'设置分类维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/categories/<level2_category>/dimensions/<int:dimension_id>', methods=['POST'])
def add_category_dimension(level2_category, dimension_id):
    """为某个分类添加维度"""
    try:
        data = request.get_json() or {}
        weight = data.get('weight', 1.0)
        
        mapping = CategoryDimensionService.add_category_dimension(level2_category, dimension_id, weight)
        
        return jsonify({
            'success': True,
            'data': mapping,
            'message': '维度添加成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'添加维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/categories/<level2_category>/dimensions/<int:dimension_id>', methods=['DELETE'])
def remove_category_dimension(level2_category, dimension_id):
    """移除某个分类的维度关联"""
    try:
        success = CategoryDimensionService.remove_category_dimension(level2_category, dimension_id)
        
        return jsonify({
            'success': success,
            'message': '维度移除成功' if success else '维度不存在'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'移除维度失败: {str(e)}'
        }), 500


@evaluation_dimension_bp.route('/api/categories/dimensions/mappings', methods=['GET'])
def get_all_category_mappings():
    """获取所有分类与维度的关联关系"""
    try:
        mappings = CategoryDimensionService.get_all_category_mappings()
        return jsonify({
            'success': True,
            'data': mappings
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取关联关系失败: {str(e)}'
        }), 500 