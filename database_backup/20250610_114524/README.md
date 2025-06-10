# 数据库备份说明

## 备份时间
- 备份日期：2025年06月10日 11:45:24
- 备份版本：竞态条件修复版本

## 备份内容

### 主要数据库
- `qa_evaluation.db` - 主数据库（最新版本，包含完整的评估记录和新导入的交易客服数据）
- `qa_evaluation_main.db` - 主数据库副本

### 历史备份
- `qa_evaluation_backup_20250608_113746.db` - 2025年06月08日备份
- `qa_evaluation_backup_20250608_193930.db` - 2025年06月08日备份  
- `qa_evaluation_backup_before_classification_20250608_114339.db` - 分类系统更新前备份
- `backup_before_field_fix.db` - 字段修复前备份

### 其他数据库
- `qa_evaluator_data.db` - data目录中的数据库
- `qa_evaluator_instance.db` - instance目录中的数据库
- `qa_evaluator.db` - 根目录中的数据库

### 空数据库（已清理）
- `app.db` - 应用数据库（空）
- `database.db` - 通用数据库（空）
- `evaluation_history.db` - 评估历史数据库（空）

## 重要修改记录

### 最新功能
1. **修复badcase跳转竞态条件问题**
   - 解决了URL参数分步更新导致的多重API调用
   - 添加防抖机制和请求取消机制
   
2. **外部页面跳转功能**
   - DimensionStatistics可正确跳转到外部badcase页面
   - 自动设置筛选条件（人工评估+对应分类）

3. **新数据导入**
   - 导入"交易客服.xlsx"数据（9条记录）
   - 新增"客服帮助及交易"分类
   - 映射到标准6维度评估体系

4. **动态分类管理**
   - 分类选项从数据库动态获取
   - 支持新导入分类的自动识别

### 数据统计（截至备份时）
- 总评估记录：149条
- Badcase记录：93条
- 分类数量：9个
- 人工评估覆盖率：100%

## 恢复说明
1. 使用 `qa_evaluation.db` 作为主数据库文件
2. 确保数据库路径：`backend/database/qa_evaluation.db`
3. 如需回滚，可使用相应的历史备份文件

## 技术改进
- 前端竞态条件修复
- API错误处理优化
- 请求取消机制
- 防抖和节流优化
- 资源清理机制 