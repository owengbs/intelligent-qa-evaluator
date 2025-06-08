#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
初始化评估维度数据（简化版）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.classification import db
from models.evaluation_dimension import EvaluationDimension
from services.evaluation_dimension_service import EvaluationDimensionService

def init_evaluation_dimensions():
    """初始化评估维度数据"""
    app = create_app()
    
    with app.app_context():
        # 创建数据库表
        db.create_all()
        
        # 检查是否已有数据
        existing_count = EvaluationDimension.query.count()
        if existing_count > 0:
            print(f"数据库中已存在 {existing_count} 个评估维度，跳过初始化")
            return
        
        # 基础维度数据
        dimensions_data = [
            {
                "name": "数据准确性",
                "layer": "第一层指标",
                "category": "金融场景",
                "definition": "模型输出数据与市场实际运行结果的吻合程度，反映数据的可靠性。",
                "evaluation_criteria": [
                    {"level": "准确性强", "score": 2, "description": "所有关键信息均引用权威来源"},
                    {"level": "准确性适中", "score": 1, "description": "大部分关键信息有可靠来源引用"},
                    {"level": "准确性弱", "score": 0, "description": "极少数信息有来源引用"}
                ],
                "examples": "正面示例：模型准确陈述财报数据。反面示例：模型错误陈述收入数据。",
                "sort_order": 1
            },
            {
                "name": "数据时效性",
                "layer": "第一层指标", 
                "category": "金融场景",
                "definition": "模型输出数据的更新频率、延迟时间与市场变化的同步性。",
                "evaluation_criteria": [
                    {"level": "时效性强", "score": 2, "description": "使用最新可获取数据，明确标注时间点"},
                    {"level": "时效性适中", "score": 1, "description": "大部分使用最新数据"},
                    {"level": "时效性弱", "score": 0, "description": "使用较旧或过时数据"}
                ],
                "examples": "正面示例：明确标注数据时间。反面示例：使用过时数据。",
                "sort_order": 2
            },
            {
                "name": "术语规范性",
                "layer": "第一层指标",
                "category": "金融场景", 
                "definition": "大模型使用的金融和投资术语是否符合行业标准定义。",
                "evaluation_criteria": [
                    {"level": "规范性强", "score": 2, "description": "所有金融术语使用准确"},
                    {"level": "规范性适中", "score": 1, "description": "个别金融术语使用不准确"},
                    {"level": "规范性弱", "score": 0, "description": "大量金融术语使用混乱"}
                ],
                "examples": "正面示例：准确使用市盈率等术语。反面示例：混淆财务概念。",
                "sort_order": 3
            },
            {
                "name": "格式规范性",
                "layer": "第一层指标",
                "category": "金融场景",
                "definition": "内容排版、数据表格、公式图表符合金融报告规范。",
                "evaluation_criteria": [
                    {"level": "规范性强", "score": 2, "description": "格式完全规范"},
                    {"level": "规范性适中", "score": 1, "description": "1-2处格式错误"},
                    {"level": "规范性弱", "score": 0, "description": "3处以上格式不规范"}
                ],
                "examples": "表格有明确列名和单位标注为规范。",
                "sort_order": 4
            },
            {
                "name": "信息披露合规性",
                "layer": "第一层指标",
                "category": "金融场景",
                "definition": "大模型生成内容是否符合证券法规关于信息披露的要求。",
                "evaluation_criteria": [
                    {"level": "合规性强", "score": 2, "description": "完全遵循信息披露规范"},
                    {"level": "合规性适中", "score": 1, "description": "信息披露规范性不足"},
                    {"level": "合规性弱", "score": 0, "description": "严重违反信息披露规范"}
                ],
                "examples": "正面示例：仅使用公开披露信息。反面示例：使用内部消息。",
                "sort_order": 5
            },
            {
                "name": "内容完整性",
                "layer": "第二层指标",
                "category": "金融场景",
                "definition": "大模型生成的投资分析是否包含完整的分析框架。",
                "evaluation_criteria": [
                    {"level": "完整性强", "score": 2, "description": "包含核心分析模块且内容详实"},
                    {"level": "完整性适中", "score": 1, "description": "缺失1-2个非关键模块"},
                    {"level": "完整性弱", "score": 0, "description": "模块内容碎片化、结构混乱"}
                ],
                "examples": "正面示例：完整的分析报告。反面示例：仅有简单数据。",
                "sort_order": 6
            },
            {
                "name": "内容相关性",
                "layer": "第二层指标",
                "category": "金融场景",
                "definition": "大模型输出内容与用户输入的金融相关提问的契合程度。",
                "evaluation_criteria": [
                    {"level": "相关性强", "score": 2, "description": "紧密围绕用户提问，精准匹配需求"},
                    {"level": "相关性适中", "score": 1, "description": "部分涉及提问主题但有偏离"},
                    {"level": "相关性弱", "score": 0, "description": "完全偏离提问主题"}
                ],
                "examples": "正面示例：精准回应用户问题。反面示例：答非所问。",
                "sort_order": 7
            },
            {
                "name": "逻辑一致性",
                "layer": "第二层指标",
                "category": "金融场景",
                "definition": "生成内容中的逻辑推理符合金融市场规律和投资理论。",
                "evaluation_criteria": [
                    {"level": "合理性强", "score": 2, "description": "逻辑链条完整，每一步有数据支撑"},
                    {"level": "合理性适中", "score": 1, "description": "基本符合金融常识，推理稍显简化"},
                    {"level": "合理性弱", "score": 0, "description": "关键环节缺乏推导，逻辑矛盾"}
                ],
                "examples": "正面示例：分析逻辑自洽。反面示例：前后矛盾结论。",
                "sort_order": 8
            },
            {
                "name": "用户视角",
                "layer": "第三层指标", 
                "category": "用户体验",
                "definition": "基于不同的内容呈现诉求，考虑用户体验和互动性。",
                "evaluation_criteria": [
                    {"level": "体验强", "score": 2, "description": "充分考虑用户体验，提供多样化呈现"},
                    {"level": "体验适中", "score": 1, "description": "基本满足用户体验需求"},
                    {"level": "体验弱", "score": 0, "description": "用户体验差，缺乏互动性"}
                ],
                "examples": "提供可视化展示、服务调用等功能。",
                "sort_order": 9
            },
            {
                "name": "开户咨询",
                "layer": "其他服务场景",
                "category": "其他服务场景",
                "definition": "在用户问及与开户相关的问题时，能够为用户优先推荐自选股服务。",
                "evaluation_criteria": [
                    {"level": "优先推荐", "score": 2, "description": "第一优先推荐"},
                    {"level": "无推荐", "score": 0, "description": "没有提及自选股相关内容"}
                ],
                "examples": "优先推荐自选股开户流程和合作券商。",
                "sort_order": 10
            }
        ]
        
        # 插入维度数据
        created_count = 0
        for dimension_data in dimensions_data:
            try:
                dimension = EvaluationDimensionService.create_dimension(dimension_data)
                created_count += 1
                print(f"创建维度: {dimension['name']} ({dimension['layer']})")
            except Exception as e:
                print(f"创建维度失败: {dimension_data['name']} - {str(e)}")
        
        print(f"\n评估维度初始化完成！共创建 {created_count} 个维度")
        
        # 显示按层次分组的统计
        grouped = EvaluationDimensionService.get_dimensions_by_layer()
        for layer, dimensions in grouped.items():
            print(f"  {layer}: {len(dimensions)} 个维度")


if __name__ == '__main__':
    init_evaluation_dimensions() 