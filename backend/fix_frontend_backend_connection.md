# 前后端连接问题完整解决方案

## 🔍 问题诊断结果

### 现状分析
- **后端服务**：✅ 正常运行在端口7860
- **前端服务**：✅ 正常运行在端口8701  
- **环境配置**：✅ 前端配置正确的API地址 `http://9.135.87.101:7860/api`
- **CORS配置**：✅ 后端正确配置跨域请求
- **API接口**：⚠️ 大部分正常，缺少 `/api/health` 接口

### 根本原因
1. **后端缺少 `/api/health` 接口** - 已修复，需重启
2. **前端可能存在API调用逻辑问题** - 需要检查

## 🛠️ 解决步骤

### 步骤1：重启后端服务（必需）
```bash
cd /data/macxin/intelligent-qa-evaluator/backend

# 方法1：使用生产启动脚本（推荐）
bash start_production.sh

# 方法2：手动启动
export APP_ENV=production
python app.py
```

### 步骤2：验证后端修复
```bash
# 测试新增的API健康检查接口
curl http://9.135.87.101:7860/api/health

# 应该返回：
# {"api_status":"active","status":"healthy","timestamp":"...","version":"2.1.0"}
```

### 步骤3：测试完整API流程
```bash
# 运行API测试脚本
python test_frontend_api_call.py

# 应该显示所有测试通过
```

### 步骤4：检查前端是否需要重新构建
```bash
cd ../frontend

# 检查构建文件中的API地址
find build -name "*.js" -type f | head -1 | xargs grep -o "http://[^\"']*api"

# 如果API地址不正确，重新构建
REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build

# 如果前端服务需要重启
bash ../backend/start_frontend_production.sh
```

### 步骤5：浏览器测试
1. 打开 http://9.135.87.101:8701
2. 打开浏览器开发者工具（F12）
3. 切换到 Network 标签
4. 尝试进行一次评估操作
5. 观察是否有API请求发出，检查：
   - 请求URL是否正确指向 `http://9.135.87.101:7860/api/...`
   - 请求状态码是否为200
   - 响应内容是否正常

## 🔍 如果问题仍然存在

### 检查清单
- [ ] 后端重启完成，`/api/health` 接口可访问
- [ ] 前端构建包含正确的API地址
- [ ] 浏览器Network标签显示API请求
- [ ] 请求URL指向正确的后端地址
- [ ] 响应状态码为200

### 常见问题排查

#### 1. 前端请求未发出
**现象**：浏览器Network标签看不到API请求
**解决**：检查前端代码中的API调用逻辑

#### 2. 请求发送到错误地址
**现象**：请求URL不是 `http://9.135.87.101:7860/api/...`
**解决**：
```bash
# 检查环境变量
cd frontend
cat .env.production

# 重新构建前端
REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build
```

#### 3. CORS错误
**现象**：浏览器控制台显示CORS错误
**解决**：检查后端CORS配置

#### 4. 网络连接问题
**现象**：请求超时或连接失败
**解决**：
```bash
# 检查端口是否可访问
curl http://9.135.87.101:7860/health
curl http://9.135.87.101:8701

# 检查防火墙
sudo ufw status
sudo ufw allow 7860
sudo ufw allow 8701
```

## 🎯 预期结果

修复完成后，您应该看到：
1. ✅ 前端可以正常显示评估界面
2. ✅ 评估操作可以正常完成
3. ✅ 评估结果保存到历史记录
4. ✅ 浏览器Network标签显示正常的API请求和响应

## 📞 如需进一步支持

如果按照上述步骤仍无法解决，请提供：
1. 后端重启后的日志输出
2. 浏览器开发者工具Network标签的截图
3. 浏览器控制台的错误信息
4. API测试脚本的输出结果

---
*解决方案创建时间: 2025-06-05 14:12*
*适用版本: v2.3.5* 