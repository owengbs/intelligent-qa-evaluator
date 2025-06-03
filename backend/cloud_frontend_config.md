
云端前端配置修复指南：

1. 设置环境变量（推荐）：
   export REACT_APP_API_URL=http://你的云端服务器IP:5001/api
   # 例如：export REACT_APP_API_URL=http://192.168.1.100:5001/api

2. 或者修改前端代码（如果无法设置环境变量）：
   文件：frontend/src/services/evaluationService.js
   修改第3行：
   const API_BASE_URL = 'http://你的云端服务器IP:5001/api';

3. 确保前端能访问后端：
   - 检查云端服务器防火墙是否开放5001端口
   - 确认后端启动时绑定了正确的IP地址
   - 测试命令：curl http://云端服务器IP:5001/health

4. 重启前端服务：
   cd frontend
   npm start
