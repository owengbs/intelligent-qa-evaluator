# 问AI评估系统

一个基于大语言模型的自动化问答质量评估系统，支持多维度评分、智能分类、自定义评估标准、SQLite持久化存储和时间因素考虑。

## ✨ 最新更新 (v2.1.0)

### 🎨 UI/UX 优化
- **简化页面设计**: 移除冗余的页面标题和描述，界面更加简洁
- **品牌统一**: 系统名称统一为"问AI评估系统"
- **现代化界面**: 采用渐变色设计，提升视觉体验
- **代码质量提升**: 修复所有ESLint警告，优化React Hook使用
- **防抖优化**: 改进智能分类的防抖机制，提升用户体验

### 🔧 技术改进
- **React优化**: 修复useEffect和useCallback的依赖问题
- **代码清理**: 移除未使用的组件和函数，精简代码结构
- **ESLint规范**: 达到更高的代码质量标准
- **性能优化**: 改进组件渲染和状态管理效率

## 🎯 主要功能

### 核心评估功能
- **多维度评分**: 支持准确性、完整性、流畅性、安全性等维度评估
- **智能分类系统**: 自动问题分类和评估历史追踪
- **自定义评估标准**: 可自定义评估维度、要求和评分规则
- **时间因素考虑**: 基于问题提出时间进行时效性评估
- **智能变量替换**: 支持多种变量名变体，容错性强

### 数据持久化
- **SQLite数据库**: 轻量级本地数据库，无需额外配置
- **分类标准管理**: 19种预设分类标准覆盖股票分析全流程
- **评估历史记录**: 完整的评估历史和分类追踪
- **用户自定义配置**: 支持创建、修改、删除自定义分类标准

### 用户界面
- **现代化UI**: 基于Ant Design的响应式界面
- **分类配置管理**: 可视化分类标准配置界面
- **实时验证**: Prompt变量实时验证和提示
- **快速操作**: 一键插入变量、历史记录查看
- **进度显示**: 详细的评估进度和时间预估

### 技术特性
- **高可靠性**: 完善的错误处理和超时机制
- **灵活集成**: 支持自定义LLM API接入
- **详细日志**: 完整的操作日志和性能监控
- **状态管理**: 基于Redux的前端状态管理
- **数据安全**: 自动备份和数据完整性检查

## 🏗️ 系统架构

```
intelligent-qa-evaluator/
├── frontend/           # React前端应用
│   ├── src/
│   │   ├── components/ # UI组件
│   │   │   ├── ClassificationConfig.js  # 分类配置组件
│   │   │   └── EvaluationForm.js        # 评估表单组件
│   │   ├── store/      # Redux状态管理
│   │   └── utils/      # 工具函数
│   └── package.json
├── backend/            # Python Flask后端
│   ├── models/         # 数据模型
│   │   └── classification.py   # 分类标准和历史模型
│   ├── services/       # 业务逻辑服务
│   │   ├── classification_service_sqlite.py  # SQLite分类服务
│   │   └── evaluation_service.py             # 评估服务
│   ├── database/       # 数据库相关
│   │   └── init_db.py  # 数据库初始化
│   ├── utils/          # 工具模块
│   ├── config.py       # 配置文件
│   ├── app.py         # 主应用文件
│   ├── requirements.txt
│   └── qa_evaluator.db # SQLite数据库文件（自动生成）
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+
- npm/yarn

### 后端部署

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖（包含SQLAlchemy等新依赖）
pip install -r requirements.txt

# 启动应用（会自动初始化SQLite数据库）
python app.py
```

后端服务将运行在 `http://localhost:5001`

### 前端部署

```bash
cd frontend
npm install
npm start
```

前端应用将运行在 `http://localhost:3000`

### 环境配置

在 `backend/.env` 文件中配置：

```env
LLM_API_URL=your_llm_api_url
LLM_API_KEY=your_api_key
LLM_MODEL_NAME=your_model_name

# 数据库配置（可选，默认使用SQLite）
DATABASE_URL=sqlite:///qa_evaluator.db
SQLALCHEMY_TRACK_MODIFICATIONS=False
```

## 📊 使用方法

### 1. 分类标准配置

1. **访问分类配置**: 点击"分类配置"标签页
2. **查看预设标准**: 系统预设19种分类标准，覆盖股票分析全流程：
   - 股票选择类：基础面分析、技术分析等
   - 分析决策类：风险评估、投资策略等
   - 信息查询类：市场数据、财务信息等
3. **自定义标准**: 
   - 添加新的分类标准
   - 编辑现有标准（非默认标准）
   - 删除用户自定义标准
4. **导入导出**: 支持批量导入标准配置

### 2. 智能评估流程

1. **填写用户输入**: 输入待评估的原始问题
2. **自动分类**: 系统自动识别问题类型并记录
3. **设置问题时间**: 选择问题提出的具体时间
4. **输入评估标准**: 定义详细的评分维度和标准
5. **提供参考答案**: 输入标准的参考答案
6. **输入模型回答**: 输入待评估的模型回答
7. **配置评分规则**: 使用或修改Prompt模板
8. **开始评估**: 点击评估按钮获取结果和分类记录

### 3. 自定义评估标准格式

```
维度名称	具体要求描述	评分标准
准确性	数据与事实完全一致	0-4分：完全正确=4分；轻微误差=2分；重大错误=0分
完整性	覆盖所有关键信息点	0-3分：完全覆盖=3分；部分覆盖=1分；未覆盖=0分
```

### 4. 支持的变量

- `{user_input}` / `{user_query}` - 用户原始问题
- `{model_answer}` / `{model_response}` - 模型回答
- `{reference_answer}` / `{reference}` - 参考答案
- `{question_time}` / `{time}` - 问题提出时间
- `{evaluation_criteria}` / `{criteria}` - 评估标准

## 🗄️ 数据库架构

### 分类标准表 (ClassificationStandard)
- **id**: 主键
- **level1**: 一级分类（如：股票选择）
- **level1_definition**: 一级分类定义
- **level2**: 二级分类（如：基本面分析）
- **level3**: 三级分类（如：财务分析）
- **level3_definition**: 三级分类详细定义
- **examples**: 问题示例
- **is_default**: 是否为系统默认标准
- **created_at/updated_at**: 时间戳

### 分类历史表 (ClassificationHistory)
- **id**: 主键
- **question**: 原始问题
- **classification_id**: 关联的分类标准ID
- **confidence**: 分类置信度
- **evaluation_result**: 评估结果
- **created_at**: 创建时间

## 🔧 技术栈

### 前端
- **React 18**: 现代化用户界面
- **Ant Design 5**: 企业级UI组件库
- **Redux Toolkit**: 状态管理
- **Axios**: HTTP客户端
- **Day.js**: 时间处理

### 后端
- **Flask**: 轻量级Web框架
- **SQLAlchemy**: ORM数据库操作
- **SQLite**: 轻量级关系数据库
- **Winston风格日志**: 结构化日志系统
- **自定义LLM客户端**: 支持多种LLM API
- **CORS支持**: 跨域请求处理

### 数据库
- **SQLite**: 本地文件数据库，零配置
- **SQLAlchemy ORM**: 面向对象的数据库操作
- **自动迁移**: 表结构自动创建和更新
- **数据完整性**: 外键约束和数据验证

## 📈 性能特点

- **智能超时处理**: 前端180秒，后端60秒超时设置
- **实时进度显示**: 30-120秒评估时间预估
- **错误容错**: 完善的异常处理和用户提示
- **响应式设计**: 适配各种设备屏幕
- **数据库优化**: 索引优化和查询缓存
- **自动分类**: 高效的问题类型识别算法

## 🛡️ 安全考虑

- **输入验证**: 严格的表单验证和数据校验
- **SQL注入防护**: 使用SQLAlchemy ORM参数化查询
- **错误隔离**: 安全的错误信息展示
- **API安全**: 支持API密钥认证
- **数据保护**: 敏感信息不记录到日志
- **数据备份**: 支持数据库备份和恢复

## 🔄 版本历史

### v2.1.0 (当前版本)
- ✅ **UI界面优化**：简化页面设计，移除冗余标题和描述
- ✅ **品牌统一**：系统名称统一为"问AI评估系统"
- ✅ **现代化设计**：采用渐变色和圆角设计，提升视觉体验
- ✅ **代码质量提升**：修复所有ESLint警告，优化React Hook使用
- ✅ **防抖机制优化**：改进智能分类的用户输入防抖处理
- ✅ **组件精简**：移除未使用的组件和函数，代码更加简洁
- ✅ **性能优化**：改进组件渲染效率和状态管理

### v2.0.0
- ✅ **新增SQLite持久化存储**：替换内存存储，数据永久保存
- ✅ **智能分类系统**：19种预设分类标准，自动问题分类
- ✅ **分类历史追踪**：完整的评估历史记录和分析
- ✅ **可视化配置管理**：图形化分类标准配置界面
- ✅ **数据库架构设计**：完整的ORM模型和数据关系
- ✅ **系统稳定性提升**：完善的错误处理和日志系统

### v1.2.0
- ✅ 新增自定义评估标准功能
- ✅ 支持时间参数评估
- ✅ 完善变量插入系统
- ✅ 优化用户界面和体验

### v1.1.0
- ✅ 添加时间因素考虑
- ✅ 修复React无限渲染问题
- ✅ 优化表单同步机制

### v1.0.0
- ✅ 基础评估功能
- ✅ 多维度评分系统
- ✅ 变量替换机制
- ✅ 历史记录功能

## 🚀 API 接口

### 分类标准管理
- `GET /api/classification-standards` - 获取所有分类标准
- `POST /api/classification-standards` - 批量更新分类标准
- `POST /api/classification-standards/single` - 创建单个分类标准
- `PUT /api/classification-standards/<id>` - 更新指定分类标准
- `DELETE /api/classification-standards/<id>` - 删除指定分类标准

### 分类历史
- `GET /api/classification-history` - 获取分类历史记录
- `POST /api/classification-history` - 创建分类历史记录

### 评估服务
- `POST /api/evaluate` - 执行问答质量评估

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置
1. Fork项目仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 安装开发依赖：`pip install -r requirements.txt`
4. 运行测试：`python -m pytest`
5. 提交更改：`git commit -am 'Add some feature'`
6. 推送分支：`git push origin feature/your-feature`
7. 创建Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请创建Issue或联系项目维护者。

---

*构建智能、可靠、易用的问答质量评估系统* 🚀 