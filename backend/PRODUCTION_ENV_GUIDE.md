# 生产环境配置指南：确保使用.env.production

## 🎯 问题背景

React应用在构建时会按照特定的优先级加载环境变量文件，如果存在多个环境文件，可能导致生产环境无法正确使用`.env.production`配置。

## 📋 React环境变量加载优先级

React按以下顺序加载环境变量（从高到低优先级）：

1. **命令行环境变量**（最高优先级）
   ```bash
   REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build
   ```

2. **`.env.production.local`**（生产环境本地覆盖）
   - 仅在生产构建时加载
   - 会覆盖`.env.production`

3. **`.env.local`**（本地环境覆盖）⚠️ **危险**
   - 在所有环境中都会加载
   - **会覆盖`.env.production`配置**

4. **`.env.production`**（生产环境配置）✅ **目标**
   - 仅在生产构建时加载
   - 我们希望使用的配置文件

5. **`.env`**（默认环境配置）
   - 在所有环境中都会加载
   - 优先级最低

## 🔍 检查当前环境文件状态

### 使用验证脚本
```bash
cd backend
./verify_frontend_config.sh
```

验证脚本会检查：
- ✅ `.env.production`文件是否存在且配置正确
- ⚠️ 是否存在会覆盖`.env.production`的冲突文件
- ✅ package.json中是否有proxy配置冲突
- ✅ 构建结果中是否包含正确的API地址

### 手动检查
```bash
cd frontend
ls -la .env*
```

查看各文件的API配置：
```bash
grep "REACT_APP_API_URL" .env* 2>/dev/null
```

## 🔧 解决环境文件冲突

### 自动化解决方案（推荐）
```bash
cd backend
./ensure_production_env.sh
```

选择方案：
- **方案1：重命名冲突文件**（推荐）
  - 将冲突文件重命名为`.disabled`后缀
  - 保留原文件便于恢复
  
- **方案2：删除冲突文件**
  - 直接删除冲突文件
  - 不可恢复，谨慎使用

### 手动解决方案
```bash
cd frontend

# 重命名冲突文件
mv .env.local .env.local.disabled
mv .env .env.disabled

# 或直接删除（谨慎）
rm .env.local .env
```

## 🚀 确保正确构建的方法

### 方法1：清理环境后构建（推荐）
```bash
# 1. 处理环境文件冲突
cd backend
./ensure_production_env.sh

# 2. 重新构建
cd ../frontend
rm -rf build
npm run build
```

### 方法2：命令行强制指定（最安全）
```bash
cd frontend
REACT_APP_API_URL=http://9.135.87.101:7860/api npm run build
```

### 方法3：使用生产启动脚本（全自动）
```bash
cd backend
./start_frontend_production.sh
```

## ✅ 验证配置正确性

### 1. 环境文件验证
```bash
cd backend
./verify_frontend_config.sh
```

应该看到：
- ✅ API URL配置正确: http://9.135.87.101:7860/api
- ✅ 无环境文件冲突
- ✅ 构建文件包含正确的API地址

### 2. 构建文件验证
```bash
cd frontend
# 检查构建结果中的API配置
grep -o "http://[^\"]*api" build/static/js/main.*.js
```

应该输出：`http://9.135.87.101:7860/api`

### 3. 运行时验证
启动前端服务后，在浏览器开发者工具中检查：
```javascript
// 在浏览器控制台中执行
console.log('API URL:', process.env.REACT_APP_API_URL);
```

## 🛠️ 常见问题解决

### 问题1：构建后仍然使用错误的API地址
**原因**：存在高优先级的环境文件覆盖了`.env.production`

**解决**：
```bash
cd backend
./ensure_production_env.sh  # 选择方案1重命名冲突文件
cd ../frontend
rm -rf build && npm run build
```

### 问题2：开发环境配置影响生产环境
**原因**：`.env.local`在所有环境中都会加载

**解决**：
```bash
# 重命名.env.local为开发专用
mv .env.local .env.development.local
```

### 问题3：团队成员环境不一致
**原因**：不同成员的本地环境文件不同

**解决**：
1. 添加到`.gitignore`：
   ```
   .env.local
   .env.development.local
   .env.test.local
   .env.production.local
   ```

2. 统一使用构建脚本：
   ```bash
   ./start_frontend_production.sh
   ```

## 📝 最佳实践

### 1. 环境文件管理
- ✅ 只保留`.env.production`用于生产环境
- ✅ 使用`.env.development.local`用于开发环境个人配置
- ❌ 避免使用`.env.local`（会影响所有环境）
- ❌ 避免提交个人本地配置到Git

### 2. 构建流程
- ✅ 构建前检查环境文件冲突
- ✅ 使用命令行参数强制指定关键配置
- ✅ 验证构建结果中的配置正确性

### 3. 团队协作
- ✅ 使用统一的构建脚本
- ✅ 定期验证生产环境配置
- ✅ 文档化环境配置要求

## 🔗 相关脚本和工具

- `./verify_frontend_config.sh` - 配置验证工具
- `./ensure_production_env.sh` - 环境冲突处理工具
- `./start_frontend_production.sh` - 生产环境启动脚本

## 📚 参考资料

- [Create React App - Environment Variables](https://create-react-app.dev/docs/adding-custom-environment-variables/)
- [React Environment Variables Priority](https://create-react-app.dev/docs/adding-custom-environment-variables/#what-other-env-files-can-be-used) 