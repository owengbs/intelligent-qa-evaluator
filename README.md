# 智能问答质量评估系统

一个基于大语言模型的自动化问答质量评估系统，支持多维度评分、自定义评估标准和时间因素考虑。

## 🎯 主要功能

### 核心评估功能
- **多维度评分**: 支持准确性、完整性、流畅性、安全性等维度评估
- **自定义评估标准**: 可自定义评估维度、要求和评分规则
- **时间因素考虑**: 基于问题提出时间进行时效性评估
- **智能变量替换**: 支持多种变量名变体，容错性强

### 用户界面
- **现代化UI**: 基于Ant Design的响应式界面
- **实时验证**: Prompt变量实时验证和提示
- **快速操作**: 一键插入变量、历史记录查看
- **进度显示**: 详细的评估进度和时间预估

### 技术特性
- **高可靠性**: 完善的错误处理和超时机制
- **灵活集成**: 支持自定义LLM API接入
- **详细日志**: 完整的操作日志和性能监控
- **状态管理**: 基于Redux的前端状态管理

## 🏗️ 系统架构

```
intelligent-qa-evaluator/
├── frontend/           # React前端应用
│   ├── src/
│   │   ├── components/ # UI组件
│   │   ├── store/      # Redux状态管理
│   │   └── utils/      # 工具函数
│   └── package.json
├── backend/            # Python Flask后端
│   ├── services/       # 业务逻辑服务
│   ├── utils/          # 工具模块
│   ├── app.py         # 主应用文件
│   └── requirements.txt
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
pip install -r requirements.txt
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
```

## 📊 使用方法

### 1. 基本评估流程

1. **填写用户输入**: 输入待评估的原始问题
2. **设置问题时间**: 选择问题提出的具体时间
3. **输入评估标准**: 定义详细的评分维度和标准
4. **提供参考答案**: 输入标准的参考答案
5. **输入模型回答**: 输入待评估的模型回答
6. **配置评分规则**: 使用或修改Prompt模板
7. **开始评估**: 点击评估按钮获取结果

### 2. 自定义评估标准格式

```
维度名称	具体要求描述	评分标准
准确性	数据与事实完全一致	0-4分：完全正确=4分；轻微误差=2分；重大错误=0分
完整性	覆盖所有关键信息点	0-3分：完全覆盖=3分；部分覆盖=1分；未覆盖=0分
```

### 3. 支持的变量

- `{user_input}` / `{user_query}` - 用户原始问题
- `{model_answer}` / `{model_response}` - 模型回答
- `{reference_answer}` / `{reference}` - 参考答案
- `{question_time}` / `{time}` - 问题提出时间
- `{evaluation_criteria}` / `{criteria}` - 评估标准

## 🔧 技术栈

### 前端
- **React 18**: 现代化用户界面
- **Ant Design 5**: 企业级UI组件库
- **Redux Toolkit**: 状态管理
- **Axios**: HTTP客户端
- **Day.js**: 时间处理

### 后端
- **Flask**: 轻量级Web框架
- **Winston风格日志**: 结构化日志系统
- **自定义LLM客户端**: 支持多种LLM API
- **CORS支持**: 跨域请求处理

## 📈 性能特点

- **智能超时处理**: 前端180秒，后端60秒超时设置
- **实时进度显示**: 30-120秒评估时间预估
- **错误容错**: 完善的异常处理和用户提示
- **响应式设计**: 适配各种设备屏幕

## 🛡️ 安全考虑

- **输入验证**: 严格的表单验证和数据校验
- **错误隔离**: 安全的错误信息展示
- **API安全**: 支持API密钥认证
- **数据保护**: 敏感信息不记录到日志

## 🔄 版本历史

### v1.2.0 (当前版本)
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

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请创建Issue或联系项目维护者。

---

*构建智能、可靠、易用的问答质量评估系统* 🚀 