# 问AI评估系统 v2.3.1

智能问答评估系统，基于大语言模型的自动化评估平台，支持多维度评分、智能分类识别、历史记录管理、统计分析、人工评估修正和配置数据全量同步。

## 🚀 最新功能特性 (v2.3.1)

### 🔄 配置数据全量同步系统 ⭐ 新增
- **全量导出导入**：支持完整的配置数据导出和全量替换导入
- **团队协作支持**：解决多人协作时配置数据不一致的问题
- **远端部署优化**：提供快速数据库初始化和部署检查工具
- **数据安全保障**：自动备份机制，确保配置数据安全
- **版本控制集成**：配置数据通过JSON文件进行版本控制

### 🛠️ 新增工具和脚本
- **📤 全量配置导出**：`backend/scripts/export_config_data.py`
- **📥 全量/增量导入**：`backend/scripts/import_config_data.py --full-replace`
- **🚀 快速数据库初始化**：`backend/quick_init.py`
- **🔍 部署状态检查**：`backend/check_deployment.py`
- **📋 完整部署指南**：`DEPLOYMENT_GUIDE.md`

### 📊 解决的核心问题
- ❌ **增量导入问题**：原有只能新增配置，无法删除或修改已有配置
- ❌ **团队不一致**：不同环境的配置数据可能不同步
- ❌ **远端数据库为空**：新部署环境缺少基础配置数据
- ✅ **全量同步**：完全替换现有配置，确保团队配置一致
- ✅ **智能初始化**：自动检测并初始化数据库
- ✅ **部署检查**：验证环境配置正确性

### 1. 人工评估系统 👨‍💼
- **AI+人工双重评估**：在AI评估基础上支持专家人工修正和补充
- **评估修正功能**：可对AI评估的总分和各维度分数进行调整
- **专业意见记录**：支持输入详细的人工评估意见和修正理由
- **评估者追溯**：记录评估者姓名和评估时间，确保评估责任可追溯
- **对比展示**：清晰展示AI评估与人工评估的差异对比
- **评估状态标识**：明确区分仅AI评估和已人工评估的记录

### 2. 历史管理增强
- **人工评估状态**：历史记录表格新增人工评估状态列
- **详情对比展示**：评估详情页面展示AI与人工评估的完整对比
- **差异分析**：自动计算并高亮显示评分差异
- **意见展示**：专门区域展示人工评估意见和修正理由

### 3. 用户体验优化
- **一键修正**：基于AI评估结果快速进行人工调整
- **表单预填充**：人工评估表单自动填入AI评估结果作为初始值
- **实时验证**：表单验证确保评分在合理范围内，修复输入组件验证问题
- **视觉差异化**：用不同颜色和图标(🤖/👨‍💼)区分AI和人工评估

## 🔄 配置数据同步工作流

### 配置更新者（产品经理/配置管理员）
```bash
# 1. 在系统中更新配置标准
# 2. 导出最新配置
cd backend/scripts
python export_config_data.py

# 3. 提交到版本控制
git add config_data/
git commit -m "feat: 更新评估标准配置（全量）"
git push
```

### 配置使用者（开发人员/测试人员）
```bash
# 1. 拉取最新代码
git pull

# 2. 全量同步配置
cd backend/scripts
python import_config_data.py --full-replace

# 3. 重启应用
```

### 远端部署流程
```bash
# 1. 克隆项目
git clone <project-url>
cd intelligent-qa-evaluator

# 2. 后端初始化
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 快速数据库初始化
python quick_init.py

# 4. 导入团队配置（可选）
cd scripts
python import_config_data.py --full-replace

# 5. 验证部署
cd ..
python check_deployment.py

# 6. 启动服务
python app.py
```

## 📋 系统功能

### 核心功能
- **智能评估**：基于DeepSeek等大语言模型的自动化评估
- **人工评估**：专家可对AI评估结果进行修正和补充 ⭐ v2.3.0
- **配置同步**：支持配置数据的全量同步和团队协作 ⭐ v2.3.1
- **多维度评分**：支持准确性、完整性、流畅性、安全性等多个维度
- **智能分类**：自动识别问题类型并应用对应的评估标准
- **时间因素**：考虑问题提出时间对答案时效性的影响
- **标准配置**：支持自定义分类标准和评估标准

### 配置同步特性 ⭐ 新增
- **全量替换模式**：完全替换现有配置，确保团队配置一致
- **增量导入模式**：只导入不存在的配置，保留现有数据
- **自动备份机制**：全量替换前自动备份现有配置
- **版本控制集成**：配置数据通过JSON文件进行版本控制
- **部署验证工具**：检查环境配置是否正确完整

### 评估流程优化
- **AI初评**：系统首先进行严格的AI评估
- **人工复审**：专家可选择性地对AI评估进行修正 ⭐ v2.3.0
- **结果对比**：同时展示AI评估和人工评估结果 ⭐ v2.3.0
- **意见记录**：详细记录人工评估的理由和修正依据 ⭐ v2.3.0
- **配置管理**：支持配置标准的团队协作和版本控制 ⭐ v2.3.1

### 2.3.0 功能特性
- **人机协作评估**：结合AI的客观性和人工的专业性 ⭐ 核心功能
- **评估追溯体系**：完整的评估者信息和时间记录
- **差异分析展示**：智能对比AI与人工评估的差异
- **评估状态管理**：清晰的评估状态标识和过滤

### 历史功能保持
- **历史管理**：完整的评估历史记录管理系统
- **统计分析**：基于历史数据的维度统计和分析
- **数据可视化**：直观的图表和进度条展示
- **筛选搜索**：支持按分类、时间等条件筛选历史记录

### 2.2.0 严格评分系统
- **严格评分系统**：全面提升评分的严格程度和准确性
- **分类专门标准**：针对不同问题类型的专门化严格评估标准
- **扣分理由强制**：必须明确说明每个扣分点和改进方向
- **评分指导可视化**：用户界面直观展示评分标准和指导原则

## 🛠️ 技术架构

### 前端技术栈
- **React 18**：现代化的前端框架
- **Redux Toolkit**：状态管理
- **Ant Design**：UI组件库
- **React Router**：路由管理
- **Axios**：HTTP客户端
- **Day.js**：日期处理

### 后端技术栈
- **Flask**：轻量级Web框架
- **SQLAlchemy**：ORM数据库操作
- **SQLite**：轻量级数据库
- **Python Logging**：日志记录系统

### 数据库设计
- **evaluation_history**：评估历史记录表（新增人工评估字段）
- **classification_standards**：分类标准表
- **evaluation_standards**：评估标准表

#### 人工评估字段扩展
```sql
-- 新增字段
human_total_score INTEGER,           -- 人工评估总分
human_dimensions_json TEXT,          -- 人工评估各维度分数
human_reasoning TEXT,                -- 人工评估理由
human_evaluation_by TEXT,            -- 评估者姓名
human_evaluation_time TIMESTAMP,     -- 人工评估时间
is_human_modified BOOLEAN DEFAULT FALSE  -- 是否已人工修正
```

## 📦 安装和运行

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 后端安装
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# 运行数据库迁移（添加人工评估字段）
python init_db.py
python app.py
```

### 前端安装
```bash
cd frontend
npm install
npm start
```

### 环境配置
创建 `backend/.env` 文件：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

## 🎯 使用指南

### 1. 评估中心（AI评估）
- 输入用户问题、模型回答和参考答案
- 选择或自动识别问题分类
- 配置评估标准和维度
- 点击评估获取多维度评分结果
- **新增**：评估完成后可点击"人工评估"按钮进行专家修正

### 2. 人工评估流程 ⭐ 新功能
1. **触发人工评估**：在AI评估结果卡片点击"人工评估"按钮
2. **调整评分**：基于AI评估结果进行分数调整
   - 总分可在0-10范围内调整
   - 各维度分数可根据维度最大值调整
3. **输入理由**：详细说明修正理由和专业意见
4. **填写评估者**：输入评估者姓名便于追溯
5. **保存修正**：保存人工评估结果，系统自动记录时间

### 3. 历史管理（增强版）
- 查看所有历史评估记录，新增"人工评估"状态列
- 按分类、时间、是否人工评估筛选记录
- 查看详细的评估结果，支持AI vs 人工对比展示
- **对比功能**：详情页面清晰展示AI评估与人工评估的差异
  - 🤖 AI评估结果
  - 👨‍💼 人工评估结果（如有）
  - 📊 评分差异分析

### 4. 维度统计
- 查看总体统计概览（包含人工评估数据）
- 按分类查看维度表现
- 分析各维度的得分分布
- 对比不同分类的表现

## 📊 数据流程

### 人工评估流程（新增）
1. **AI基础评估**：系统首先完成AI评估
2. **人工复审触发**：专家点击"人工评估"按钮
3. **评分调整**：基于专业判断调整AI评分
4. **理由记录**：输入详细的修正理由
5. **数据保存**：保存人工评估结果，标记为已修正
6. **对比展示**：系统展示AI vs 人工评估对比

### 评估数据结构
```json
{
  "ai_evaluation": {
    "total_score": 7.5,
    "dimensions": {"准确性": 3, "完整性": 2, "流畅性": 2.5},
    "reasoning": "AI评估理由..."
  },
  "human_evaluation": {
    "total_score": 8.0,
    "dimensions": {"准确性": 4, "完整性": 2, "流畅性": 2.0},
    "reasoning": "基于行业经验，准确性表现更好，但流畅性有待改进...",
    "evaluator": "张专家",
    "evaluation_time": "2025-06-03 10:30:00"
  }
}
```

## 🔧 配置说明

### API接口更新
```bash
# 新增人工评估接口
PUT /api/evaluation-history/{history_id}/human-evaluation
Content-Type: application/json

{
  "human_total_score": 8.0,
  "human_dimensions": {"准确性": 4, "完整性": 2, "流畅性": 2.0},
  "human_reasoning": "专家评估意见...",
  "human_evaluation_by": "评估者姓名"
}
```

### 严格评分标准 (保持v2.2.0标准)
- **8-10分**：仅给予信息完全准确、分析深入、表达清晰的优秀回答
- **5-7分**：基本合格但存在明显不足的回答
- **2-4分**：存在错误或质量较低的回答
- **0-1分**：严重错误或完全不合格的回答

## 📈 版本历史

### v2.3.1 (2025-06-03) - 配置数据全量同步版本
- 🔄 **配置数据全量同步系统**：完美解决团队协作配置不一致问题
- ✨ 新增全量导出脚本：`backend/scripts/export_config_data.py`
- ✨ 新增全量/增量导入脚本：`backend/scripts/import_config_data.py --full-replace`
- ✨ 新增快速数据库初始化：`backend/quick_init.py` 解决远端部署数据库为空问题
- ✨ 新增部署状态检查：`backend/check_deployment.py` 验证环境配置
- ✨ 配置数据版本控制：通过JSON文件实现配置的版本管理
- ✨ 自动备份机制：全量替换前自动备份现有配置数据
- ✨ 团队协作工作流：配置更新者导出→提交→推送，使用者拉取→导入→同步
- 📋 完整部署指南：`DEPLOYMENT_GUIDE.md` 和 `CONFIG_SYNC_GUIDE.md`
- 📋 功能总结文档：`README_CONFIG_SYNC.md` 详细说明解决方案
- 🛡️ 数据安全保障：配置数据与用户评估数据完全分离，确保隐私安全

### v2.3.0 (2025-06-03) - 人工评估版本
- 🎯 **人工评估系统**：支持专家对AI评估结果进行修正和补充
- ✨ 新增人工评估表单，支持调整总分、维度分数和添加专家意见
- ✨ 数据库扩展：添加人工评估相关字段（human_total_score等）
- ✨ 历史管理增强：新增人工评估状态列和详情对比展示
- ✨ AI vs 人工评估对比：清晰展示评估差异和修正理由
- 🐛 修复表单验证问题：InputNumber组件替换Input type="number"
- 🎨 视觉优化：用图标区分AI(🤖)和人工(👨‍💼)评估
- 🔧 API扩展：新增PUT /api/evaluation-history/{id}/human-evaluation接口

### v2.2.0 (2025-06-01)
- 🎯 **评估系统严格化**：全面提升评分的严格程度和准确性
- ✨ 新增分级评分指导原则（8-10优秀，5-7合格，2-4不足，0-1不合格）
- ✨ 评分理由必须明确说明扣分原因和改进方向
- ✨ 针对不同分类制定专门的严格评估标准
- ✨ 时效性判断更加严格，基于问题提出时间
- 🔧 前端集成严格评分prompt生成
- 🎨 优化评估结果展示，突出扣分理由

### v2.1.0 (2025-01-XX)
- ✨ 新增评估历史管理功能
- ✨ 新增维度统计分析功能
- ✨ 新增数据可视化展示
- 🐛 修复动态维度评分问题
- 🎨 优化用户界面和交互体验

### v2.0.0 (2025-01-XX)
- ✨ 实现动态维度评分
- ✨ 支持自定义评估标准
- ✨ 智能分类识别
- 🎨 全新的UI设计

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/HumanEvaluation`)
3. 提交更改 (`git commit -m 'Add human evaluation system'`)
4. 推送到分支 (`git push origin feature/HumanEvaluation`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的大语言模型API
- [Ant Design](https://ant.design/) - 优秀的React UI组件库
- [Flask](https://flask.palletsprojects.com/) - 简洁的Python Web框架

---

**Powered by React + Flask + DeepSeek LLM © 2025**
**支持AI+人工协作评估，配置数据全量同步，完美解决团队协作问题 🤖👨‍💼🔄**

## 📚 相关文档

- [`DEPLOYMENT_GUIDE.md`](backend/DEPLOYMENT_GUIDE.md) - 完整部署指南
- [`README_CONFIG_SYNC.md`](README_CONFIG_SYNC.md) - 配置同步解决方案总结
- [`CONFIG_SYNC_GUIDE.md`](backend/CONFIG_SYNC_GUIDE.md) - 详细使用指南

---

**配置同步解决方案亮点**：
- 🔄 **全量同步**：解决增量导入无法删除配置的问题
- 👥 **团队协作**：多人开发配置标准完全一致
- 🚀 **快速部署**：远端环境一键初始化
- 🛡️ **数据安全**：配置与用户数据分离，自动备份 