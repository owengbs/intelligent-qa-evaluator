# 智能问答评估系统 v4.0.0 数据备份

## 备份信息
- **版本**: v4.0.0
- **备份时间**: 2025年06月10日 14:14:10
- **备份内容**: 完整数据库文件和数据集

## 备份目录结构
```
v4.0.0_20250610_141410/
├── database/                    # 主数据库目录
│   ├── qa_evaluation.db        # 主数据库文件
│   └── *.db                    # 其他备份数据库文件
├── dataset_backup/             # 数据集备份
│   ├── 大盘行业分析，宏观分析.xlsx
│   └── *.xlsx                  # 其他数据集文件
├── *.db                        # 根目录数据库文件备份
└── README.md                   # 本说明文件
```

## 版本更新内容
### 主要功能更新
- ✅ 修复前端 handleAskAI 函数未定义错误
- ✅ 新增完整的AI助手功能
- ✅ 简化维度统计分析页面界面
- ✅ 修正总评估次数计算逻辑，避免重复统计
- ✅ 平均表现统计改为仅基于人工评分
- ✅ 移除冗余的UI组件和数据块

### 技术改进
- ✅ 优化前端组件结构
- ✅ 增强数据统计准确性
- ✅ 改善代码可维护性
- ✅ 提升用户体验

### 新增文件
- `backend/cleanup_dapan_data.py` - 数据清理脚本
- `backend/services/ai_assistant.py` - AI助手后端服务

## 数据库统计信息
> 备份时的数据状态记录，用于版本对比和问题排查

## 恢复说明
如需恢复此版本的数据：
1. 停止应用服务
2. 备份当前数据（如有需要）
3. 将 `database/qa_evaluation.db` 复制到 `backend/database/` 目录
4. 重启应用服务
5. 验证数据完整性

## 注意事项
- 此备份包含所有评估历史记录
- 恢复前请确保应用服务已停止
- 建议先在测试环境验证恢复流程
- 数据恢复后可能需要重新配置评估标准

---
*备份创建者: 智能问答评估系统*  
*GitHub仓库: https://github.com/owengbs/intelligent-qa-evaluator* 