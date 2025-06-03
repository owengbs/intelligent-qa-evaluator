
# 云端部署故障排除指南

## 常见问题及解决方案

### 1. 评估结果无法保存
**症状**: 前端评估完成后，历史记录中没有数据
**原因**: 字段映射问题已修复
**验证**: 
```bash
curl -X POST http://localhost:5001/api/evaluation-history \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "测试问题",
    "model_answer": "测试答案",
    "total_score": 8.0,
    "evaluation_criteria": "测试标准"
  }'
```

### 2. 前端无法连接后端
**症状**: 网络错误或CORS错误
**解决方案**:
1. 检查后端是否启动: `curl http://服务器IP:5001/health`
2. 检查防火墙设置: `sudo ufw allow 5001`
3. 确认IP地址正确: `hostname -I`

### 3. 依赖包问题
**症状**: 导入错误或模块不存在
**解决方案**:
```bash
source venv/bin/activate
pip install -r requirements.txt
pip list | grep -E "(flask|sqlalchemy|openai)"
```

### 4. 数据库问题
**症状**: 数据库文件不存在或表结构错误
**解决方案**:
```bash
python quick_init.py
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 5. 端口占用
**症状**: 地址已在使用
**解决方案**:
```bash
sudo lsof -i :5001
sudo kill -9 PID号
```

## 部署检查清单

- [ ] 虚拟环境已创建并激活
- [ ] 依赖包已安装
- [ ] 数据库已初始化
- [ ] 后端服务可正常启动
- [ ] 健康检查接口正常: /health
- [ ] 评估历史保存接口正常: POST /api/evaluation-history
- [ ] 前端环境变量已配置
- [ ] 防火墙端口已开放

## 联系支持
如果问题仍未解决，请提供：
- 错误日志完整信息
- 服务器环境信息（OS、Python版本）
- 网络配置信息
