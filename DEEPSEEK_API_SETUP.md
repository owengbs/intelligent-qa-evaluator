# DeepSeek API 配置说明

## 📋 功能介绍

AI总结功能使用DeepSeek V3大模型对各分类下的Badcase原因进行智能归纳总结，提供：

- 🎯 主要问题类型识别和分类
- 📊 问题频次统计和占比分析  
- 🔍 根本原因深度分析
- 💡 具体可行的改进建议
- 🚨 优先级排序和严重程度评估

## 🔑 API密钥配置

### 1. 获取DeepSeek API密钥

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册/登录账号
3. 进入控制台，创建API密钥
4. 复制生成的API密钥

### 2. 配置环境变量

#### 生产环境（推荐）

在服务器上设置环境变量：

```bash
# 临时设置（重启后失效）
export DEEPSEEK_API_KEY="your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.profile）
echo 'export DEEPSEEK_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 开发环境

创建 `.env` 文件（如果不存在）：

```bash
# 在项目根目录创建.env文件
cd /path/to/intelligent-qa-evaluator
echo 'DEEPSEEK_API_KEY=your-api-key-here' >> .env
```

#### Docker环境

在docker-compose.yml中添加环境变量：

```yaml
version: '3.8'
services:
  backend:
    # ... 其他配置
    environment:
      - DEEPSEEK_API_KEY=your-api-key-here
```

### 3. 验证配置

重启后端服务后，查看日志确认配置：

```bash
# 重启服务
cd backend
python app.py

# 如果配置正确，不会看到警告信息
# 如果未配置，会看到: "DEEPSEEK_API_KEY 环境变量未设置，AI总结功能将无法使用"
```

## 🚀 使用方法

1. **进入维度统计页面**
   - 导航到 "维度统计" 页面
   - 切换到 "Badcase分析" 标签页

2. **使用AI总结功能**
   - 在 "各分类Badcase统计" 区域
   - 点击任一分类下的 "AI总结" 按钮
   - 等待AI分析完成（通常需要10-30秒）

3. **查看总结结果**
   - 弹出的Modal窗口会显示详细的AI分析结果
   - 包含问题类型、根本原因、改进建议等

## 📊 输出格式说明

AI总结结果包含以下部分：

### 主要问题类型
- **类型名称**：问题的分类标签
- **描述**：问题的详细说明
- **频次**：出现次数统计
- **占比**：在总问题中的百分比
- **严重程度**：高/中/低级别

### 根本原因分析
- 识别导致问题的深层次原因
- 从系统性角度分析问题根源

### 改进建议
- **针对问题**：对应的具体问题
- **改进建议**：可执行的解决方案
- **优先级**：高/中/低优先级排序

## ⚠️ 注意事项

1. **API费用**：DeepSeek API按使用量计费，请合理使用
2. **网络要求**：需要服务器能访问DeepSeek API（api.deepseek.com）
3. **响应时间**：AI分析需要时间，请耐心等待
4. **数据要求**：需要该分类下有足够的Badcase记录才能获得有意义的总结

## 🔧 故障排除

### 常见错误及解决方案

#### 1. "DeepSeek API密钥未配置"
**解决方案**：按照上述步骤正确设置DEEPSEEK_API_KEY环境变量

#### 2. "API调用失败"
**可能原因**：
- API密钥无效或过期
- 网络连接问题
- API配额不足

**解决方案**：
- 检查API密钥是否正确
- 确认网络连接正常
- 检查DeepSeek账户余额

#### 3. "总结格式解析失败"
**说明**：AI返回的内容格式不标准，但仍会显示原始总结内容

#### 4. "没有badcase原因可供总结"
**解决方案**：确保该分类下有Badcase记录，且记录中包含原因说明

## 📞 技术支持

如遇问题，请：

1. 检查后端日志获取详细错误信息
2. 确认环境变量配置正确
3. 验证网络连接和API密钥状态
4. 联系系统管理员获取帮助

## 🔄 更新历史

- **v2.1.0** (2025-06-09): 首次引入AI总结功能
  - 支持DeepSeek V3模型
  - 多维度问题分析
  - 智能改进建议生成 